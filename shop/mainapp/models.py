# import sys
# from PIL import Image    # - для работы с изображением

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils import timezone
# from django.core.files.uploadedfile import InMemoryUploadedFile    # - для работы с изображением

# from io import BytesIO    # для преобразования изображения в байты


User = get_user_model()    # юзер из settings.AUTH_USER_MODEL


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):    # функция для настройки URL для объекта
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={"ct_model": ct_model, "slug": obj.slug})


class MinResolutionErrorException(Exception):    # ошибка при меньшем разрешении картинки
    pass


class MaxResolutionErrorException(Exception):    # ошибка при большем разрешении картинки
    pass


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):    # для вывода продуктов на главную страницу
        with_respect_to = kwargs.get("with_respect_to")    # агрумент принимает товат (with_respect_to="продукты") которые первыми будут идти на главной странице
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by("-id")[:5]    # 5 последних записей
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products,
                        key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to),
                        reverse=True
                    )
        return products


class LatestProducts:    # вывод товара на главную страницу
    objects = LatestProductsManager()


class CategoryManager(models.Manager):
    CATEGORY_NAME_COUNT_NAME = {
        "Ноутбуки": "notebook__count",
        "Смартфоны": "smartphone__count"
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count("notebook", "smartphone")
        qs = list(self.get_queryset().annotate(*models))    # инструмент анотации (существует еще инструмент агрегации)
        data = [
            dict(
                name=c.name, url=c.get_absolute_url(),
                count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name])
            ) for c in qs
        ]
        return data


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя категории")    # строка из 255 символов
    slug = models.SlugField(unique=True)    # уникальный слаг для URL
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):    # настройка url
        return reverse("mainapp:category_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    # MIN_RESOLUTION = (400, 400)  # минимально допустимое разрешение изображение
    # MAX_RESOLUTION = (800, 800)  # максимально допустимое разрешение изображение
    # MAX_IMAGE_SIZE = 3145728  # (3MB) # макмимально допустимый размер файла (изображения)

    class Meta:
        abstract = True  # делает данную модель обстрактной (созлать для нее миграцию не возможно) (некий каркас для продукта)

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


'''
    def save(self, *args, **kwargs):  # переопределение и сохранение изображения
        """ проверка по размеру и разрешению изображения """
        # image = self.image
        # img = Image.open(image)
        # min_height, min_width = self.MIN_RESOLUTION  # минимальное разрешение картинки
        # max_height, max_width = self.MAX_RESOLUTION  # максимальное разрешение картинки
        # if img.height < min_height or img.width < min_width:  # проверка на минимальное разрешение изображения
        #     raise MinResolutionErrorException("Разрешение изображения меньше минимального!")
        # if img.height > max_height or img.width > max_width:  # проверка на максимальное разрешение изображения
        #     raise MaxResolutionErrorException("Разрешение изображения больше максимального!")
        # super().save(*args, **kwargs)

        """ обрезка изображения """
        image = self.image
        img = Image.open(image)
        new_img = img.convert("RGB")  # конвертирование изображения c "RGBA" в "RGB"
        resize_new_img = new_img.resize((200, 200),
                                        resample=Image.ANTIALIAS)  # (первый способ) 1-до какого разрешения уменьшить изображение (200x200) 2-способ уменьшения (resize необходимо заносить в новую переменную)
        # new_img.thumbnail((200, 200),resample=Image.ANTIALIAS)    # (второй способ) не нужно заносить в новую переменную (меняет существующюю переменную)
        filestream = BytesIO()  # преобразование изображения в поток данных (байты)
        resize_new_img.save(filestream, "JPEG", quality=90)  # сохранить изображение в filestream, формат, качество
        filestream.seek(0)
        name = ".".join(self.image.name.split('.'))
        self.image = InMemoryUploadedFile(  # 1-файл 2-название поля 3-имя файла 4-тип, 5-размер 6-charset?
            filestream, "imageField", name, "jpeg/image", sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)
'''


class Notebook(Product):
    diagonal = models.CharField(max_length=255, verbose_name="Диагональ")
    display_type = models.CharField(max_length=255, verbose_name="Тип дисплея")
    processor_freq = models.CharField(max_length=255, verbose_name="Частота процессора")
    ram = models.CharField(max_length=255, verbose_name="Оперативная память")
    video = models.CharField(max_length=255, verbose_name="Видеокарта")
    time_without_charge = models.CharField(max_length=255, verbose_name="Время работы аккумулятора")

    def __str__(self):
        return f"{self.category.name} : {self.title}"

    def get_absolute_url(self):
        return get_product_url(self, "mainapp:product_detail")


class Smartphone(Product):
    diagonal = models.CharField(max_length=255, verbose_name="Диагональ")
    display_type = models.CharField(max_length=255, verbose_name="Тип дисплея")
    resolution = models.CharField(max_length=255, verbose_name="Разрешение экрана")
    accum_volume = models.CharField(max_length=255, verbose_name="Объем батареи")
    ram = models.CharField(max_length=255, verbose_name="Оперативная память")
    rom = models.CharField(max_length=255, verbose_name="Встроенная память")
    sd = models.BooleanField(default=True, verbose_name="Наличие SD карты")    # булиевское поле (флажек)
    sd_volume_max = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Максимальный объем SD карты"
    )
    main_cam_mp = models.CharField(max_length=255, verbose_name="Главная камера")
    frontal_cam_mp = models.CharField(max_length=255, verbose_name="Фронтальная камера")

    def __str__(self):
        return f"{self.category.name} : {self.title}"

    def get_absolute_url(self):
        return get_product_url(self, "mainapp:product_detail")

    # @property
    # def sd(self):
    #     if self.sd:
    #         return "Да"
    #     return "Нет"


class CartProduct(models.Model):
    user = models.ForeignKey("Customer", verbose_name="Покупатель", on_delete=models.CASCADE)    #? первый аргумент
    cart = models.ForeignKey(
        "Cart", verbose_name="Корзина", on_delete=models.CASCADE, related_name="related_products"
    )    # related_name - название, используемое для обратной связи от связанной модели
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)    # ContentType - микрофреймворк который видетвсе модели в Install apps (все модели которые есть в проекте)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    qty = models.PositiveIntegerField(default=1)    # челое число больше нуля
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name="Общая цена")

    def __str__(self):
        return f"Продукт {self.content_object.title} (для корзины)"

    def save(self, *args, **kwargs):    # для определения цены товара в зависимости от его количества
        self.final_price = self.qty * self.content_object.price
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


''' для коректной работы метода - перенесено с файл utils.py    
    # def save(self, *args, **kwargs):    # пересчитать корзиту (какая сумма товаров и какое количество товара в корзине)
    #     cart_data = self.products.aggregate(models.Sum("final_price"), models.Count("id"))    # <aggregate> принимает выражение (посчитать общюю сумму всех продуктов и количество товаров в корзине)
    #     # определение суммы корзины (с замена None на 0)
    #     if cart_data.get("final_price__sum"):
    #         self.final_price = cart_data["final_price__sum"]
    #     else:
    #         self.final_price = 0
    #     self.total_product = cart_data["id__count"]    # определение количества товаров в корзине
    #     super().save(*args, **kwargs)
'''


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


'''
# для теста и настройки медиа контента
class TestModelForImage(models.Model):
    image = models.ImageField()

    def __str__(self):
        return str(self.id)
        
    def save(self, *args, **kwargs):  # переопределение и сохранение изображения
        """ проверка по размеру и разрешению изображения """
        # image = self.image
        # img = Image.open(image)
        # min_height, min_width = self.MIN_RESOLUTION  # минимальное разрешение картинки
        # max_height, max_width = self.MAX_RESOLUTION  # максимальное разрешение картинки
        # if img.height < min_height or img.width < min_width:  # проверка на минимальное разрешение изображения
        #     raise MinResolutionErrorException("Разрешение изображения меньше минимального!")
        # if img.height > max_height or img.width > max_width:  # проверка на максимальное разрешение изображения
        #     raise MaxResolutionErrorException("Разрешение изображения больше максимального!")
        # super().save(*args, **kwargs)

        """ обрезка изображения """
        image = self.image
        img = Image.open(image)
        new_img = img.convert("RGB")  # конвертирование изображения c "RGBA" в "RGB"
        resize_new_img = new_img.resize((200, 200),
                                        resample=Image.ANTIALIAS)  # (первый способ) 1-до какого разрешения уменьшить изображение 2-способ уменьшения (resize необходимо заносить в новую переменную)
        # new_img.thumbnail((200, 200),resample=Image.ANTIALIAS)    # (второй способ) не нужно заносить в новую переменную (меняет существующюю переменную)
        filestream = BytesIO()  # преобразование изображения в поток данных (байты)
        resize_new_img.save(filestream, "JPEG", quality=90)  # сохранить изображение в filestream, формат, качество
        filestream.seek(0)
        name = ".".join(self.image.name.split('.'))
        self.image = InMemoryUploadedFile(  # 1-файл 2-название поля 3-имя файла 4-тип, 5-размер 6-charset?
            filestream, "imageField", name, "jpeg/image", sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)
'''
