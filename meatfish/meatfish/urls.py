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
from rest_framework import permissions
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('csrf/', views.get_csrf_token),
    path('dishes/', views.DishList.as_view(), name='dish-list'),
    path('dishes/<int:pk>/', views.DishDetail.as_view(), name='dish-detail'),
    path('dishes/<int:pk>/image/', views.DishImageUpdate.as_view(), name='dish-update-image'),
    path('dishes/<int:pk>/draft/', views.DishAddToDraft.as_view(), name='dish-add-to-draft'),
    path('dinners/', views.DinnerList.as_view(), name='dinner-list'),
    path('dinners/<int:pk>/', views.DinnerDetail.as_view(), name='dinner-detail'),
    path('dinners/<int:pk>/edit/', views.DinnerDetail.as_view(), name='dinner-detail-edit'),
    path('dinners/<int:pk>/form/', views.DinnerDetail.as_view(), name='dinner-detail-form'),
    path('dinners/<int:pk>/complete/', views.DinnerDetail.as_view(), name='dinner-detail-complete'),
    path('dinners/<int:dinner_id>/dishes/<int:dish_id>/', views.DinnerDishDetail.as_view(), name='dinner-dish-detail'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('login/',  views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/auth/', views.UserViewSet.as_view({'post': 'create'}), name='user-register'),
    path('users/profile/', views.UserViewSet.as_view({'put': 'profile'}), name='user-profile'),
    path('users/check/', views.check_session)
]
