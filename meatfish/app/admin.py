from django.contrib import admin
from app import models

admin.site.register(models.Dinner)
admin.site.register(models.DinnerDish)
admin.site.register(models.Dish)
admin.site.register(models.CustomUser)