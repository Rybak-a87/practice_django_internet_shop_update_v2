from django.urls import path
from . import views

app_name = "specs"


urlpatterns = [
    path("", views.BaseSpecView.as_view(), name="base-spec"),
]