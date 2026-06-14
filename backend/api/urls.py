from django.urls import path

from .views import delete_item, hello, items

urlpatterns = [
    path("hello/", hello, name="hello"),
    path("items/", items, name="items"),
    path("items/<int:item_id>/", delete_item, name="delete_item"),
]
