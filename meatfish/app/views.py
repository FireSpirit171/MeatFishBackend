from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.http import Http404, HttpResponse
from .models import Dish, Dinner, DinnerDish
from .serializers import *
from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import *
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt

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

        user = request.user
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

    @swagger_auto_schema(request_body=serializer_class)
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

    @swagger_auto_schema(request_body=serializer_class)
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

class DishImageUpdate(APIView):
    model_class = Dish
    serializer_class = DishImageSerializer

    @swagger_auto_schema(request_body=serializer_class)
    def post(self, request, pk, format=None):
        dish = get_object_or_404(Dish, pk=pk)
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

class DishAddToDraft(APIView):
    @swagger_auto_schema()
    def post(self, request, pk, format=None):
        user = request.user
        if not user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        dish = get_object_or_404(Dish, pk=pk)
        draft_dinner = Dinner.objects.filter(creator=user, status='dr').first()

        if not draft_dinner:
            draft_dinner = Dinner.objects.create(
                table_number=1,
                creator=user,
                status='dr',
                created_at=timezone.now()
            )
            draft_dinner.save()

        if DinnerDish.objects.filter(dinner=draft_dinner, dish=dish).exists():
            return Response(data={"error": "Блюдо уже добавлено в черновик."}, status=status.HTTP_400_BAD_REQUEST)

        DinnerDish.objects.create(dinner=draft_dinner, dish=dish, count=1)
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Dinner (заявки)
class DinnerList(APIView):
    model_class = Dinner
    serializer_class = DinnerSerializer

    def get(self, request, format=None):
        user = request.user

        # Получаем фильтры из запросов
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        status = request.query_params.get('status')

        # Фильтруем ужины по пользователю и статусам
        dinners = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])

        if date_from:
            dinners = dinners.filter(created_at__gte=date_from)
        if date_to:
            dinners = dinners.filter(created_at__lte=date_to)
        if status:
            dinners = dinners.filter(status=status)

        # Сериализуем данные
        serialized_dinners = [
            {**self.serializer_class(dinner).data, 'creator': dinner.creator.email, 'moderator': dinner.moderator.email if dinner.moderator else None}
            for dinner in dinners
        ]

        return Response(serialized_dinners)

    @swagger_auto_schema(request_body=serializer_class)
    def put(self, request, format=None):
        user = request.user
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
        data['creator'] = dinner.creator.email
        if dinner.moderator:
            data['moderator'] = dinner.moderator.email 

        return Response(data)

    @swagger_auto_schema(request_body=serializer_class)
    def put(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        user = request.user

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

    @swagger_auto_schema(request_body=serializer_class)
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

class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def create(self, request):
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(email=serializer.data['email'],
                                     password=serializer.data['password'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
def login_view(request):
    email = request.data["email"]
    password = request.data["password"]
    user = authenticate(request, email=email, password=password)
    if user is not None:
        login(request, user)
        return HttpResponse("{'status': 'ok'}")
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")

def logout_view(request):
    logout(request)
    return Response({'status': 'Success'})

# class UserView(APIView):
#     def post(self, request, action, format=None):
#         if action == 'register':
#             serializer = UserSerializer(data=request.data)
#             if serializer.is_valid():
#                 validated_data = serializer.validated_data
#                 user = CustomUser(
#                     username=validated_data['username'],
#                     email=validated_data['email']
#                 )
#                 user.set_password(request.data.get('password'))
#                 user.save()
#                 return Response({
#                     'message': 'Регистрация прошла успешно'
#                 }, status=status.HTTP_201_CREATED)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         elif action == 'authenticate':
#             username = request.data.get('username')
#             password = request.data.get('password')
#             user = authenticate(request, username=username, password=password)
            
#             if user is not None:
#                 user_data = UserSerializer(user).data
#                 return Response({
#                     'message': 'Аутентификация успешна',
#                     'user': user_data
#                 }, status=200)
            
#             return Response({'error': 'Неправильное имя пользователя или пароль'}, status=400)

#         elif action == 'logout':
#             return Response({'message': 'Вы вышли из системы'}, status=200)

#         return Response({'error': 'Некорректное действие'}, status=400)

#     # Обновление данных профиля пользователя
#     def put(self, request, action, format=None):
#         if action == 'profile':
#             user = UserSingleton.get_instance()
#             if user is None:
#                 return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
            
#             serializer = UserSerializer(user, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         return Response({'error': 'Некорректное действие'}, status=status.HTTP_400_BAD_REQUEST)

