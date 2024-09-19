from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Dish, Order, OrderDish
from test_data import FOOD_DATA

class Command(BaseCommand):
    help = 'Fills the database with test data: dishes, users, orders, and order-dish relationships'

    def handle(self, *args, **kwargs):
        # Создание блюд
        for food in FOOD_DATA:
            dish, created = Dish.objects.get_or_create(
                id=food['id'],
                defaults={
                    'name': food['name'],
                    'type': food['type'],
                    'description': food['description'],
                    'price': food['price'],
                    'weight': food['weight'],
                    'photo': food['photo'],
                    'status': 'a'  # Все блюда активны по умолчанию
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Dish "{dish.name}" added.'))
            else:
                self.stdout.write(self.style.WARNING(f'Dish "{dish.name}" already exists.'))

        # Создание пользователей с простыми паролями
        for i in range(1, 11):
            password = ''.join(str(x) for x in range(1, i+1))  # Пример: для id=5, пароль будет '12345'
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={'password': password}
            )
            if created:
                user.set_password(password)  # Django требует явной установки пароля через set_password
                user.save()

                if i == 9 or i == 10:  # Назначаем 9-го и 10-го пользователей модераторами
                    user.is_staff = True
                    user.save()

                self.stdout.write(self.style.SUCCESS(f'User "{user.username}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.username}" already exists.'))

        # Создание заказов
        orders_data = [
            {'table_number': 1, 'creator_id': 1},
            {'table_number': 2, 'creator_id': 2},
            {'table_number': 3, 'creator_id': 3},
            {'table_number': 4, 'creator_id': 4},
            {'table_number': 5, 'creator_id': 5},
        ]

        for data in orders_data:
            order, created = Order.objects.get_or_create(
                table_number=data['table_number'],
                creator_id=data['creator_id'],
                defaults={'status': 'dr'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Order for table {order.table_number} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Order for table {order.table_number} already exists.'))

        # Создание записей в many-to-many OrderDish
        order_dish_data = [
            # Для первого заказа один человек (первый пользователь)
            {'order_id': 1, 'dish_id': 1, 'user_id': 1, 'count': 2},
            # Во втором заказе 1 и 2 пользователь
            {'order_id': 2, 'dish_id': 2, 'user_id': 1, 'count': 1},
            {'order_id': 2, 'dish_id': 2, 'user_id': 2, 'count': 1},
            # В третьем заказе 1, 2 и 3 пользователь
            {'order_id': 3, 'dish_id': 1, 'user_id': 1, 'count': 1},
            {'order_id': 3, 'dish_id': 2, 'user_id': 2, 'count': 2},
            {'order_id': 3, 'dish_id': 1, 'user_id': 3, 'count': 1},
            # В четвертом заказе только 4 пользователь
            {'order_id': 4, 'dish_id': 1, 'user_id': 4, 'count': 3},
            # В пятом заказе 4 и 5 пользователь
            {'order_id': 5, 'dish_id': 2, 'user_id': 4, 'count': 1},
            {'order_id': 5, 'dish_id': 2, 'user_id': 5, 'count': 2},
        ]

        for od in order_dish_data:
            order_dish, created = OrderDish.objects.get_or_create(
                order_id=od['order_id'],
                dish_id=od['dish_id'],
                user_id=od['user_id'],
                defaults={'count': od['count']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'OrderDish entry for order {od["order_id"]}, dish {od["dish_id"]}, user {od["user_id"]} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'OrderDish entry for order {od["order_id"]}, dish {od["dish_id"]}, user {od["user_id"]} already exists.'))
