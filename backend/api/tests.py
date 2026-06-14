import datetime

from django.db import connection
from django.utils import timezone

from api.models import Item


def test_hello_returns_message(client):
    response = client.get("/api/hello/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, world!"}


def test_items_returns_seed_items(client, db):
    # 初期状態は空であることを確認
    response = client.get("/api/items/")
    assert response.status_code == 200
    assert response.json() == {"items": []}

    # アイテムを登録して一覧に表示されることを確認
    item = Item.objects.create(
        name="サンプルCSV",
        table_name="sample_csv",
        created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    )
    response = client.get("/api/items/")
    assert response.json() == {
        "items": [
            {
                "id": item.id,
                "name": "サンプルCSV",
                "tableName": "sample_csv",
                "createdAt": "2026-01-01T00:00:00Z",
            }
        ]
    }


def test_delete_item_success(client, db):
    # 1. テストデータの準備
    # メタデータレコードを作成 (自動採番を使用)
    item = Item.objects.create(
        name="テストCSV",
        table_name="test_csv_table",
        created_at=timezone.now(),
    )

    # テスト用のダミーテーブルを作成 (専用スキーマ csv_data 内)
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")
        cursor.execute(
            "CREATE TABLE csv_data.test_csv_table ("
            "_id SERIAL PRIMARY KEY, name VARCHAR(50))"
        )
        cursor.execute("INSERT INTO csv_data.test_csv_table (name) VALUES ('test')")

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
            "WHERE table_schema = %s AND table_name = %s)",
            ["csv_data", item.table_name],
        )
        exists = cursor.fetchone()[0]
        assert not exists


def test_delete_item_not_found(client, db):
    # 存在しないIDに対して DELETE を実行
    response = client.delete("/api/items/9999/")
    assert response.status_code == 404


def test_create_item_success(client, db):
    csv_text = "name,age,city\nAlice,30,Tokyo\nBob,,Osaka\nCharlie,25,Kyoto"
    data = {"name": "新規CSV", "csvText": csv_text}
    response = client.post("/api/items/", data=data, content_type="application/json")

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == "新規CSV"
    assert "tableName" in res_data
    assert "createdAt" in res_data

    # メタデータ存在確認
    item = Item.objects.get(id=res_data["id"])
    assert item.name == "新規CSV"
    assert item.table_name == res_data["tableName"]

    # 実データテーブル存在確認とデータ検証
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = %s)",
            ["csv_data", item.table_name],
        )
        assert cursor.fetchone()[0]

        # カラム検証
        cursor.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
            ["csv_data", item.table_name],
        )
        columns = cursor.fetchall()
        col_dict = {col[0]: col[1] for col in columns}
        assert "_id" in col_dict
        assert col_dict["name"] in ["text", "character varying"]
        assert col_dict["age"] in ["text", "character varying"]
        assert col_dict["city"] in ["text", "character varying"]

        # レコード検証
        cursor.execute(
            f'SELECT name, age, city FROM csv_data."{item.table_name}" ORDER BY _id'
        )
        rows = cursor.fetchall()
        assert len(rows) == 3
        assert rows[0] == ("Alice", "30", "Tokyo")
        assert rows[1] == ("Bob", "", "Osaka")
        assert rows[2] == ("Charlie", "25", "Kyoto")


def test_create_item_duplicate_name(client, db):
    # 事前にサンプルCSVを登録しておく
    Item.objects.create(
        name="サンプルCSV",
        table_name="sample_csv",
        created_at=timezone.now(),
    )
    # すでに登録済みのデータ名「サンプルCSV」で登録を試みる
    data = {"name": "サンプルCSV", "csvText": "id,val\n1,abc"}
    response = client.post("/api/items/", data=data, content_type="application/json")

    assert response.status_code == 400
    assert "既に存在します" in response.json()["error"]


def test_create_item_empty_csv(client, db):
    data = {"name": "空のCSV", "csvText": ""}
    response = client.post("/api/items/", data=data, content_type="application/json")

    assert response.status_code == 400
    assert "空" in response.json()["error"]


def test_create_item_invalid_column_name(client, db):
    data = {"name": "列名不正", "csvText": "id,val-name\n1,abc"}
    response = client.post("/api/items/", data=data, content_type="application/json")

    assert response.status_code == 400
    assert "列名" in response.json()["error"]


def test_create_item_duplicate_column_name(client, db):
    data = {"name": "列名重複", "csvText": "id,val,val\n1,abc,def"}
    response = client.post("/api/items/", data=data, content_type="application/json")

    assert response.status_code == 400
    assert "重複" in response.json()["error"]


def test_create_item_too_many_columns(client, db):
    headers = ",".join([f"col_{i}" for i in range(21)])
    data = {"name": "列数過多", "csvText": f"{headers}\n" + ",".join(["1"] * 21)}
    response = client.post("/api/items/", data=data, content_type="application/json")

    assert response.status_code == 400
    assert "最大" in response.json()["error"]


def test_create_item_too_many_rows(client, db):
    rows = ["id,val"] + [f"{i},abc" for i in range(1001)]
    csv_text = "\n".join(rows)
    data = {"name": "行数過多", "csvText": csv_text}
    response = client.post("/api/items/", data=data, content_type="application/json")

    assert response.status_code == 400
    assert "最大" in response.json()["error"]


def test_get_item_detail_success(client, db):
    # 1. テストデータの準備
    item = Item.objects.create(
        name="テストCSV",
        table_name="test_csv_table_detail",
        created_at=timezone.now(),
    )

    # テスト用の実データテーブルを作成 (専用スキーマ csv_data 内)
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")
        cursor.execute(
            "CREATE TABLE csv_data.test_csv_table_detail ("
            "_id SERIAL PRIMARY KEY, name TEXT, age TEXT)"
        )
        cursor.execute(
            "INSERT INTO csv_data.test_csv_table_detail (name, age) VALUES "
            "('Alice', '30'), ('Bob', '25')"
        )

    # 2. 詳細取得 API を実行
    response = client.get(f"/api/items/{item.id}/")

    # 3. アサーション
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["id"] == item.id
    assert res_data["name"] == "テストCSV"
    assert res_data["headers"] == ["name", "age"]
    assert res_data["rows"] == [["Alice", "30"], ["Bob", "25"]]


def test_get_item_detail_not_found(client, db):
    # 存在しないIDに対して GET を実行
    response = client.get("/api/items/9999/")
    assert response.status_code == 404


def test_aggregate_item_success_count(client, db):
    item = Item.objects.create(
        name="集計テストCSV",
        table_name="test_csv_aggregate",
        created_at=timezone.now(),
    )

    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")
        cursor.execute(
            "CREATE TABLE csv_data.test_csv_aggregate ("
            "_id SERIAL PRIMARY KEY, category TEXT, score TEXT)"
        )
        cursor.execute(
            "INSERT INTO csv_data.test_csv_aggregate (category, score) VALUES "
            "('A', '100'), ('A', '200'), ('B', '150')"
        )

    # category ごとに score の COUNT を集計
    response = client.get(
        f"/api/items/{item.id}/aggregate/",
        {"group_by": "category", "aggregate_by": "score", "function": "COUNT"},
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["headers"] == ["category", "score(COUNT)"]
    assert res_data["rows"] == [["A", "2"], ["B", "1"]]


def test_aggregate_item_success_sum(client, db):
    item = Item.objects.create(
        name="集計テストCSV2",
        table_name="test_csv_aggregate2",
        created_at=timezone.now(),
    )

    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")
        cursor.execute(
            "CREATE TABLE csv_data.test_csv_aggregate2 ("
            "_id SERIAL PRIMARY KEY, category TEXT, score TEXT)"
        )
        cursor.execute(
            "INSERT INTO csv_data.test_csv_aggregate2 (category, score) VALUES "
            "('A', '100'), ('A', '200'), ('B', '150')"
        )

    # category ごとに score の SUM を集計
    response = client.get(
        f"/api/items/{item.id}/aggregate/",
        {"group_by": "category", "aggregate_by": "score", "function": "SUM"},
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["headers"] == ["category", "score(SUM)"]
    assert res_data["rows"] == [["A", "300"], ["B", "150"]]


def test_aggregate_item_invalid_numeric_cast(client, db):
    item = Item.objects.create(
        name="キャストエラーCSV",
        table_name="test_csv_aggregate_err",
        created_at=timezone.now(),
    )

    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")
        cursor.execute(
            "CREATE TABLE csv_data.test_csv_aggregate_err ("
            "_id SERIAL PRIMARY KEY, category TEXT, score TEXT)"
        )
        cursor.execute(
            "INSERT INTO csv_data.test_csv_aggregate_err (category, score) VALUES "
            "('A', 'not_number'), ('B', '150')"
        )

    # SUM を指定した際、数値キャストできない行が存在するためエラーになること
    response = client.get(
        f"/api/items/{item.id}/aggregate/",
        {"group_by": "category", "aggregate_by": "score", "function": "SUM"},
    )

    assert response.status_code == 400
    assert "数値" in response.json()["error"]


def test_aggregate_item_invalid_function(client, db):
    item = Item.objects.create(
        name="関数エラーCSV",
        table_name="test_csv_aggregate_func_err",
        created_at=timezone.now(),
    )

    # 許可されていない関数を指定した際、エラーになること
    response = client.get(
        f"/api/items/{item.id}/aggregate/",
        {"group_by": "category", "aggregate_by": "score", "function": "DROP"},
    )

    assert response.status_code == 400
    assert "集計関数" in response.json()["error"]


def test_aggregate_item_invalid_column(client, db):
    item = Item.objects.create(
        name="カラムエラーCSV",
        table_name="test_csv_aggregate_col_err",
        created_at=timezone.now(),
    )
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")
        cursor.execute(
            "CREATE TABLE csv_data.test_csv_aggregate_col_err ("
            "_id SERIAL PRIMARY KEY, category TEXT)"
        )

    # 存在しないカラムを指定した際、エラーになること
    response = client.get(
        f"/api/items/{item.id}/aggregate/",
        {"group_by": "category", "aggregate_by": "invalid_col", "function": "COUNT"},
    )

    assert response.status_code == 400
    assert "列名" in response.json()["error"]


def test_aggregate_item_success_no_group_by(client, db):
    item = Item.objects.create(
        name="全体集計テストCSV",
        table_name="test_csv_aggregate_no_group",
        created_at=timezone.now(),
    )

    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")
        cursor.execute(
            "CREATE TABLE csv_data.test_csv_aggregate_no_group ("
            "_id SERIAL PRIMARY KEY, score TEXT)"
        )
        cursor.execute(
            "INSERT INTO csv_data.test_csv_aggregate_no_group (score) VALUES "
            "('100'), ('200'), ('150')"
        )

    # グループ化なしで score の SUM を集計 (450)
    response = client.get(
        f"/api/items/{item.id}/aggregate/",
        {"aggregate_by": "score", "function": "SUM"},
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["headers"] == ["score(SUM)"]
    assert res_data["rows"] == [["450"]]
