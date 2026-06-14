import csv
import io
import json
import re
import uuid

from django.db import connection, transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Item


def hello(_request):
    return JsonResponse({"message": "Hello, world!"})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def items(request):
    if request.method == "GET":
        return list_items(request)
    return register_item(request)


def list_items(_request):
    """登録済みCSVの一覧を取得して返します。"""
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


def register_item(request):
    """CSV名とテキストを受け取り、検証のうえDBへ登録します。"""
    # 1. 基本入力値とCSV内容のバリデーション (例外ベースでまとめて処理)
    try:
        name, csv_text = parse_and_validate_request(request)
        header, data_rows = parse_and_validate_csv(csv_text)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    # 2. トランザクション内でのデータベース保存
    table_name = f"csv_data_{uuid.uuid4().hex}"
    try:
        with transaction.atomic():
            # メタデータ登録
            item = Item.objects.create(
                name=name, table_name=table_name, created_at=timezone.now()
            )
            # 実データテーブル作成 & データ投入
            create_table_and_insert_data(table_name, header, data_rows)
    except Exception as e:
        return JsonResponse(
            {"error": f"データベースへの保存中にエラーが発生しました: {e}"}, status=400
        )

    return JsonResponse(
        {
            "id": item.id,
            "name": item.name,
            "tableName": item.table_name,
            "createdAt": item.created_at.isoformat().replace("+00:00", "Z"),
        },
        status=201,
    )


def parse_and_validate_request(request):
    """リクエストデータをパースし、CSV名とCSVテキストの基本バリデーションを行います。"""
    try:
        body = json.loads(request.body)
        name = body.get("name", "").strip()
        csv_text = body.get("csvText", "").strip()
    except (json.JSONDecodeError, AttributeError):
        raise ValueError("不正なリクエストデータです")

    if not name:
        raise ValueError("CSV名を入力してください")
    if not csv_text:
        raise ValueError("CSVテキストが空です")

    if Item.objects.filter(name=name).exists():
        raise ValueError("同名のCSVが既に存在します")

    return name, csv_text


def parse_and_validate_csv(csv_text):
    """CSVテキストをパースし、検証ルールに沿ってチェックした上でヘッダーとデータ行を返します。"""
    try:
        reader = csv.reader(io.StringIO(csv_text))
        rows = [r for r in reader]
    except csv.Error:
        raise ValueError("CSVの解析に失敗しました")

    if not rows or not rows[0]:
        raise ValueError("有効なCSVを入力してください")

    header, data_rows = rows[0], rows[1:]

    # 制限値チェック
    if len(header) > 20:
        raise ValueError("列数は最大20までです")
    if len(data_rows) > 1000:
        raise ValueError("行数は最大1000行までです")
    if len(header) != len(set(header)):
        raise ValueError("列名に重複があります")

    # 列名書式チェック
    for col in header:
        if not col.strip() or not re.match(r"^[a-zA-Z0-9_]+$", col.strip()):
            raise ValueError("列名は英数字とアンダースコアのみ使用できます")

    # 各行の列数チェック
    for i, row in enumerate(data_rows):
        if len(row) != len(header):
            raise ValueError(f"{i + 2}行目の列数がヘッダーと一致しません")

    return header, data_rows


def create_table_and_insert_data(table_name, header, data_rows):
    """実データテーブルを作成し、データを一括投入します。
    すべての列は TEXT 型で作成されます。
    """
    quoted_schema = connection.ops.quote_name("csv_data")
    quoted_table = connection.ops.quote_name(table_name)

    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS csv_data")

        # すべての列を TEXT 型でテーブル作成
        col_defs = [f"{connection.ops.quote_name(h)} TEXT" for h in header]
        cursor.execute(
            f"CREATE TABLE {quoted_schema}.{quoted_table} "
            f"(_id SERIAL PRIMARY KEY, {', '.join(col_defs)})"
        )

        # データ投入 (キャスト型変換なしでそのまま挿入)
        if data_rows:
            cols = [connection.ops.quote_name(h) for h in header]
            placeholders = ["%s"] * len(header)
            insert_sql = (
                f"INSERT INTO {quoted_schema}.{quoted_table} "
                f"({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
            )
            insert_data = [[v.strip() for v in row] for row in data_rows]
            cursor.executemany(insert_sql, insert_data)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def item_detail(request, item_id):
    if request.method == "GET":
        return get_item_detail(request, item_id)
    return delete_item(request, item_id)


def get_item_detail(_request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if not re.match(r"^[a-zA-Z0-9_]+$", item.table_name):
        raise Http404("Invalid table name")

    quoted_schema = connection.ops.quote_name("csv_data")
    quoted_table = connection.ops.quote_name(item.table_name)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {quoted_schema}.{quoted_table} ORDER BY _id")
        desc = cursor.description or []
        all_headers = [col[0] for col in desc]
        id_index = all_headers.index("_id") if "_id" in all_headers else -1

        headers = [h for h in all_headers if h != "_id"]
        rows = []
        for row in cursor.fetchall():
            row_list = list(row)
            if id_index != -1:
                row_list.pop(id_index)
            rows.append(row_list)

    return JsonResponse(
        {
            "id": item.id,
            "name": item.name,
            "headers": headers,
            "rows": rows,
        }
    )


def delete_item(_request, item_id):
    with transaction.atomic():
        item = get_object_or_404(Item.objects.select_for_update(), id=item_id)

        if not re.match(r"^[a-zA-Z0-9_]+$", item.table_name):
            raise Http404("Invalid table name")

        with connection.cursor() as cursor:
            quoted_schema = connection.ops.quote_name("csv_data")
            quoted_table_name = connection.ops.quote_name(item.table_name)
            cursor.execute(f"DROP TABLE IF EXISTS {quoted_schema}.{quoted_table_name}")

        item.delete()

    return HttpResponse(status=204)


@csrf_exempt
@require_http_methods(["GET"])
def aggregate_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    group_by = request.GET.get("group_by", "").strip()
    aggregate_by = request.GET.get("aggregate_by", "").strip()
    function = request.GET.get("function", "").strip().upper()

    if not aggregate_by or not function:
        return JsonResponse({"error": "必要なパラメータが不足しています"}, status=400)

    try:
        validate_aggregate_params(group_by, aggregate_by, function, item.table_name)
        results = execute_aggregation_query(
            item.table_name, group_by, aggregate_by, function
        )
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse(
            {"error": f"集計処理中にエラーが発生しました: {e}"}, status=400
        )

    rows = format_aggregate_results(results, has_group_by=bool(group_by))
    if group_by:
        headers = [group_by, f"{aggregate_by}({function})"]
    else:
        headers = [f"{aggregate_by}({function})"]

    return JsonResponse({"headers": headers, "rows": rows})


def validate_aggregate_params(group_by, aggregate_by, function, table_name):
    """集計パラメータの妥当性を検証します。不正な場合は ValueError を発生させます。"""
    # 1. 集計関数の検証
    allowed_functions = ["SUM", "AVG", "COUNT", "MAX", "MIN"]
    if function not in allowed_functions:
        raise ValueError(f"サポートされていない集計関数です: {function}")

    # 2. テーブル名の形式検証 (SQLインジェクション対策)
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        raise ValueError("Invalid table name")

    # 3. カラムの存在検証
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'csv_data' AND table_name = %s",
            [table_name],
        )
        existing_cols = {row[0] for row in cursor.fetchall()}

    if group_by and group_by not in existing_cols:
        raise ValueError(f"グループ化対象の列名が存在しません: {group_by}")
    if aggregate_by not in existing_cols:
        raise ValueError(f"集計対象の列名が存在しません: {aggregate_by}")


def execute_aggregation_query(table_name, group_by, aggregate_by, function):
    """データベースで集計クエリを実行し、結果を返します。"""
    quoted_schema = connection.ops.quote_name("csv_data")
    quoted_table = connection.ops.quote_name(table_name)
    quoted_agg_col = connection.ops.quote_name(aggregate_by)

    # SUM, AVG は数値キャストする
    if function in ["SUM", "AVG"]:
        agg_expr = f"{function}(CAST({quoted_agg_col} AS NUMERIC))"
    else:
        agg_expr = f"{function}({quoted_agg_col})"

    if group_by:
        quoted_group_col = connection.ops.quote_name(group_by)
        sql = (
            f"SELECT {quoted_group_col}, {agg_expr} "
            f"FROM {quoted_schema}.{quoted_table} "
            f"GROUP BY {quoted_group_col} "
            f"ORDER BY {quoted_group_col}"
        )
    else:
        sql = f"SELECT {agg_expr} FROM {quoted_schema}.{quoted_table}"

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        error_msg = str(e)
        if (
            "invalid input syntax for type numeric" in error_msg
            or "cannot be cast to type numeric" in error_msg
        ):
            raise ValueError("集計列に数値に変換できない値が含まれています")
        raise e


def format_aggregate_results(results, has_group_by=True):
    """データベースの集計結果をJSON用の行リストに整形します。"""
    rows = []
    for row in results:
        if has_group_by:
            g_val = row[0]
            agg_val = row[1]
        else:
            g_val = None
            agg_val = row[0]

        if agg_val is None:
            agg_val = ""
        elif isinstance(agg_val, float):
            if agg_val.is_integer():
                agg_val = str(int(agg_val))
            else:
                agg_val = f"{agg_val:.4f}".rstrip("0").rstrip(".")
        else:
            agg_val = str(agg_val)

        if has_group_by:
            rows.append([str(g_val) if g_val is not None else "", agg_val])
        else:
            rows.append([agg_val])
    return rows
