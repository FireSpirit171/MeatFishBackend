from django.shortcuts import render
from app.services import order_service, qr_generate
from test_data import FOOD_DATA, ORDERS_DATA

def index(request):
    # Поиск по названию
    # query = request.GET.get('dish_name')
    # if query:
    #     matching_dishes = [dish for dish in FOOD_DATA if query.lower() in dish['name'].lower()]
    #     return render(request, 'index.html', {
    #         'query': query,
    #         'dishes': matching_dishes
    #     })
    
    min_value = request.GET.get('min_value')
    max_value = request.GET.get('max_value')
    if min_value: min_value = int(min_value)
    if max_value: max_value = int(max_value)
    
    if min_value and max_value and min_value > max_value:
        min_value, max_value = max_value, min_value

    if min_value is not None or max_value is not None:
        matching_dishes = [dish for dish in FOOD_DATA if min_value <= dish['price'] <= max_value]
        return render(request, 'index.html', {
            'min_value': min_value,
            'max_value': max_value,
            'dishes': matching_dishes
        })

    else:    
        return render(request, 'index.html', {"dishes": FOOD_DATA})



def dish(request, dish_id):
    for service in FOOD_DATA:
        if service['id'] == dish_id:
            dish = service
            break
    return render(request, 'dish.html', {"food": dish})


def order(request, order_id):
    curr_order = next((order for order in ORDERS_DATA if order['id'] == order_id), None)
    if not curr_order:
        return render(request, 'order.html')

    orders_with_names, total_person_price, total = order_service.calculate_order_details(curr_order)
    qr_image = qr_generate.get_qr(curr_order, orders_with_names, total_person_price, total)

    total_dish_count = sum(
        count for person_dishes in curr_order['orders'].values() for count in person_dishes.values()
    )

    return render(request, 'order.html', {
        "order": curr_order,
        "orders_with_names": orders_with_names,
        "total_person_price": total_person_price,
        "total": total,
        "qr": qr_image,
        "count_dishes": total_dish_count
    })
