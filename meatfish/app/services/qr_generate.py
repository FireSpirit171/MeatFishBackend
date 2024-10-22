import segno
import base64
from io import BytesIO

def generate_dinner_qr(dinner, dinner_dishes, time):
    # Формируем информацию для QR-кода
    info = f"Заказ №{dinner.id}\nСтол №{dinner.table_number}\n\n"
    person_orders = {}

    for dinner_dish in dinner_dishes:
        guest = dinner_dish.guest
        dish_info = {
            'name': dinner_dish.dish.name,
            'price': dinner_dish.dish.price,
            'count': dinner_dish.count
        }
        if guest not in person_orders:
            person_orders[guest] = []
        person_orders[guest].append(dish_info)

    # Суммируем стоимость для каждого гостя
    total_cost = 0
    for guest, dishes in person_orders.items():
        info += f'{guest}:\n'
        guest_cost = 0
        for dish in dishes:
            cost = dish['price'] * dish['count']
            guest_cost += cost
            info += f"\t{dish['name']} - {dish['count']} шт. = {cost}р.\n"
        total_cost += guest_cost
        info += f"\tСумма для {guest} = {guest_cost}р.\n"
    
    info += f"Общая сумма = {total_cost}р.\n\n"

    completed_at_str = time.strftime('%Y-%m-%d %H:%M:%S')
    info += f"Дата и время заказа: {completed_at_str}"

    # Генерация QR-кода
    qr = segno.make(info)
    buffer = BytesIO()
    qr.save(buffer, kind='png')
    buffer.seek(0)

    # Конвертация изображения в base64
    qr_image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return qr_image_base64
