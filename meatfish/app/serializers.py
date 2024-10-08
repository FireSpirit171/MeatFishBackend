from rest_framework import serializers
from django.contrib.auth.models import User
from app.models import Dish, Dinner, DinnerDish

class DishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['id', 'name', 'type', 'description', 'price', 'weight', 'photo', 'status']

class DinnerDishSerializer(serializers.ModelSerializer):
    dish = DishSerializer(read_only=True)
    
    class Meta:
        model = DinnerDish
        fields = ['id', 'dinner', 'dish', 'user', 'count']

class DinnerSerializer(serializers.ModelSerializer):
    dishes = DinnerDishSerializer(many=True, read_only=True, source='dinnerdish_set')

    class Meta:
        model = Dinner
        fields = ['id', 'table_number', 'total_cost', 'status', 'created_at', 'formed_at', 'completed_at', 'creator', 'moderator', 'dishes']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
