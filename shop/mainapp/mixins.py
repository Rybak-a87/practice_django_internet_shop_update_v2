from django.views.generic.detail import SingleObjectMixin
from django.views.generic import View

from .models import (
    Category,
    Cart,
    Customer,
    Notebook,
    Smartphone
)


# Миксин для вывода информации о категориях на любой странице сайта
class CategoryDetailMixin(SingleObjectMixin):
    CATEGORY_SLUG2PRODUCT_MODEL = {
        "notebooks": Notebook,
        "smartphones": Smartphone
    }

    def get_context_data(self, **kwargs):    # функция для вывода контента в вьешке (аналог <{"categories": categories}> в функции test_view)
        if isinstance(self.get_object(), Category):    # для категорий
            model = self.CATEGORY_SLUG2PRODUCT_MODEL[self.get_object().slug]
            context = super().get_context_data(**kwargs)
            context["categories"] = Category.objects.get_categories_for_left_sidebar()
            context["category_products"] = model.objects.all()
            return context
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.get_categories_for_left_sidebar()
        return context


class CartMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:    # если пользователь авторизован
            customer = Customer.objects.filter(user=request.user).first()    # поиск пользователя
            if not customer:    # если покупателя нет - создаем покупателя
                customer = Customer.objects.cteate(user=request.user)
            cart = Cart.objects.filter(owner=customer, in_order=False).first()    # поиск корзины которая относится к этому пользователю и не находится в заказе
            if not cart:    # если корзина найдена - созается новую корзина этого пользователя
                cart = Cart.objects.create(owner=customer)
        else:    # если пользовательне авторизован
            cart = Cart.objects.filter(for_anonymous_user=True).first()    # поиск корзины анонимного пользователя
            if not cart:
                cart = Cart.objects.create(for_anonymous_user=True)    # создание анонимной корзины
        self.cart = cart
        return super().dispatch(request, *args, **kwargs)