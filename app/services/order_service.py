from test_data import FOOD_DATA

def get_services_dict():
    return {service['id']: service['name'] for service in FOOD_DATA}

def get_price_dict():
    return {service['id']: service['price'] for service in FOOD_DATA}

def get_photos_dict():
    return {service['id']: service['photo'] for service in FOOD_DATA}

def calculate_order_details(order):
    services_dict = get_services_dict()
    price_dict = get_price_dict()
    photos_dict = get_photos_dict()

    total = 0
    orders_with_names = {}
    total_person_price = []

    for person, dishes in order["orders"].items():
        orders_with_names[person] = [
            (dish_id, services_dict[dish_id], price_dict[dish_id] * count, count, photos_dict[dish_id])
            for dish_id, count in dishes.items()
        ]

        total_price = sum([price_dict[dish_id] * count for dish_id, count in dishes.items()])
        total_person_price.append(total_price)
        total += total_price

    return orders_with_names, total_person_price, total

