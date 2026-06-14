from django.urls import path

from .views import hello, item_detail, items

urlpatterns = [
    path("hello/", hello, name="hello"),
    path("items/", items, name="items"),
    path("items/<int:item_id>/", item_detail, name="item_detail"),
]
