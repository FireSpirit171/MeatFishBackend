from django.shortcuts import render, get_object_or_404, redirect
from app.models import Dish, Dinner, DinnerDish
from app.services import dinner_service, qr_generate
from django.db import connection

def add_dish_to_dinner(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    user = request.user

    try:
        dinner = Dinner.objects.get(creator=user, status='dr')
    except Dinner.DoesNotExist:
        dinner = Dinner.objects.create(creator=user, table_number=1, status='dr')

    dinner_dish, created = DinnerDish.objects.get_or_create(dinner=dinner, count=1, dish=dish, user=user.username)
    if not created:
        dinner_dish.count += 1
    dinner_dish.save()

    return redirect('dinner', dinner_id=dinner.id)

def delete_dinner(request, dinner_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE app_dinner SET status = 'del' WHERE id = %s", [dinner_id])
    
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
    curr_dinner = Dinner.objects.filter(creator=user, status='dr').first()

    if curr_dinner:
        dinner_info = {
            'id': curr_dinner.id,
            'count': Dinner.objects.get_total_dish_count(curr_dinner)
        }
    else:
        dinner_info = None

    if min_value is not None or max_value is not None:
        dishes = Dish.objects.filter(price__gte=min_value, price__lte=max_value)
        return render(request, 'index.html', {
            'min_value': min_value,
            'max_value': max_value,
            'dishes': dishes,
            'dinner': dinner_info
        })

    dishes = Dish.objects.all()
    return render(request, 'index.html', {"dishes": dishes, 'dinner': dinner_info})

def dish(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    return render(request, 'dish.html', {"food": dish})

def dinner(request, dinner_id):
    try:
        curr_dinner = Dinner.objects.get(id=dinner_id)
        if curr_dinner.status == 'del':
            raise Dinner.DoesNotExist 
    except Dinner.DoesNotExist:
        return render(request, 'dinner.html', {"error_message": "Нельзя просмотреть заказ."})

    dinners_with_names, total_person_price, total = dinner_service.calculate_dinner_details(curr_dinner)
    total_dish_count = Dinner.objects.get_total_dish_count(curr_dinner)
    number_of_guests = DinnerDish.objects.filter(dinner=curr_dinner).values('user').distinct().count()
    qr_image = qr_generate.get_qr(curr_dinner, dinners_with_names, total_person_price, total)

    return render(request, 'dinner.html', {
        "dinner": curr_dinner,
        "table_number": curr_dinner.table_number,
        "dinners_with_names": dinners_with_names,
        "total_person_price": total_person_price,
        "total": total,
        "count_dishes": total_dish_count,
        "number_of_guests": number_of_guests,
        "qr": qr_image,
    })