from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .models import Dish, Dinner, DinnerDish
from .serializers import DishSerializer, DinnerSerializer, DinnerDishSerializer, UserSerializer
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('meatfish', image_name, file_object, file_object.size)
        return f"http://localhost:9000/meatfish/{image_name}"
    except Exception as e:
        return {"error": str(e)}

def add_pic(new_dish, pic):
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )
    img_obj_name = f"{new_dish.id}.jpg"

    if not pic:
        return {"error": "Нет файла для изображения."}

    result = process_file_upload(pic, client, img_obj_name)
    
    if 'error' in result:
        return {"error": result['error']}

    return result 

# View для Dish (блюда)
class DishList(APIView):
    model_class = Dish
    serializer_class = DishSerializer

    def get(self, request, format=None):
        dishes = self.model_class.objects.filter(status='a')
        serializer = self.serializer_class(dishes, many=True)
        return Response(serializer.data)
  
    def post(self, request, format=None):
        pic = request.FILES.get("photo")
        data = request.data.copy()
        data.pop('photo', None) 
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            dish = serializer.save()
            if pic:
                pic_url = add_pic(dish, pic)
                if 'error' in pic_url:
                    return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)
                dish.photo = pic_url
                dish.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DishDetail(APIView):
    model_class = Dish
    serializer_class = DishSerializer

    def get(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dish)
        return Response(serializer.data)
    
    def post(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        pic = request.FILES.get("photo")

        if not pic:
            return Response({"error": "Файл изображения не предоставлен."}, status=status.HTTP_400_BAD_REQUEST)

        if dish.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            old_img_name = dish.photo.split('/')[-1] 
            try:
                client.remove_object('meatfish', old_img_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении старого изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        pic_url = add_pic(dish, pic)
        if 'error' in pic_url:
            return Response({"error": pic_url['error']}, status=status.HTTP_400_BAD_REQUEST)

        dish.photo = pic_url
        dish.save()
        
        return Response({"message": "Изображение успешно обновлено.", "photo_url": pic_url}, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dish, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        dish.status = 'd'
        dish.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Dinner (заявки)
class DinnerList(APIView):
    model_class = Dinner
    serializer_class = DinnerSerializer

    def get(self, request, format=None):
        dinners = self.model_class.objects.exclude(status__in=['dr', 'del'])
        serialized_dinners = []
        for dinner in dinners:
            serialized_dinner = self.serializer_class(dinner).data
            serialized_dinner['creator'] = dinner.creator.username
            if dinner.moderator:
                serialized_dinner['moderator'] = dinner.moderator.username 
            serialized_dinners.append(serialized_dinner)

        return Response(serialized_dinners)

    def put(self, request, format=None):
        required_fields = ['table_number']
        for field in required_fields:
            if field not in request.data or request.data[field] is None:
                return Response({field: 'Это поле обязательно для заполнения.'}, status=status.HTTP_400_BAD_REQUEST)
            
        dinner_id = request.data.get('id')
        if dinner_id:
            dinner = get_object_or_404(self.model_class, pk=dinner_id)
            serializer = self.serializer_class(dinner, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=request.user)
                return Response(serializer.data)
            
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            dinner = serializer.save(creator=request.user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DinnerDetail(APIView):
    model_class = Dinner
    serializer_class = DinnerSerializer

    def get(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dinner)
        data = serializer.data
        data['creator'] = dinner.creator.username
        if dinner.moderator:
            data['moderator'] = dinner.moderator.username 

        return Response(data)

    def put(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        if 'status' in request.data:
            status = request.data['status']
            if status in ['f', 'r']: 
                total_cost = self.calculate_total_cost(dinner)
                updated_data = request.data.copy()
                updated_data['total_cost'] = total_cost
                dinner.completed_at = timezone.now()
                serializer = self.serializer_class(dinner, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save(moderator=request.user)
                    return Response(serializer.data)
                
        serializer = self.serializer_class(dinner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(moderator=request.user)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def calculate_total_cost(self, dinner):
        total_cost = 0
        dinner_dishes = dinner.dinnerdish_set.all() 

        for dinner_dish in dinner_dishes:
            dish_price = dinner_dish.dish.price 
            dish_count = dinner_dish.count 
            total_cost += dish_price * dish_count

        return total_cost

    # Удаление заявки
    def delete(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        dinner.status = 'del'  # Мягкое удаление
        dinner.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class DinnerDishDetail(APIView):
    model_class = DinnerDish
    serializer_class = DinnerDishSerializer

    def put(self, request, dinner_id, dish_id, format=None):
        dinner = get_object_or_404(Dinner, pk=dinner_id)
        dinner_dish = get_object_or_404(self.model_class, dinner=dinner, dish__id=dish_id)
        
        serializer = self.serializer_class(dinner_dish, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, dinner_id, dish_id, format=None):
        dinner = get_object_or_404(Dinner, pk=dinner_id)
        dinner_dish = get_object_or_404(self.model_class, dinner=dinner, dish__id=dish_id)
        
        dinner_dish.delete()  # Удаляем запись м-м
        return Response({"message": "Блюдо успешно удалено из заявки"}, status=status.HTTP_204_NO_CONTENT)

class UserView(APIView):
    def post(self, request, action, format=None):
        if action == 'register':
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Регистрация прошла успешно',
                    'token': token.key
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'authenticate':
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Аутентификация успешна',
                    'token': token.key
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Неправильное имя пользователя или пароль'}, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'logout':
            if request.user.is_authenticated:
                request.user.auth_token.delete()
                logout(request)
                return Response({'message': 'Вы вышли из системы'}, status=status.HTTP_200_OK)
            return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, action, format=None):
        if action == 'profile':
            if not request.user.is_authenticated:
                return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
            
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)


# Дополнительный метод PUT для пользователя (функциональное представление)
@api_view(['PUT'])
def update_dinner_for_user(request, pk):
    dinner = get_object_or_404(Dinner, pk=pk)
    serializer = DinnerSerializer(dinner, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()  # Обновление без назначения модератора
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
