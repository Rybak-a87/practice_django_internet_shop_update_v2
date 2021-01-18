# Кастомный тег шаблона (фильтр)

from django import template
from django.utils.safestring import mark_safe

from ..models import Smartphone


register = template.Library()


# начало таблицы
TABLE_HEAD = """
                <table class="table">
                    <tbody>
             """

# конец таблицы
TABLE_TAIL = """
                    </tbody>
                </table>
             """

# содержимое таблицы
TABLE_CONTENT = """
                    <tr>
                        <td>{name}</td>
                        <td>{value}</td>
                    </tr>
                """

PRODUCT_SPEC = {
    "notebook": {
        "Диалональ": "diagonal",
        "Тип дисплея": "display_type",
        "Частота процессора": "processor_freq",
        "Оперативная память": "ram",
        "Видеокарта": "video",
        "Время работы аккумулятора": "time_without_charge"
    },
    "smartphone": {
        "Диалональ": "diagonal",
        "Тип дисплея": "display_type",
        "Разрешение экрана": "resolution",
        "Объем батареи": "accum_volume",
        "Оперативная память": "ram",
        "Встроенная память": "rom",
        "Наличие sd карты": "sd",
        "Максимальный объем SD карты": "sd_volume_max",
        "Главная камера": "main_cam_mp",
        "Фронтальная камера": "frontal_cam_mp"
    }
}


def get_product_spec(product, model_name):
    table_content = ""
    for name, value in PRODUCT_SPEC[model_name].items():
        table_content += TABLE_CONTENT.format(name=name, value=getattr(product, value))
    return table_content


@register.filter
def product_spec(product):
    model_name = product.__class__._meta.model_name
    if isinstance(product, Smartphone):
        if not product.sd:
            PRODUCT_SPEC["smartphone"].pop("Максимальный объем SD карты")
    return mark_safe(TABLE_HEAD + get_product_spec(product, model_name) + TABLE_TAIL)
