import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, AuthenticatedUser

client = TestClient(app)

@pytest.fixture
def mock_auth_user():
    return AuthenticatedUser(
        id="c39f0f9b-6415-4c01-b75a-0d123456789a",
        email="athlete.profile@nutriwell.com",
        role="authenticated",
        user_metadata={"name": "Alex Profile"}
    )

def test_get_user_profile_unauthorized():
    res = client.get("/users/me")
    assert res.status_code == 401

def test_get_user_profile_authenticated(mock_auth_user):
    app.dependency_overrides[get_current_user] = lambda: mock_auth_user
    try:
        res = client.get("/users/me")
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] == mock_auth_user.id
        assert data["email"] == mock_auth_user.email
        assert "daily_calorie_target" in data
        assert "bmi" in data
        assert "bmr" in data
        assert "tdee" in data
    finally:
        app.dependency_overrides.clear()

def test_update_user_profile_authenticated(mock_auth_user):
    app.dependency_overrides[get_current_user] = lambda: mock_auth_user
    try:
        payload = {
            "name": "Alex Hunter Pro",
            "age": 28,
            "gender": "Male",
            "height": 180.0,
            "weight": 75.0,
            "activity_level": "Moderately Active",
            "dietary_preference": "Non-Veg",
            "food_preferences": ["Grilled Chicken", "Oatmeal", "Brown Rice"],
            "allergies": ["Peanuts"],
            "medical_or_dietary_restrictions": ["Low Lactose"],
            "nutrition_goal": "muscle_gain"
        }
        res = client.put("/users/me", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "Alex Hunter Pro"
        assert data["age"] == 28
        assert data["gender"] == "Male"
        assert data["height"] == 180.0
        assert data["weight"] == 75.0
        assert data["nutrition_goal"] == "muscle_gain"
        assert "Peanuts" in data["allergies"]
        # BMI for 75kg, 180cm: 75 / (1.8^2) = 23.15
        assert data["bmi"] == 23.15
        assert data["bmi_category"] == "Normal weight"
        # BMR Male: 10*75 + 6.25*180 - 5*28 + 5 = 750 + 1125 - 140 + 5 = 1740.0
        assert data["bmr"] == 1740.0
        # TDEE Moderately Active: 1740 * 1.55 = 2697.0
        assert data["tdee"] == 2697.0
        # Muscle Gain Calorie Target: 2697 + 250 = 2947.0
        assert data["daily_calorie_target"] == 2947.0
        # Protein for Muscle Gain (2g / kg): 75 * 2.0 = 150.0g
        assert data["daily_protein_target"] == 150.0
    finally:
        app.dependency_overrides.clear()

def test_update_user_profile_validation_error(mock_auth_user):
    app.dependency_overrides[get_current_user] = lambda: mock_auth_user
    try:
        # Invalid age > 120
        res = client.put("/users/me", json={"age": 150})
        assert res.status_code == 422

        # Invalid negative height
        res = client.put("/users/me", json={"height": -10})
        assert res.status_code == 422
    finally:
        app.dependency_overrides.clear()
