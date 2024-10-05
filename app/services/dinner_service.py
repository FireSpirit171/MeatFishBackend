from app.models import DinnerDish

def calculate_dinner_details(dinner):
    dinner_dishes = DinnerDish.objects.filter(dinner=dinner).select_related('dish').order_by('user')  # Убираем select_related('user')

    dinners_with_names = {}
    total_person_price = {}
    total = 0

    for dinner_dish in dinner_dishes:
        username = dinner_dish.user
        dish = dinner_dish.dish
        dish_price = dish.price * dinner_dish.count

        if username not in dinners_with_names:
            dinners_with_names[username] = []
            total_person_price[username] = 0

        dinners_with_names[username].append(
            (dish.id, dish.name, dish_price, dinner_dish.count, dish.photo)
        )

        total_person_price[username] += dish_price
        total += dish_price

    return dinners_with_names, list(total_person_price.values()), total
