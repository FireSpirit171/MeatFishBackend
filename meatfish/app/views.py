from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from .models import Dish, Dinner
from .serializers import DishSerializer, DinnerSerializer

# View для Dish (блюда)
class DishList(APIView):
    model_class = Dish
    serializer_class = DishSerializer

    # Получение списка блюд
    def get(self, request, format=None):
        dishes = self.model_class.objects.filter(status='a')  # Только активные блюда
        serializer = self.serializer_class(dishes, many=True)
        return Response(serializer.data)

    # Добавление нового блюда
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DishDetail(APIView):
    model_class = Dish
    serializer_class = DishSerializer

    # Получение информации о блюде
    def get(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dish)
        return Response(serializer.data)

    # Обновление информации о блюде
    def put(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dish, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаление блюда
    def delete(self, request, pk, format=None):
        dish = get_object_or_404(self.model_class, pk=pk)
        dish.status = 'd'  # Мягкое удаление
        dish.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# View для Dinner (заявки)
class DinnerList(APIView):
    model_class = Dinner
    serializer_class = DinnerSerializer

    # Получение списка заявок
    def get(self, request, format=None):
        dinners = self.model_class.objects.all()
        serializer = self.serializer_class(dinners, many=True)
        return Response(serializer.data)

    # Добавление новой заявки
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=request.user)  # Автоматически присваиваем пользователя
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DinnerDetail(APIView):
    model_class = Dinner
    serializer_class = DinnerSerializer

    # Получение информации о заявке
    def get(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dinner)
        return Response(serializer.data)

    # Обновление заявки (для модератора)
    def put(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(dinner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(moderator=request.user)  # Устанавливаем модератора
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаление заявки
    def delete(self, request, pk, format=None):
        dinner = get_object_or_404(self.model_class, pk=pk)
        dinner.status = 'del'  # Мягкое удаление
        dinner.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Дополнительный метод PUT для пользователя (функциональное представление)
@api_view(['PUT'])
def update_dinner_for_user(request, pk):
    dinner = get_object_or_404(Dinner, pk=pk)
    serializer = DinnerSerializer(dinner, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()  # Обновление без назначения модератора
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
