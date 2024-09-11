from django.shortcuts import render
from app.services import order_service, qr_generate
from test_data import SERVICES_DATA, ORDERS_DATA

def index(request):
    types = ["ribs", "steak", "fish", "soup", "salad", "pizza", "appetizers", "snacks", "sauce", "drinks"]
    categories = {name: [] for name in types}

    for service in SERVICES_DATA:
        if service["type"] in categories:
            categories[service["type"]].append(service)

    return render(request, 'index.html', {"categories": categories})


def dish(request, dish_id):
    for service in SERVICES_DATA:
        if service['id'] == dish_id:
            dish = service
            break
    return render(request, 'dish.html', {"food": dish})

def dish_search(request):
    query = request.GET.get('q')
    if query:
        matching_dishes = [dish for dish in SERVICES_DATA if query.lower() in dish['name'].lower()]
    else:
        matching_dishes = []
    
    return render(request, 'dish_search.html', {
        'query': query,
        'dishes': matching_dishes
    })


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
