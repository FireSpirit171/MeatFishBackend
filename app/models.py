from django.db import models
from django.contrib.auth.models import User
import segno
from io import BytesIO

class DishManager(models.Manager):
    def get_one_dish(self, dish_id):
        dishes = Dish.objects.filter(id=dish_id)
        return dishes.get(id=dish_id)

class Dish(models.Model):
    STATUS_CHOICES = [
        ("a", "Active"), 
        ("d", "Deleted")
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.IntegerField()
    weight = models.IntegerField()
    photo = models.URLField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')

    objects = DishManager()

    def __str__(self):
        return self.name
    
class OrderManager(models.Manager):
    def generate_qr_code(self, order):
        qr_data = f"Order ID: {order.id}, Table Number: {order.table_number}"
        qr = segno.make(qr_data)

        buffer = BytesIO()
        qr.save(buffer, kind='png', scale=5)
        buffer.seek(0)

        return buffer

    def get_one_order(self, order_id):
        orders = Order.objects.filter(id=order_id)
        return orders.get(id=order_id)

class Order(models.Model):
    STATUS_CHOICES = [
        ('dr', "Draft"),
        ('del', "Deleted"), 
        ('f', "Formed"), 
        ('c', "Completed"), 
        ('r', "Rejected")
    ]
    table_number = models.IntegerField()
    status = models.CharField(choices=STATUS_CHOICES, max_length=9, default='dr')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(User, related_name='orders_created', on_delete=models.SET_NULL, null=True)
    moderator = models.ForeignKey(User, related_name='orders_moderated', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='draft'), name='unique_draft_per_user')
        ]

    objects = OrderManager()

    def __str__(self):
        return self.id
    
class OrderDish(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    count = models.IntegerField()

    class Meta:
        unique_together = ('order', 'dish', 'user')
    








