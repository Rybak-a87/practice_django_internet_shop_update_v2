from django.db import transaction
from django.shortcuts import render
from django.contrib import messages    # выводит информацию о каких либо осуществленных действиях
from django.http import HttpResponseRedirect    # для перенаправления
from django.views.generic import DetailView, View
from django.contrib.auth import authenticate, login

from .models import Product, Category, Customer, Order, CartProduct
from .mixins import CartMixin     # должет первый по порядку наследоватся
from .forms import OrderForm, LoginForm, RegistrationForm
from .utils import recalc_cart


class BaseView(CartMixin, View):
    def get(self, request, *args, **kwargs):    # метод - аналог функции test_base (гет запрос)
        categories = Category.objects.all()   # для истользования объекта в шаблоне
        products = Product.objects.all()   # для вывода продуктов на главной странице

        context = {
            "categories": categories,
            "products": products,
            "cart": self.cart,
        }
        return render(request, "base/base.html", context)


class ProductDetailView(CartMixin, DetailView):
    context_object_name = "product"
    template_name = "mainapp/product_detail.html"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):    # для вывода необходимой информации для шаблона
        context = super().get_context_data(**kwargs)
        context["cart"] = self.cart
        return context


class CategoryDetailView(CartMixin, DetailView):
    model = Category
    queryset = Category.objects.all()    # при использовании фильтра (.filter(key=value)) - можно использовать символы подчеркивания (__) для навигации по многим уровням отношений (ForeignKey / ManyToManyField) по своему усмотрению.
    context_object_name = "category"
    template_name = "mainapp/category_detail.html"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart"] = self.cart
        return context


class AddToCartView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        # логика добавление в корзину
        product_slug = kwargs.get("slug")    # слаг товара
        product = Product.objects.get(slug=product_slug)    # получение продукта через модель, находя продукт по слагу товара
        cart_product, created = CartProduct.objects.get_or_create(    # создание нового карт-продукт объекта с необходимым набором аргументов (get_or_create - для проверки наличия товара в корзине (возвращает кортеж)
            user=self.cart.owner, cart=self.cart, product=product
        )
        if created:    # проверяет был ли создан новый объект (чтобы не добавлять один и тот же товар в корзину)
            self.cart.products.add(cart_product)    # добавление в корзину (add - это добавление в многих ко многим)
        recalc_cart(self.cart)    # сохранить информацию в корзину
        messages.add_message(request, messages.INFO, "Товар успешно добавлен")    # вывод информации о действии (при тестировании - хакоментировать)
        return HttpResponseRedirect("/cart/")    # перенаправить сразу в корзину


class DeleteFromCartView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get("slug")  # слаг товара
        product = Product.objects.get(slug=product_slug)  # получение продукта через модель, находя продукт по слагу товара
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        self.cart.products.remove(cart_product)  # удаление из корзины (remove - это удаление в многих ко многим)
        cart_product.delete()    # удаление товара из базы данных
        recalc_cart(self.cart)    # сохранить информацию в корзину
        messages.add_message(request, messages.INFO, "Товар успешно удален")  # вывод информации о действии
        return HttpResponseRedirect("/cart/")  # перенаправить сразу в корзину


class ChangeQTYView(CartMixin, View):
    def post(self, request, *args, **kwargs):    # пост запрос
        product_slug = kwargs.get("slug")  # слаг товара
        product = Product.objects.get(slug=product_slug)  # получение продукта через модель, находя продукт по слагу товара
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        qty = int(request.POST.get("qty"))
        cart_product.qty = qty
        cart_product.save()    # посчитать наличие корзины
        recalc_cart(self.cart)    # сохранить информацию в корзину
        messages.add_message(request, messages.INFO, "Количество успешно изменено")  # вывод информации о действии
        return HttpResponseRedirect("/cart/")


class CartView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        context = {
            "cart": self.cart,
            "categories": categories,
        }
        return render(request, "mainapp/cart.html", context)


class CheckoutView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = OrderForm(request.POST or None)    # пост запрос или ничего (инстансирование формы)
        context = {
            "cart": self.cart,
            "categories": categories,
            "form": form,
        }
        return render(request, "mainapp/checkout.html", context)


class MakeOrderView(CartMixin, View):
    @transaction.atomic    # для коректной работы метода post (в случае некоректной работы все откатится)
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        if form.is_valid():    #для работы с формой ее нужно поволидировать
            new_order = form.save(commit=False)    # сохранить для работы с формой (в подвешенном состоянии)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data["first_name"]    # берем данные с формы
            new_order.last_name = form.cleaned_data["last_name"]
            new_order.phone = form.cleaned_data["phone"]
            new_order.address = form.cleaned_data["address"]
            new_order.buying_type = form.cleaned_data["buying_type"]
            new_order.order_date = form.cleaned_data["order_date"]
            new_order.comment = form.cleaned_data["comment"]
            self.cart.in_order = True
            self.cart.save()    # сохранить корзины в статусе True
            new_order.cart = self.cart
            new_order.save()    # сохранить заказ в бд
            customer.orders.add(new_order)    # записать пользователю его заказ в историю заказов
            messages.add_message(request, messages.INFO, "Спасибо за заказ. Менеджер с Вами свяжется.")
            return HttpResponseRedirect("/")
        return HttpResponseRedirect("/checkout/")


class LoginView(CartMixin, View):
    def get(self, request, *args, **kwargs):    #get - для отрисовки формы
        form = LoginForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            "form": form,
            "categories": categories,
            "cart": self.cart
        }
        return render(request, "mainapp/login.html", context)

    def post(self, request, *args, **kwargs):    # post - для отправки данных в форму
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data["username"]    # забираем логин и пароль
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)    # авторизация
            if user:
                login(request, user)    # залогинитmься
                return HttpResponseRedirect("/")
        context = {"form": form, "cart": self.cart}
        return render(request, "mainapp/login.html", context)


class RegistrationView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            "form": form,
            "categories": categories,
            "cart": self.cart
        }
        return render(request, "mainapp/registration.html", context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data["username"]
            new_user.email = form.cleaned_data["email"]
            new_user.first_name = form.cleaned_data["first_name"]
            new_user.last_name = form.cleaned_data["last_name"]
            new_user.save()
            new_user.set_password(form.cleaned_data["password"])    # задать пароль
            new_user.save()
            Customer.objects.create(
                user=new_user,
                phone=form.cleaned_data["phone"],
                address=form.cleaned_data["address"]
            )
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            login(request, user)
            return HttpResponseRedirect("/")
        context = {"form": form, "cart": self.cart}
        return render(request, "mainapp/registration.html", context)

class ProfileView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        orders = Order.objects.filter(customer=customer).order_by("-created_date")    # сортировка в убывающем порядке
        categories = Category.objects.all()
        context = {
            "orders": orders,
            "categories": categories,
            "cart": self.cart
        }
        return render(request, "mainapp/profile.html", context)

