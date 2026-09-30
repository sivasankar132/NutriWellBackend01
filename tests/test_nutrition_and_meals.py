import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, AuthenticatedUser
from app.services.nutrition_service import nutrition_service

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

def test_nutrition_profile_calculation(authenticated_client):
    res = authenticated_client.get("/nutrition/profile")
    assert res.status_code == 200
    data = res.json()
    assert "bmi" in data
    assert "bmr" in data
    assert "tdee" in data
    assert "daily_calorie_target" in data
    assert data["daily_calorie_target"] > 0

def test_daily_nutrition_calculation(authenticated_client):
    res = authenticated_client.get("/nutrition/daily")
    assert res.status_code == 200
    data = res.json()
    assert "calories_consumed" in data
    assert "calorie_target" in data
    assert "protein_target" in data

def test_progress_summary(authenticated_client):
    res = authenticated_client.get("/progress/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_logs" in data
    assert "records" in data

def test_profile_upsert_does_not_write_goal_to_profile_table(monkeypatch):
    captured_profile_payload = None

    class FakeQuery:
        def __init__(self, operation="select"):
            self.operation = operation
            self.payload = None
            self.user_id = None

        def select(self, *_columns):
            return self

        def eq(self, column, value):
            if column == "user_id":
                self.user_id = value
            return self

        def order(self, *_columns, **_kwargs):
            return self

        def limit(self, *_count):
            return self

        def insert(self, payload):
            nonlocal captured_profile_payload
            if "age" in payload:
                captured_profile_payload = payload
            self.operation = "insert"
            return self

        def execute(self):
            if self.operation == "insert":
                return type("Result", (), {"data": [{"id": "profile-1", **(captured_profile_payload or {})}]})()
            return type("Result", (), {"data": []})()

    class FakeSupabase:
        def table(self, table_name):
            assert table_name in {"nutrition_profiles", "nutrition_goals"}
            return FakeQuery()

    monkeypatch.setattr(nutrition_service, "supabase", FakeSupabase())
    from app.schemas.profile import UserProfileUpdateRequest

    nutrition_service.upsert_profile(
        "user-1",
        UserProfileUpdateRequest(age=30, height=175, weight=70, nutrition_goal="weight_loss"),
    )

    assert captured_profile_payload["user_id"] == "user-1"
    assert "nutrition_goal" not in captured_profile_payload
