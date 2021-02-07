from django import forms
from django.contrib.auth.models import User

from .models import Order


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["order_date"].label = "Дата получения заказа"    # для отображения коректной надписи в форме

    order_date = forms.DateField(widget=forms.TextInput(attrs={"type": "date"}))    # для упрощения выбора даты (как на календаре)

    class Meta:
        model = Order    # модель с которой необходимо работать
        fields = (    # поля которые необходимо отрендерить в шаблоне
            "first_name", "last_name", "phone",
            "address", "buying_type", "order_date", "comment"
        )


class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)    # для скрытия пароля при вводе (звездочки)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    # переопределение класса из родительского класса
        self.fields["username"].label = "Логин"
        self.fields["password"].label = "Пароль"

    def clean(self):    # проверка логина и пароля
        username = self.cleaned_data["username"]    # cleaned_data - данные их заполненной формы
        password = self.cleaned_data["password"]    # cleaned_data - данные их заполненной формы
        if not User.objects.filter(username=username).exists():
            raise forms.ValidationError(f"Пользователь с именем {username} не найден")

        user = User.objects.filter(username=username).first()
        if user:
            if not user.check_password(password):
                raise forms.ValidationError(f"Неверный пароль")
        return self.cleaned_data

    class Meta:
        model = User
        fields = (
            "username",
            "password"
        )


class RegistrationForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)    # подтверждение что пользователь ввел правильный пароль
    password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(required=False)    # required=False - не одязательное поле
    address = forms.CharField(required=False)
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.fields["password"].label = "Пароль"
        self.fields["confirm_password"].label = "Подтвердите пароль"
        self.fields["email"].label = "Электронная почта"
        self.fields["first_name"].label = "Ваше имя"
        self.fields["last_name"].label = "Ваша фамилия"
        self.fields["phone"].label = "Номер телефона"
        self.fields["address"].label = "Адрес"

    def clean_email(self):    # валидируем email (проверки)
        email = self.cleaned_data["email"]
        domain = email.split(".")[-1]
        if domain in ("ru", "org"):
            raise forms.ValidationError(f"Регистрация для домена {domain} невозможна")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Данный почтовый адрес уже зарегистрирован")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(f"Логин {username} уже существует")
        return username

    def clean(self):    # проверка правильного повторного ввода пароля
        password = self.cleaned_data["password"]
        confirm_password = self.cleaned_data["confirm_password"]
        if password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают")
        return self.cleaned_data

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "confirm_password",
            "email",
            "first_name",
            "last_name",
            "phone",
            "address",
        )
