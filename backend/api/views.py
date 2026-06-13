from django.http import JsonResponse

from .models import Item


def hello(_request):
    return JsonResponse({"message": "Hello, world!"})


def items(_request):
    item_list = [
        {
            "id": item.id,
            "name": item.name,
            "tableName": item.table_name,
            "createdAt": item.created_at.isoformat().replace("+00:00", "Z"),
        }
        for item in Item.objects.all()
    ]

    return JsonResponse({"items": item_list})
