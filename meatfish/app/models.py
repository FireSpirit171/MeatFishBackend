from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
import segno
from io import BytesIO

class NewUserManager(UserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        verbose_name=('groups')
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text=('Specific permissions for this user.'),
        verbose_name=('user permissions')
    )

    USERNAME_FIELD = 'email'

    objects = NewUserManager()


class DishManager(models.Manager):
    def get_one_dish(self, dish_id):
        return self.get(id=dish_id)

class Dish(models.Model):
    STATUS_CHOICES = [
        ("a", "Active"), 
        ("d", "Deleted")
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=25, null=True)
    description = models.TextField()
    price = models.IntegerField()
    weight = models.IntegerField()
    photo = models.CharField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=7, default='a')

    objects = DishManager()

    def __str__(self):
        return self.name

class DinnerManager(models.Manager):
    def generate_qr_code(self, dinner):
        qr_data = f"Order ID: {dinner.id}, Table Number: {dinner.table_number}"
        qr = segno.make(qr_data)

        buffer = BytesIO()
        qr.save(buffer, kind='png', scale=5)
        buffer.seek(0)

        return buffer

    def get_one_dinner(self, dinner_id):
        return self.get(id=dinner_id)

    def get_total_dish_count(self, dinner):
        return dinner.dinnerdish_set.aggregate(count=models.Sum('count'))['count'] or 0

class Dinner(models.Model):
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
    creator = models.ForeignKey(CustomUser, related_name='dinners_created', on_delete=models.SET_NULL, null=True)
    moderator = models.ForeignKey(CustomUser, related_name='dinners_moderated', on_delete=models.SET_NULL, null=True, blank=True)
    total_cost = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator'], condition=models.Q(status='draft'), name='unique_draft_per_user')
        ]

    objects = DinnerManager()

    def __str__(self):
        return str(self.id)

class DinnerDish(models.Model):
    dinner = models.ForeignKey(Dinner, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)    
    guest = models.CharField(max_length=100)
    count = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['dinner', 'dish'], name='unique_dinner_dish')
        ]
