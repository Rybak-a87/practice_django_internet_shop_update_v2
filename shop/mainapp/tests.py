from decimal import Decimal
from unittest import mock    # эмитирует что угодно (внешнее апи и т.д)
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile


from .models import Category, Notebook, CartProduct, Cart, Customer
from .views import recalc_cart, AddToCartView, BaseView


User = get_user_model()


class ShopTestCases(TestCase):
    def setUp(self) -> None:    # метод для предварительных настроек тестирования (создаются объекты которые будут использоватся в тестах)
        self.user = User.objects.create(username="testuser", password="password")
        self.category = Category.objects.create(name="Ноутбуки", slug="notebooks")
        image = SimpleUploadedFile("notebook_img.jpg", content=b"", content_type="imega/jpg")    # создаем имитацию изображения
        self.notebook = Notebook.objects.create(
            category=self.category,
            title="test_noutbook",
            slug="test-slug",
            image=image,
            price=Decimal("50000.00"),
            diagonal="17.3",
            display_type="IPS",
            processor_freq="3.4 GHz",
            ram="6 Gb",
            video="GeForce GTX",
            time_without_charge="10 hours"
        )
        self.customer = Customer.objects.create(user=self.user, phone="1234567890", address="Address")
        self.cart = Cart.objects.create(owner=self.customer)
        self.cart_product = CartProduct.objects.create(
            user=self.customer,
            cart=self.cart,
            content_object = self.notebook
        )

    def test_add_to_cart(self):    # каждому методу добавлять префикс <test> (тест 1 - добавление товара в корзину (топорно))
        self.cart.products.add(self.cart_product)
        recalc_cart(self.cart)
        self.assertIn(self.cart_product, self.cart.products.all())    # проверка 1 - данный объект находится в данной корзине (assertIn - вхождение чегото в какой-то котнейнер)
        self.assertEqual(self.cart.products.count(), 1)    # проверка 2 - количество обьектов - 1 (нет дублирования)
        self.assertEqual(self.cart.final_price, Decimal("50000.00"))    # проверка 3 - цена корзины равна 50000.00

    def test_response_from_add_to_cart_view(self):    # тест 2 - через имя представления
        # client = Client()    # создать клиетна
        # response = client.get("/add-to-cart/notebook/test-slug")
        factory = RequestFactory()
        request = factory.get("")
        request.user = self.user
        response = AddToCartView.as_view()(request, ct_model="notebook", slug="test-slug")
        self.assertEqual(response.status_code, 302)    # проверка - ответ от сервера статус-302
        self.assertEqual(response.url, "/cart/")    # проверка - url /cart/

    def test_mock_homepage(self):    # тест 3
        mock_data = mock.Mock(status_code=444)    # создать инстанс мока
        with mock.patch("mainapp.views.BaseView.get", return_value=mock_data) as mock_data_:    # запатчить метод (принимает путь до нужного метода и mock_data)
            factory = RequestFactory()
            request = factory.get("")
            request.user = self.user
            response = BaseView.as_view()(request)
            self.assertEqual(response.status_code, 444)    # проверка
            print("Вызван ",mock_data_.called)    # проверка - была ли вызвана mock_data_
