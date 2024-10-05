import segno
import base64
from io import BytesIO

def get_qr(dinner_info, person_dinners, person_price, total):
    modified_person_price = {}
    i = 0
    for person in person_dinners.keys():
        modified_person_price[person] = person_price[i]
        i += 1

    info = f"Заказ №{dinner_info.id}\nСтол №{dinner_info.table_number}\n\n"
    for person, dishes in person_dinners.items():
        info += f'Гость №{person}:\n'
        for dish in dishes:
            info += f"\t{dish[1]} - {dish[3]}шт. = {dish[2]}р.\n"
        info += f"\tСумма = {modified_person_price[person]}р.\n"
    info += f"Общая сумма = {total}р."

    qr = segno.make(info)
    buffer = BytesIO()
    qr.save(buffer, kind='png')
    buffer.seek(0)
    qr_image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return f"data:image/png;base64,{qr_image_base64}"




