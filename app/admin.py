from django.contrib import admin
from app import models

admin.site.register(models.Order)
admin.site.register(models.OrderDish)
admin.site.register(models.Dish)