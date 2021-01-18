from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone


User = get_user_model()    # юзер из settings.AUTH_USER_MODEL


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя категории")    # строка из 255 символов
    slug = models.SlugField(unique=True)    # уникальный слаг для URL

    def __str__(self):
        return self.name

    def get_absolute_url(self):    # настройка url
        return reverse("mainapp:category_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    category = models.ForeignKey(Category, verbose_name="Категория",
                                 on_delete=models.CASCADE)  # связь с объектом Category (один ко многим)
    title = models.CharField(max_length=255, verbose_name="Наименование")
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name="Изображение", upload_to="mainapp/")    # изображение (аргумент <upload_to=""> - путь сохранения файла)
    description = models.TextField(verbose_name="Описание", null=True)  # большой текст (null=True - может быть пустым)
    price = models.DecimalField(max_digits=9, decimal_places=2,
                                verbose_name="Цена")  # 1-количество цифр 2-цифры после запятой

    def __str__(self):
        return self.title

    def get_model_name(self):
        return self.__class__.__name__.lower()

    def get_absolute_url(self):
        return reverse("mainapp:product_detail", kwargs={"slug": self.slug})


class CartProduct(models.Model):
    user = models.ForeignKey("Customer", verbose_name="Покупатель", on_delete=models.CASCADE)    #? первый аргумент
    cart = models.ForeignKey(
        "Cart", verbose_name="Корзина", on_delete=models.CASCADE, related_name="related_products"
    )    # related_name - название, используемое для обратной связи от связанной модели
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)    # челое число больше нуля
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Общая цена")

    def __str__(self):
        return f"Продукт {self.content_object.title} (для корзины)"

    def save(self, *args, **kwargs):    # для определения цены товара в зависимости от его количества
        self.final_price = self.qty * self.product.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    owner = models.ForeignKey("Customer", null=True, verbose_name="Владелец", on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name="related_cart")    # связь с объектом CartProdukt (многие ко многим). blank=True - для проверки даных. поле может быть пустым
    total_product = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(
        max_digits=9, decimal_places=2, verbose_name="Общая цена", default=0
    )
    in_order = models.BooleanField(default=False)    # для определения является корзина в заказе или нет (по умолчанию - нет)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE)    # связь на юзера из settings
    phone = models.CharField(max_length=20, verbose_name="Номер телефона", null=True, blank=True)    # желательно чтоб было обязательным к заполнению
    address = models.CharField(max_length=255, verbose_name="Адрес", null=True, blank=True)    # желательно чтоб было обязательным к заполнению
    orders = models.ManyToManyField(
        "Order", verbose_name="Заказы покупателя", related_name="related_customer", blank=True
    )

    def __str__(self):
        return f"Покупатель {self.user.first_name} {self.user.last_name}"


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_READY = "is_ready"
    STATUS_COMPLETED = "completed"

    BUYING_TYPE_SELF = "self"
    BUYING_TYPE_DELIVERY = "delivery"

    STATUS_CHOICES = (
        (STATUS_NEW, "Новый заказ"),
        (STATUS_IN_PROGRESS, "Заказ в обработке"),
        (STATUS_READY, "Заказ готов"),
        (STATUS_COMPLETED, "Заказ выполнен")
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, "Самовывоз"),
        (BUYING_TYPE_DELIVERY, "Доставка")
    )

    customer = models.ForeignKey(
        Customer, verbose_name="Покупатель",
        related_name="related_orders", on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=255, verbose_name="Имя")
    last_name = models.CharField(max_length=255, verbose_name="Фамилия")
    cart = models.ForeignKey(Cart, verbose_name="Корзина", on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name="Номер телефона")
    address = models.CharField(max_length=1024, verbose_name="Адрес", null=True, blank=True)
    status = models.CharField(
        max_length=100, verbose_name="Статус заказа",
        choices=STATUS_CHOICES,    # choices - это всплывающий список из переданного в него кортежа
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100, verbose_name="Тип заказа",
        choices=BUYING_TYPE_CHOICES, default=BUYING_TYPE_SELF
    )
    comment = models.TextField(verbose_name="Комментаний к заказу", null=True, blank=True)
    created_date = models.DateTimeField(verbose_name="Дата создания заказа", auto_now=True)    # не будет отображен в админке при заполнении формы
    order_date = models.DateField(verbose_name="Дата получения заказа", default=timezone.now)

    def __str__(self):
        return str(self.id)
