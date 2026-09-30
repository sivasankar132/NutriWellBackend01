import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, AuthenticatedUser
from app.services.food_service import food_service

client = TestClient(app)

@pytest.fixture
def authenticated_client():
    mock_user = AuthenticatedUser(
        id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        email="athlete@nutriwell.com",
        role="authenticated",
        user_metadata={"name": "Athlete User"}
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.clear()

def test_list_foods():
    res = client.get("/foods")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_search_foods_validation():
    res = client.get("/foods/search?q=")
    assert res.status_code == 422 # Min length validation

def test_create_food_accepts_numeric_serving_size(authenticated_client, monkeypatch):
    created_food = {
        "id": "custom-food-1",
        "name": "Test Oats",
        "calories": 389.0,
        "protein": 16.9,
        "carbs": 66.3,
        "fats": 6.9,
        "fiber": 10.6,
        "sugar": 0.0,
        "sodium": 2.0,
        "serving_size": 100.0,
        "serving_unit": "g",
        "category": "Carbs",
        "diet_type": "Vegan",
        "is_custom": True,
        "created_by": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "created_at": "2026-09-14T00:00:00Z",
    }
    monkeypatch.setattr(food_service, "create_food", lambda data, user_id: created_food)

    res = authenticated_client.post("/foods", json=created_food)

    assert res.status_code == 201
    assert res.json()["serving_size"] == 100.0

def test_meals_endpoints_with_auth(authenticated_client):
    res = authenticated_client.get("/meals")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_meal_plans_endpoints_with_auth(authenticated_client):
    res = authenticated_client.get("/meal-plans")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_progress_endpoints_with_auth(authenticated_client):
    res = authenticated_client.get("/progress")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
