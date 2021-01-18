from django.contrib import admin

from .models import *


admin.site.register(Category)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Product)


# admin.site.register(Order)    # регистрация модели так или как ниже
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    fields = (
        "customer", "first_name", "last_name",
        "phone", "cart", "address", "status",
        "buying_type", "comment", "order_date"
    )
