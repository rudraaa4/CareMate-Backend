def test_health_check_returns_up(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "UP",
        "service": "CareMate API",
        "database": "UP",
    }
