import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, AuthenticatedUser

client = TestClient(app)

def test_protected_routes_unauthorized_without_token():
    # Attempting to access protected endpoints without token must return 401
    endpoints = [
        "/auth/me",
        "/users/me",
        "/nutrition/profile",
        "/nutrition/goals",
        "/meals",
        "/meal-plans",
        "/nutrition/daily",
        "/progress"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 401
        assert "detail" in res.json() or "message" in res.json()

def test_invalid_bearer_token():
    headers = {"Authorization": "Bearer invalid.mock.token"}
    res = client.get("/auth/me", headers=headers)
    assert res.status_code == 401

def test_authenticated_user_dependency_override():
    # Mock authenticated user to test protected endpoints behavior
    mock_user = AuthenticatedUser(
        id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        email="testuser@nutriwell.com",
        role="authenticated",
        user_metadata={"name": "Test Nutri User"}
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        res = client.get("/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        assert data["email"] == "testuser@nutriwell.com"
        assert data["name"] == "Test Nutri User"
    finally:
        app.dependency_overrides.clear()
