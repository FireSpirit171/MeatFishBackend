from rest_framework import serializers
from django.contrib.auth.models import User
from app.models import Dish, Dinner, DinnerDish, CustomUser

class DishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['id', 'name', 'type', 'description', 'price', 'weight', 'photo']

class DishImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['photo']

class DinnerDishSerializer(serializers.ModelSerializer):
    dish = DishSerializer(read_only=True)
    
    class Meta:
        model = DinnerDish
        fields = ['id', 'dinner', 'dish', 'guest', 'count']

class DishCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['id', 'name', 'price', 'weight', 'photo']

class DinnerDishCompactSerializer(serializers.ModelSerializer):
    dish = DishCompactSerializer(read_only=True)
    
    class Meta:
        model = DinnerDish
        fields = ['dish', 'guest', 'count']

class DinnerSerializer(serializers.ModelSerializer):
    dishes = DinnerDishCompactSerializer(many=True, read_only=True, source='dinnerdish_set')

    class Meta:
        model = Dinner
        fields = ['id', 'table_number', 'total_cost', 'status', 'created_at', 'formed_at', 'completed_at', 'creator', 'moderator', 'dishes', 'qr']


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']
