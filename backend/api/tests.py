from django.db import connection
from django.utils import timezone

from api.models import Item


def test_hello_returns_message(client):
    response = client.get("/api/hello/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, world!"}


def test_items_returns_seed_items(client, db):
    response = client.get("/api/items/")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 1,
                "name": "サンプルCSV",
                "tableName": "sample_csv",
                "createdAt": "2026-01-01T00:00:00Z",
            }
        ]
    }


def test_delete_item_success(client, db):
    # 1. テストデータの準備
    # メタデータレコードを作成
    item = Item.objects.create(
        id=100,
        name="テストCSV",
        table_name="test_csv_table",
        created_at=timezone.now(),
    )

    # テスト用のダミーテーブルを作成
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE test_csv_table (id SERIAL PRIMARY KEY, name VARCHAR(50))"
        )
        cursor.execute("INSERT INTO test_csv_table (name) VALUES ('test')")

    # 2. 削除 API を実行
    response = client.delete(f"/api/items/{item.id}/")

    # 3. アサーション
    assert response.status_code == 204

    # メタデータが消えていることを確認
    assert not Item.objects.filter(id=item.id).exists()

    # 実データテーブルが消えていることを確認
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_name = %s)",
            [item.table_name],
        )
        exists = cursor.fetchone()[0]
        assert not exists


def test_delete_item_not_found(client, db):
    # 存在しないIDに対して DELETE を実行
    response = client.delete("/api/items/9999/")
    assert response.status_code == 404
