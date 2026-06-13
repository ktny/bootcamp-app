# ミニ CSV 集計サービス

研修用に、CSV テキストを登録して一覧表示・削除・詳細表示・集計を行う小さな Web アプリケーションです。

バックエンド、フロントエンド、DB、Docker 構成を段階的に作り、各 step の完成状態をブランチとして残します。受講者が差分を追いながら、Web アプリケーション開発の基本的な流れを学べることを目的とします。

## 使用技術

- Docker Compose
- Python / Django
- TypeScript / Angular
- PostgreSQL

## 機能概要

### 一覧画面

- 登録済み CSV の一覧を表示する
- CSV 名と登録日時を表示する
- 各 CSV を削除できる
- 各 CSV の詳細画面へ遷移できる

### 登録画面

- CSV 名を入力する
- CSV 内容をテキストとして貼り付ける
- 登録時にメタデータと実データを DB に保存する
- 登録した CSV は DB 上の個別テーブルとして扱う

### 詳細画面

- 登録済み CSV の内容を表形式で表示する
- グループ化列、集計列、集計関数を指定して集計結果を表示する

## 想定データ構造

メタデータは `items` テーブルで管理します。

| column | description |
| --- | --- |
| `id` | 主キー |
| `name` | CSV 名。一意にする |
| `table_name` | 実データを保存するテーブル名 |
| `created_at` | 登録日時 |

CSV の実データは PostgreSQL 上の専用スキーマに、`table_name` ごとのテーブルとして作成します。

## 想定 API

| API | method | description |
| --- | --- | --- |
| 一覧取得 API | `GET` | 登録済み CSV の一覧を返す |
| データ登録 API | `POST` | CSV 名と CSV テキストを登録する |
| データ削除 API | `DELETE` | メタデータと実データを削除する |
| 詳細データ取得 API | `GET` | 指定 CSV の実データを返す |
| 集計 API | `GET` または `POST` | 指定列と集計関数に基づいて集計結果を返す |

具体的な URL、リクエスト形式、レスポンス形式は各 step の実装時に確定します。

## CSV 定義の制限

- 1 行目は必ずヘッダーとする
- 列名は英数字とアンダースコアのみ許可する
- 列数は最大 20
- 行数は最大 1000
- 空の CSV は登録不可
- 重複列名は登録不可
- 列の型は文字列と整数のみ扱う

## 注意すること

- CSV 登録時は必ずバリデーションを行う
- メタデータ登録と実データテーブル作成はトランザクションで扱う
- SQL インジェクションを防ぐため、テーブル名・列名・集計関数は許可リストまたは安全な識別子生成で扱う
- ユーザー入力をそのまま SQL 文字列へ埋め込まない
- 削除時はメタデータと実データの不整合が残らないようにする

## ブランチと step

各 step の完成状態をブランチとして残します。

| step | branch | goal |
| --- | --- | --- |
| step0 | `step0-docs` | README と AGENTS を作成し、研修全体の方針を決める |
| step1 | `step1-backend-base` | Django を Docker で構築し、Hello World API を返す |
| step2 | `step2-db-base` | PostgreSQL を Docker に追加し、Django から `items` 一覧 API を返す |
| step3 | `step3-frontend-base` | Angular を Docker に追加し、一覧画面から API を呼ぶ |
| step4 | `step4-delete` | 削除 API と削除ボタンを追加する |
| step5 | `step5-register` | 登録画面と登録 API を追加し、CSV を DB テーブルとして保存する |
| step6 | `step6-detail` | 詳細画面と詳細 API を追加し、CSV データを表形式で表示する |
| step7 | `step7-aggregate` | 集計 API と集計 UI を追加する |

## step 詳細

### step1: バックエンド基礎構築

- Django を Docker で起動できるようにする
- Django から Hello World API を返す
- API 疎通を確認する

### step2: DB 基礎構築

- PostgreSQL を Docker Compose に追加する
- Django から PostgreSQL に接続する
- `items` テーブルを作成する
- 仮データを投入する
- `items` 一覧を返す API を作成する

### step3: フロントエンド基礎構築

- Angular を Docker で起動できるようにする
- 一覧画面を作成する
- 画面表示時に一覧 API を呼び、レスポンスを一覧表示する

### step4: 削除機能

- 一覧画面の各 item に削除ボタンを追加する
- バックエンドに削除 API を追加する
- API 実行時に `items` レコードと実データテーブルを削除する
- 削除後に一覧表示を更新する

### step5: 登録機能

- ヘッダーに登録ボタンを追加する
- 登録画面を作成する
- CSV 名と CSV テキストを入力できるようにする
- バックエンドに登録 API を追加する
- CSV 名の重複を禁止する
- 衝突しない `table_name` を生成する
- CSV を検証し、実データテーブルを作成してデータを保存する

### step6: 詳細機能

- 一覧の item クリックで詳細画面へ遷移する
- バックエンドに詳細データ取得 API を追加する
- 指定 CSV の実データを JSON で返す
- フロントエンドで表形式に表示する

### step7: 集計機能

- 詳細画面に集計条件の入力 UI を追加する
- グループ化列、集計列、集計関数を指定できるようにする
- バックエンドに集計 API を追加する
- 集計結果を詳細画面に表示する

## 起動方法

step0 ではアプリケーション実装をまだ作成しません。

Docker Compose による起動方法は step1 以降で追記します。
