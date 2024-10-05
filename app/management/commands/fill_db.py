from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Dish, Dinner, DinnerDish

URL = 'http://127.0.0.1:9000/meatfish/{}.jpg'
FOOD_DATA = [
    {
        'id': 1,
        'name': 'Рёбра свиные medium size',
        'type': 'ribs',
        'description': 'Фирменные свиные рёбра в соусе на выбор. Подаются с печёным картофелем с розмарином или красной фасолью в соусе Тако (на выбор)',
        'price': 720,
        'weight': 350,
        'photo': URL.format('1'),
    },
    {
        'id': 2,
        'name': 'Ассорти из свиных рёбер в 3 соусах',
        'type': 'ribs',
        'description': 'Сочетание разных вкусов на одной порции: соус BBQ с фисташкой и апельсиновой цедрой, соус медовый-терияки с кунжутом и зеленым луком, соус кисло-сладкий. На гарнир печеный картофель с розмарином',
        'price': 1090,
        'weight': 720,
        'photo': URL.format('2')
    },
    {
        'id': 3,
        'name': 'Мраморное говяжье ребро',
        'type': 'ribs',
        'description': 'Говяжьи рёбра в соусе на выбор. Подаются с печеным картофелем с розмарином или красной фасолью в соусе Тако (на выбор)',
        'price': 1790,
        'weight': 240,
        'photo': URL.format('3')
    },
    {
        'id': 4,
        'name': 'Фланк стейк с перечным соусом',
        'type': 'steak',
        'description': 'Стейк фланк обжаренный на гриле Прожарка стейка well done/medium well/medium/medium rare/rare. Подается на доске, посыпается крупной морской солью со сливочно перечным соусом.',
        'price': 1250,
        'weight': 230,
        'photo': URL.format('4')
    },
    {
        'id': 5,
        'name': 'Филе-миньон со стручковой фасолью',
        'type': 'steak',
        'description': 'Говяжья вырезка со стручковой фасолью, обжаренной на гриле, стручками гороха, со стейковым маслом, перечным соусом, луком шнит, печёным чесноком. Прожарка стейка well done/medium well/medium/medium rare/rare. Прожарка может перейти в более высокую в зависимости от времени доставки',
        'price': 1890,
        'weight': 390,
        'photo': URL.format('5')
    },
    {
        'id': 6,
        'name': 'Стейк Мясника',
        'type': 'steak',
        'description': 'Легендарный стейк по рецепту Конюха из песни `Ели мясо мужики` группы `Король и Шут`',
        'price': 1590,
        'weight': 320,
        'photo': URL.format('6')
    },
    {
        'id': 7,
        'name': 'Стейк из лосося с овощами гриль',
        'type': 'fish',
        'description': 'Лосось, брокколи, цуккини, кукуруза початок, масло сливочное, соус тар-тар, лимон',
        'price': 1490,
        'weight': 410,
        'photo': URL.format('7')
    },
    {
        'id': 8,
        'name': 'Стейк из сёмги с овощами гриль',
        'type': 'fish',
        'description': 'Сёмга, перец, кукуруза початок, масло сливочное, соус тар-тар, лимон',
        'price': 1290,
        'weight': 410,
        'photo': URL.format('8')
    },
    {
        'id': 9,
        'name': 'Корюшка питерская',
        'type': 'fish',
        'description': 'Жареная во фритюре свежевыловленная питерская корюшка',
        'price': 1190,
        'weight': 510,
        'photo': URL.format('9')
    },
    {
        'id': 10,
        'name': 'Куриный бульон',
        'type': 'soup',
        'description': 'Бульон с куриным филе на гриле, перепелиным яйцом, вермишелью и зеленью',
        'price': 390,
        'weight': 360,
        'photo': URL.format('10')
    },
    {
        'id': 11,
        'name': 'Сырный суп с беконом',
        'type': 'soup',
        'description': 'Куриный бульон, бекон, репчатый лук, морковь, чеснок, крахмал, сыр чеддер, плавленый сыр, сырный соус',
        'price': 490,
        'weight': 290,
        'photo': URL.format('11')
    },
    {
        'id': 12,
        'name': 'Окрошка на квасе',
        'type': 'soup',
        'description': 'Классический холодный суп русской кухни',
        'price': 420,
        'weight': 400,
        'photo': URL.format('12')
    },
    {
        'id': 13,
        'name': 'Зеленый салат с креветками',
        'type': 'salad',
        'description': 'Зеленый горошек, креветки, авокадо, брокколи, огурцы, тыквенные семечки, руккола, мини шпинат и перец чили соломкой, соус цитронет.',
        'price': 790,
        'weight': 360,
        'photo': URL.format('13')
    },
    {
        'id': 14,
        'name': 'Салат калифорнийский с киноа, авокадо и креветками',
        'type': 'salad',
        'description': 'Авокадо, зелень, креветки, киноа, томаты, кинза, устричный соус, растительное масло',
        'price': 790,
        'weight': 300,
        'photo': URL.format('14')
    },
    {
        'id': 15,
        'name': 'Салат с розовыми томатами, страчателлой, кедровыми орешками и семечками',
        'type': 'salad',
        'description': 'Томаты, кремчиз, зелень, кедровый орех, тыквенные семечки, растительное масло, красный лук, морская соль.',
        'price': 650,
        'weight': 210,
        'photo': URL.format('15')
    },
    {
        'id': 16,
        'name': 'Пицца Супермясная',
        'type': 'pizza',
        'description': 'Грудинка, пеперони, бекон, шампиньоны, перец, оливки, моццарелла, томатная паста',
        'price': 790,
        'weight': 420,
        'photo': URL.format('16')
    },
    {
        'id': 17,
        'name': 'Пицца Венеция',
        'type': 'pizza',
        'description': 'Шампиньоны, стручновая фасоль, лук, моццарелла, пармезан, томатная паста, базилик ',
        'price': 690,
        'weight': 380,
        'photo': URL.format('17')
    },
    {
        'id': 18,
        'name': 'Пицца Бавария',
        'type': 'pizza',
        'description': 'Бекон, баварские колбаски, куриная грудка, красный лук, моццарелла, томатная паста',
        'price': 790,
        'weight': 410,
        'photo': URL.format('18')
    },
    {
        'id': 19,
        'name': 'Mac and Cheese',
        'type': 'appetizers',
        'description': 'Челлентани, соус Бешамель, сыр Пармезан, сыр Моцарелла, сыр Гауда, сыр Чеддер',
        'price': 450,
        'weight': 250,
        'photo': URL.format('19')
    },
    {
        'id': 20,
        'name': 'Картофель фри с пармезаном и трюфельным маслом',
        'type': 'appetizers',
        'description': 'Обжаренный до золотистой корочки картофель фри с трюфельным маслом, украшенный пармезаном, зеленым луком и луком фри. Подается с соусом на основе сливочного сыра и трюфельной пасты',
        'price': 490,
        'weight': 240,
        'photo': URL.format('20')
    },
    {
        'id': 21,
        'name': 'Тартар из говядины',
        'type': 'appetizers',
        'description': 'Говядина, красный лук, кетчуп, соль, перец, трюфельный соус, пармезан, хлеб бородинский',
        'price': 720,
        'weight': 199,
        'photo': URL.format('21')
    },
    {
        'id': 22,
        'name': 'Начос с гуакомоле и томатной сальсой',
        'type': 'snacks',
        'description': 'Кукурузные чипсы запеченые под сырной корочкой с гуакамоле и томатной сальсой',
        'price': 390,
        'weight': 190,
        'photo': URL.format('22')
    },
    {
        'id': 23,
        'name': 'Джерки',
        'type': 'snacks',
        'description': 'Сушеная говядина под пенное',
        'price': 450,
        'weight': 260,
        'photo': URL.format('23')
    },
    {
        'id': 24,
        'name': 'Овощные палочки с соусом тар-тар',
        'type': 'snacks',
        'description': 'Огурец, сельдерей, морковь, нарезанными дольками, отдельно подается соус тартар',
        'price': 290,
        'weight': 220,
        'photo': URL.format('24')
    },
    {
        'id': 25,
        'name': 'Сырный соус',
        'type': 'sauce',
        'description': 'Идеален для любого вида картофеля',
        'price': 100,
        'weight': 50,
        'photo': URL.format('25')
    },
    {
        'id': 26,
        'name': 'Кетчуп',
        'type': 'sauce',
        'description': 'Подходит к рёбрам и стейкам',
        'price': 100,
        'weight': 50,
        'photo': URL.format('26')
    },
    {
        'id': 27,
        'name': 'Соус тар-тар',
        'type': 'sauce',
        'description': 'Для овощной нарезки',
        'price': 100,
        'weight': 50,
        'photo': URL.format('27')
    },
    {
        'id': 28,
        'name': 'Домашний лимонад',
        'type': 'drinks',
        'description': 'Освежающий негазированный напиток с гуанабаной и базиликом',
        'price': 380,
        'weight': 200,
        'photo': URL.format('28')
    },
    {
        'id': 29,
        'name': 'Морс',
        'type': 'drinks',
        'description': 'Лёгкий напиток из натуральных ягод',
        'price': 190,
        'weight': 200,
        'photo': URL.format('29')
    },
    {
        'id': 30,
        'name': 'Red Bull',
        'type': 'drinks',
        'description': 'Бодрящий напиток для долгого вечера',
        'price': 300,
        'weight': 250,
        'photo': URL.format('30')
    }
]

class Command(BaseCommand):
    help = 'Fills the database with test data: dishes, users, dinners, and dinner-dish relationships'

    def handle(self, *args, **kwargs):
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
                    'status': 'a' 
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Dish "{dish.name}" added.'))
            else:
                self.stdout.write(self.style.WARNING(f'Dish "{dish.name}" already exists.'))

        for i in range(1, 11):
            password = ''.join(str(x) for x in range(1, i+1)) 
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={'password': password}
            )
            if created:
                user.set_password(password)
                user.save()

                if i == 9 or i == 10: 
                    user.is_staff = True
                    user.save()

                self.stdout.write(self.style.SUCCESS(f'User "{user.username}" created with password "{password}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user.username}" already exists.'))

        dinners_data = [
            {'table_number': 1, 'creator_id': 1},
            {'table_number': 2, 'creator_id': 2},
            {'table_number': 3, 'creator_id': 3},
            {'table_number': 4, 'creator_id': 4},
            {'table_number': 5, 'creator_id': 5},
        ]

        for data in dinners_data:
            dinner, created = Dinner.objects.get_or_create(
                table_number=data['table_number'],
                creator_id=data['creator_id'],
                defaults={'status': 'dr'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Dinner for table {dinner.table_number} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Dinner for table {dinner.table_number} already exists.'))

        dinner_dish_data = [
            # Для первого заказа один человек (первый пользователь)
            {'dinner_id': 1, 'dish_id': 1, 'user': 'user1', 'count': 1},
            # Во втором заказе 1 и 2 пользователь
            {'dinner_id': 2, 'dish_id': 2, 'user': 'user1', 'count': 1},
            {'dinner_id': 2, 'dish_id': 3, 'user': 'user2', 'count': 1},
            # В третьем заказе 1, 2 и 3 пользователь
            {'dinner_id': 3, 'dish_id': 4, 'user': 'user1', 'count': 1},
            {'dinner_id': 3, 'dish_id': 5, 'user': 'user2', 'count': 1},
            {'dinner_id': 3, 'dish_id': 6, 'user': 'user3', 'count': 1},
            # В четвертом заказе только 4 пользователь
            {'dinner_id': 4, 'dish_id': 7, 'user': 'user4', 'count': 1},
            # В пятом заказе 4 и 5 пользователь
            {'dinner_id': 5, 'dish_id': 8, 'user': 'user4', 'count': 1},
            {'dinner_id': 5, 'dish_id': 9, 'user': 'user5', 'count': 1},
        ]

        for od in dinner_dish_data:
            dinner_dish, created = DinnerDish.objects.get_or_create(
                dinner_id=od['dinner_id'],
                dish_id=od['dish_id'],
                user=od['user'],
                defaults={'count': od['count']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'DinnerDish entry for dinner {od["dinner_id"]}, dish {od["dish_id"]}, user {od["user"]} created.'))
            else:
                self.stdout.write(self.style.WARNING(f'DinnerDish entry for dinner {od["dinner_id"]}, dish {od["dish_id"]}, user {od["user"]} already exists.'))
