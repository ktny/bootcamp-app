import re

from django.db import connection, transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

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


@require_http_methods(["DELETE"])
def delete_item(_request, item_id):
    with transaction.atomic():
        # 行ロックを取得しつつオブジェクトを取得
        item = get_object_or_404(Item.objects.select_for_update(), id=item_id)

        # 安全性チェック（英数字とアンダースコアのみ許可）
        if not re.match(r"^[a-zA-Z0-9_]+$", item.table_name):
            raise Http404("Invalid table name")

        # 実データテーブルを安全に削除
        with connection.cursor() as cursor:
            quoted_table_name = connection.ops.quote_name(item.table_name)
            cursor.execute(f"DROP TABLE IF EXISTS {quoted_table_name}")

        # メタデータを削除
        item.delete()

    return HttpResponse(status=204)
