from django import forms


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
