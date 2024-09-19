from django.shortcuts import render, get_object_or_404
from app.models import Dish, Order, OrderDish
from app.services import order_service

def index(request):
    min_value = request.GET.get('min_value')
    max_value = request.GET.get('max_value')
    if min_value: min_value = int(min_value)
    if max_value: max_value = int(max_value)

    if min_value and max_value and min_value > max_value:
        min_value, max_value = max_value, min_value
    
    # Получаем текущий заказ (здесь для примера с id=1)
    order_id = 1
    curr_order = get_object_or_404(Order, id=order_id)
    
    order_info = {
        'id': curr_order.id,
        'count': Order.objects.get_total_dish_count(curr_order) 
    }
    
    if min_value is not None or max_value is not None:
        dishes = Dish.objects.filter(price__gte=min_value, price__lte=max_value)
        return render(request, 'index.html', {
            'min_value': min_value,
            'max_value': max_value,
            'dishes': dishes,
            'order': order_info
        })
    
    dishes = Dish.objects.all()
    return render(request, 'index.html', {"dishes": dishes, 'order': order_info})

def dish(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    return render(request, 'dish.html', {"food": dish})

def order(request, order_id):
    curr_order = get_object_or_404(Order, id=order_id)
    
    orders_with_names, total_person_price, total = order_service.calculate_order_details(curr_order)
    total_dish_count = Order.objects.get_total_dish_count(curr_order)
    number_of_guests = OrderDish.objects.filter(order=curr_order).values('user').distinct().count()

    return render(request, 'order.html', {
        "order": curr_order,
        "table_number": curr_order.table_number,
        "orders_with_names": orders_with_names,
        "total_person_price": total_person_price,
        "total": total,
        "count_dishes": total_dish_count,
        "number_of_guests": number_of_guests
    })

