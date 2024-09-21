from app.models import OrderDish

def calculate_order_details(order):
    order_dishes = OrderDish.objects.filter(order=order).select_related('dish', 'user').order_by('user__id')

    orders_with_names = {}
    total_person_price = {}
    total = 0

    for order_dish in order_dishes:
        user_id = order_dish.user.id
        dish = order_dish.dish
        dish_price = dish.price * order_dish.count

        if user_id not in orders_with_names:
            orders_with_names[user_id] = []
            total_person_price[user_id] = 0

        orders_with_names[user_id].append(
            (dish.id, dish.name, dish_price, order_dish.count, dish.photo)
        )

        total_person_price[user_id] += dish_price
        total += dish_price

    return orders_with_names, list(total_person_price.values()), total

