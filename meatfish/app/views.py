from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from django.http import Http404
from .models import Dish, Dinner, DinnerDish
from .serializers import DishSerializer, DinnerSerializer, DinnerDishSerializer, UserSerializer
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

class UserSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = User.objects.get(id=4)
            except User.DoesNotExist:
                cls._instance = None
        return cls._instance

    @classmethod
    def clear_instance(cls, user):
        pass


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
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')

        dishes = self.model_class.objects.filter(status='a')
        if min_price:
            dishes = dishes.filter(price__gte=min_price)
        if max_price:
            dishes = dishes.filter(price__lte=max_price)

        user = UserSingleton.get_instance()
        draft_dinner_id = None
        if user:
            draft_dinner = Dinner.objects.filter(creator=user, status='dr').first()
            if draft_dinner:
                draft_dinner_id = draft_dinner.id

        serializer = self.serializer_class(dishes, many=True)
        response_data = {
            'dishes': serializer.data,
            'draft_dinner_id': draft_dinner_id 
        }
        return Response(response_data)
  
    def post(self, request, format=None):
        data = request.data.copy()
        data['photo'] = None

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            dish = serializer.save() 
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
        if request.path.endswith('/image/'):
            return self.update_image(request, pk)
        elif request.path.endswith('/draft/'):
            return self.add_to_draft(request, pk)
        raise Http404

    def update_image(self, request, pk):
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

    def add_to_draft(self, request, pk):
        user = UserSingleton.get_instance()
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        dish = get_object_or_404(self.model_class, pk=pk)
        draft_dinner = Dinner.objects.filter(creator=user, status='dr').first()

        if not draft_dinner:
            draft_dinner = Dinner.objects.create(
                table_number = 1,
                creator=user,
                status='dr',
                created_at=timezone.now()
            )
            draft_dinner.save()

        if DinnerDish.objects.filter(dinner=draft_dinner, dish=dish).exists():
            return Response(data={"error": "Блюдо уже добавлено в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        DinnerDish.objects.create(dinner=draft_dinner, dish=dish, count=1)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dish, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        if dish.photo:
            client = Minio(
                endpoint=settings.AWS_S3_ENDPOINT_URL,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                secure=settings.MINIO_USE_SSL
            )
            image_name = dish.photo.split('/')[-1]
            try:
                client.remove_object('meatfish', image_name)
            except Exception as e:
                return Response({"error": f"Ошибка при удалении изображения: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        dish.status = 'd'
        dish.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Dinner (заявки)
class DinnerList(APIView):
    model_class = Dinner
    serializer_class = DinnerSerializer

    def get(self, request, format=None):
        user = UserSingleton.get_instance()

        # Получаем фильтры из запросов
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        # Фильтруем ужины по пользователю и статусам
        dinners = self.model_class.objects.exclude(status__in=['dr', 'del'])

        if date_from:
            dinners = dinners.filter(created_at__gte=date_from)
        if date_to:
            dinners = dinners.filter(created_at__lte=date_to)
        if status:
            dinners = dinners.filter(status=status)

        # Сериализуем данные
        serialized_dinners = [
            {**self.serializer_class(dinner).data, 'creator': dinner.creator.username, 'moderator': dinner.moderator.username if dinner.moderator else None}
            for dinner in dinners
        ]

        return Response(serialized_dinners)

    def put(self, request, format=None):
        user = UserSingleton.get_instance()
        required_fields = ['table_number']
        for field in required_fields:
            if field not in request.data or request.data[field] is None:
                return Response({field: 'Это поле обязательно для заполнения.'}, status=status.HTTP_400_BAD_REQUEST)
            
        dinner_id = request.data.get('id')
        if dinner_id:
            dinner = get_object_or_404(self.model_class, pk=dinner_id)
            serializer = self.serializer_class(dinner, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)
            
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            dinner = serializer.save(creator=user) 
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
        user = UserSingleton.get_instance()

        if 'status' in request.data:
            status_value = request.data['status']

            if status_value in ['del', 'f']:
                if dinner.creator == user:
                    updated_data = request.data.copy()

                    if status_value == 'f':
                        dinner.formed_at = timezone.now()

                    serializer = self.serializer_class(dinner, data=updated_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                else:
                    return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)
                
            if status_value not in ['c', 'r']:
                return Response({"error": "Неверный статус."}, status=status.HTTP_400_BAD_REQUEST)
            
            if dinner.status != 'f':
                return Response({"error": "Заявка ещё не сформирована."}, status=status.HTTP_403_FORBIDDEN)

            total_cost = self.calculate_total_cost(dinner)
            updated_data = request.data.copy()
            updated_data['total_cost'] = total_cost
            dinner.completed_at = timezone.now()
            
            serializer = self.serializer_class(dinner, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save(moderator=user)
                return Response(serializer.data)

        # Если статус не был передан, пробуем обновить остальные данные
        serializer = self.serializer_class(dinner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(moderator=user)
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
        
        dinner_dish.delete()
        return Response({"message": "Блюдо успешно удалено из заявки"}, status=status.HTTP_204_NO_CONTENT)

class UserView(APIView):
    def post(self, request, action, format=None):
        if action == 'register':
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                user = User(
                    username=validated_data['username'],
                    email=validated_data['email']
                )
                user.set_password(request.data.get('password'))
                user.save()
                return Response({
                    'message': 'Регистрация прошла успешно'
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif action == 'authenticate':
            username = request.data.get('username')
            password = request.data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                user_data = UserSerializer(user).data
                return Response({
                    'message': 'Аутентификация успешна',
                    'user': user_data
                }, status=200)
            
            return Response({'error': 'Неправильное имя пользователя или пароль'}, status=400)

        elif action == 'logout':
            return Response({'message': 'Вы вышли из системы'}, status=200)

        return Response({'error': 'Некорректное действие'}, status=400)

    # Обновление данных профиля пользователя
    def put(self, request, action, format=None):
        if action == 'profile':
            user = UserSingleton.get_instance()
            if user is None:
                return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
            
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)

