import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_users():
    res = client.get("/users")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

def test_create_user_validation_error():
    # Calling create user without required fields should fail gracefully
    res = client.post("/users")
    assert res.status_code in (400, 422)
