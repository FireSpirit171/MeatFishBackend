from django.shortcuts import render, get_object_or_404, redirect
from app.models import Dish, Order, OrderDish
from app.services import order_service, qr_generate
from django.db import connection

def add_dish_to_order(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    user = request.user

    try:
        order = Order.objects.get(creator=user, status='dr')
    except Order.DoesNotExist:
        order = Order.objects.create(creator=user, table_number=1, status='dr')

    order_dish, created = OrderDish.objects.get_or_create(order=order, count=1, dish=dish, user=user)
    if not created:
        order_dish.count += 1
    order_dish.save()

    return redirect('order', order_id=order.id)

def delete_order(request, order_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_order SET status = 'del' WHERE id = %s", [order_id])
    
    return redirect('index')

def index(request):
    min_value = request.GET.get('min_value')
    max_value = request.GET.get('max_value')

    if min_value:
        min_value = int(min_value)
    if max_value:
        max_value = int(max_value)

    if min_value and max_value and min_value > max_value:
        min_value, max_value = max_value, min_value

    user = request.user
    curr_order = Order.objects.filter(creator=user, status='dr').first()

    if curr_order:
        order_info = {
            'id': curr_order.id,
            'count': Order.objects.get_total_dish_count(curr_order)
        }
    else:
        order_info = None

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
    try:
        curr_order = Order.objects.get(id=order_id)
        if curr_order.status == 'del':
            raise Order.DoesNotExist 
    except Order.DoesNotExist:
        return render(request, 'order.html', {"error_message": "Нельзя просмотреть заказ."})

    orders_with_names, total_person_price, total = order_service.calculate_order_details(curr_order)
    total_dish_count = Order.objects.get_total_dish_count(curr_order)
    number_of_guests = OrderDish.objects.filter(order=curr_order).values('user').distinct().count()
    qr_image = qr_generate.get_qr(curr_order, orders_with_names, total_person_price, total)

    return render(request, 'order.html', {
        "order": curr_order,
        "table_number": curr_order.table_number,
        "orders_with_names": orders_with_names,
        "total_person_price": total_person_price,
        "total": total,
        "count_dishes": total_dish_count,
        "number_of_guests": number_of_guests,
        "qr": qr_image,
    })


