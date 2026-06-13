from django.urls import path

from .views import hello, items

urlpatterns = [
    path("hello/", hello, name="hello"),
    path("items/", items, name="items"),
]
