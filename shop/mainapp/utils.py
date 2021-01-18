from django.db import models    # функции для агригации


def recalc_cart(cart):    # пересчитать корзину (какая сумма товаров и какое количество товара в корзине)
    cart_data = cart.products.aggregate(models.Sum("final_price"), models.Count("id"))    # <aggregate> принимает выражение (посчитать общюю сумму всех продуктов и количество товаров в корзине)
    # определение суммы корзины (с замена None на 0)
    if cart_data.get("final_price__sum"):
        cart.final_price = cart_data["final_price__sum"]
    else:
        cart.final_price = 0
    cart.total_product = cart_data["id__count"]    # определение количества товаров в корзине
    cart.save()    # сохранение корзины
