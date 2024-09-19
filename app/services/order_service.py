from app.models import OrderDish

def calculate_order_details(order):
    # Получаем связанные записи OrderDish для текущего заказа
    order_dishes = OrderDish.objects.filter(order=order).select_related('dish', 'user').order_by('user__id')

    orders_with_names = {}
    total_person_price = []
    total = 0

    # Для каждого пользователя в заказе считаем его блюда и стоимость
    for order_dish in order_dishes:
        user_id = order_dish.user.id
        dish = order_dish.dish
        dish_price = dish.price * order_dish.count

        if user_id not in orders_with_names:
            orders_with_names[user_id] = []

        orders_with_names[user_id].append(
            (dish.id, dish.name, dish_price, order_dish.count, dish.photo)
        )

        total_price = dish_price
        total_person_price.append(total_price)
        total += total_price

    return orders_with_names, total_person_price, total
