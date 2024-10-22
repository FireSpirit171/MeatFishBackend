from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from django.http import Http404, HttpResponse, JsonResponse
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
from app.permissions import *
from app.services.qr_generate import generate_dinner_qr
import redis
import uuid

session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes        
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)
        return decorated_func
    return decorator

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
        total_dish_count = 0

        if user.is_authenticated:
            draft_dinner = Dinner.objects.filter(creator=user, status='dr').first()
            if draft_dinner:
                draft_dinner_id = draft_dinner.id
                total_dish_count = Dinner.objects.get_total_dish_count(draft_dinner)

        serializer = self.serializer_class(dishes, many=True)
        response_data = {
            'dishes': serializer.data,
            'draft_dinner_id': draft_dinner_id,
            'total_dish_count': total_dish_count 
        }
        return Response(response_data)

    @method_permission_classes([IsManager])
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
    
    @method_permission_classes([IsManager])
    @swagger_auto_schema(request_body=serializer_class)
    def put(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dish, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes([IsManager])
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
    @method_permission_classes([IsManager])
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
        if user.is_authenticated:
            if user.is_staff:
                dinners = self.model_class.objects.all().exclude(status__in=['del'])
            else:
                dinners = self.model_class.objects.filter(creator=user).exclude(status__in=['dr', 'del'])
        else:
            return Response({"error": "Вы не авторизованы"}, status=401)

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

class DinnerDetail(APIView):
    model_class = Dinner
    serializer_class = DinnerSerializer
    permission_classes = [IsAuthenticated]

    # Получение заявки
    def get(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        if dinner.status == 'del' or dinner.creator != request.user:
            return Response({"error": "Нельзя посмотреть заявку"}, status=403)
        serializer = self.serializer_class(dinner)
        data = serializer.data
        data['creator'] = dinner.creator.email
        if dinner.moderator:
            data['moderator'] = dinner.moderator.email
        return Response(data)

    def put(self, request, pk, format=None):
        # Получаем полный путь запроса
        full_path = request.path

        # Проверяем, заканчивается ли путь на /form/, /complete/ или /edit/
        if full_path.endswith('/form/'):
            return self.put_creator(request, pk)
        elif full_path.endswith('/complete/'):
            return self.put_moderator(request, pk)
        elif full_path.endswith('/edit/'):
            return self.put_edit(request, pk)

        return Response({"error": "Неверный путь"}, status=status.HTTP_400_BAD_REQUEST)

    # PUT для создателя: формирование заявки
    def put_creator(self, request, pk):
        dinner = get_object_or_404(self.model_class, pk=pk)
        user = request.user

        if user == dinner.creator:

            # Проверка на обязательные поля
            required_fields = ['table_number']
            for field in required_fields:
                if field not in request.data:
                    return Response({"error": f"Поле {field} является обязательным."}, status=status.HTTP_400_BAD_REQUEST)

            # Установка статуса 'f' (сформирована) и даты формирования
            if 'status' in request.data and request.data['status'] == 'f':
                dinner.formed_at = timezone.now()
                updated_data = request.data.copy()

                serializer = self.serializer_class(dinner, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"error": "Создатель может только формировать заявку."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Отказано в доступе"}, status=status.HTTP_403_FORBIDDEN)        

    # PUT для модератора: завершение или отклонение заявки
    @method_permission_classes([IsManager])  # Разрешаем только модераторам
    def put_moderator(self, request, pk):
        dinner = get_object_or_404(self.model_class, pk=pk)
        user = request.user
        
        if 'status' in request.data:
            status_value = request.data['status']

            # Модератор может завершить ('c') или отклонить ('r') заявку
            if status_value in ['c', 'r']:
                if dinner.status != 'f':
                    return Response({"error": "Заявка должна быть сначала сформирована."}, status=status.HTTP_403_FORBIDDEN)

                # Установка даты завершения и расчёт стоимости для завершённых заявок
                if status_value == 'c':
                    real_time = timezone.now()
                    dinner.completed_at = real_time
                    total_cost = self.calculate_total_cost(dinner)
                    updated_data = request.data.copy()
                    updated_data['total_cost'] = total_cost

                    # Генерация QR-кода
                    dinner_dishes = dinner.dinnerdish_set.all()
                    qr_code_base64 = generate_dinner_qr(dinner, dinner_dishes, real_time)
                    updated_data['qr'] = qr_code_base64

                elif status_value == 'r':
                    dinner.completed_at = timezone.now()
                    updated_data = request.data.copy()

                serializer = self.serializer_class(dinner, data=updated_data, partial=True)
                if serializer.is_valid():
                    serializer.save(moderator=user)
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": "Модератор может только завершить или отклонить заявку."}, status=status.HTTP_400_BAD_REQUEST)

    def put_edit(self, request, pk):
        user = request.user
        if user.is_authenticated:
            dinner = get_object_or_404(self.model_class, pk=pk)

            if dinner.creator == user:
                # Обновление дополнительных полей
                serializer = self.serializer_class(dinner, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)

                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Вы не создатель заказа"}, status=403)
        return Response({"error": "Вы не авторизованы"}, status=401)
    
    # Вычисление общей стоимости заявки
    def calculate_total_cost(self, dinner):
        total_cost = 0
        dinner_dishes = dinner.dinnerdish_set.all()

        for dinner_dish in dinner_dishes:
            dish_price = dinner_dish.dish.price
            dish_count = dinner_dish.count
            total_cost += dish_price * dish_count

        return total_cost

    # Мягкое удаление заявки
    def delete(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        if dinner.creator != request.user:
            return Response({"error": "Вы не создатель заказа"}, status=403)
        if dinner.status != 'dr':
            return Response({"error": "Нельзя удалить заявку"}, status=403)
        dinner.status = 'del'  # Мягкое удаление
        dinner.formed_at = timezone.now()
        dinner.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    
class DinnerDishDetail(APIView):
    model_class = DinnerDish
    serializer_class = DinnerDishSerializer

    @swagger_auto_schema(request_body=serializer_class)
    @method_permission_classes([IsManager])
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
        user = request.user
        if user.is_authenticated:
            if dinner.creator == user:
                dinner_dish = get_object_or_404(self.model_class, dinner=dinner, dish__id=dish_id)
                dinner_dish.delete()
                return Response({"message": "Блюдо успешно удалено из заявки"}, status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "Вы не создатель заказа"}, status=403)
        return Response({"error": "Вы не авторизованы"}, status=401)

class UserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def get_permissions(self):
        # Удаляем ненужные проверки, чтобы любой пользователь мог обновить свой профиль
        if self.action == 'create' or self.action == 'profile':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request):
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(
                email=serializer.data['email'],
                password=serializer.data['password'],
                is_superuser=serializer.data['is_superuser'],
                is_staff=serializer.data['is_staff']
            )
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # Обновление данных профиля пользователя
    @action(detail=False, methods=['put'], permission_classes=[AllowAny])
    def profile(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Профиль обновлен', 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@authentication_classes([])
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    username = request.data["email"] 
    password = request.data["password"]

    print(username)
    print(password)

    user = authenticate(request, email=username, password=password)

    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)
        
        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")

@swagger_auto_schema(method='post')
def logout_view(request):
    if request.user.is_authenticated:
        session_id = request.COOKIES.get("session_id")
        if session_id:
            session_storage.delete(session_id)
            response = HttpResponse("{'status': 'ok'}")
            response.delete_cookie("session_id")
            return response
        else:
            return HttpResponse("{'status': 'error', 'error': 'no session found'}")
    return HttpResponse("{'error': 'Вы не авторизованы'}")

