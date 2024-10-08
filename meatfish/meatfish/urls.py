"""
URL configuration for meatfish project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from app import views 
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('dishes/', views.DishList.as_view(), name='dish-list'),
    path('dishes/<int:pk>/', views.DishDetail.as_view(), name='dish-detail'),
    path('dinners/', views.DinnerList.as_view(), name='dinner-list'),
    path('dinners/<int:pk>/', views.DinnerDetail.as_view(), name='dinner-detail'),
    path('dinners/<int:pk>/put/', views.update_dinner_for_user, name='user-update-dinner'),
    path('dinners/<int:dinner_id>/dishes/<int:dish_id>/', views.DinnerDishDetail.as_view(), name='dinner-dish-detail'),
    path('users/<str:action>/', views.UserView.as_view(), name='user-action'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
]

