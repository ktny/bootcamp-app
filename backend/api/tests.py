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
