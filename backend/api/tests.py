def test_hello_returns_message(client):
    response = client.get("/api/hello/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, world!"}
