import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, AuthenticatedUser
from app.utils.error_handlers import AIContractException

client = TestClient(app)

def mock_get_current_user():
    return AuthenticatedUser(
        id="test-user-id",
        email="testuser@example.com",
        user_metadata={"name": "Test User"}
    )

@pytest.fixture(autouse=True)
def override_auth_dependency():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_ai_chat_success():
    mock_gemini_json = '{"id": "ai-123", "sender": "ai", "text": "Hello! High protein meal recommendation: Moong Dal.", "timestamp": "10:00 AM", "recommendedMeal": null}'
    
    with patch("app.services.gemini_service.gemini_service._call_gemini_raw", return_value=mock_gemini_json):
        response = client.post("/ai/chat", json={"prompt": "What should I eat for breakfast?"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["text"] == "Hello! High protein meal recommendation: Moong Dal."
        assert data["data"]["sender"] == "ai"


def test_ai_chat_missing_api_key_unauthorized():
    with patch("app.services.gemini_service.gemini_service._get_api_key", side_effect=AIContractException(error_code="GEMINI_UNAUTHORIZED", message="AI generation failed. Please try again.", status_code=401)):
        response = client.post("/ai/chat", json={"prompt": "High protein options?"})
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "GEMINI_UNAUTHORIZED"
        assert data["message"] == "AI generation failed. Please try again."


def test_ai_chat_rate_limited():
    with patch("app.services.gemini_service.gemini_service._call_gemini_raw", side_effect=AIContractException(error_code="GEMINI_RATE_LIMITED", message="AI generation failed. Please try again.", status_code=429)):
        response = client.post("/ai/chat", json={"prompt": "Macro guidance?"})
        assert response.status_code == 429
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "GEMINI_RATE_LIMITED"
        assert data["message"] == "AI generation failed. Please try again."


def test_ai_chat_timeout():
    with patch("app.services.gemini_service.gemini_service._call_gemini_raw", side_effect=AIContractException(error_code="GEMINI_TIMEOUT", message="AI generation failed. Please try again.", status_code=504)):
        response = client.post("/ai/chat", json={"prompt": "Macro guidance?"})
        assert response.status_code == 504
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "GEMINI_TIMEOUT"
        assert data["message"] == "AI generation failed. Please try again."


def test_ai_chat_invalid_json():
    with patch("app.services.gemini_service.gemini_service._call_gemini_raw", return_value="INVALID NON-JSON TEXT"):
        response = client.post("/ai/chat", json={"prompt": "Tell me a recipe"})
        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "GEMINI_INVALID_JSON"
        assert data["message"] == "AI generation failed. Please try again."


def test_ai_scan_food_success():
    mock_scan_json = '''{
        "name": "Paneer Tikka",
        "serving": "1 plate",
        "dietType": "Veg",
        "calories": 320.0,
        "protein": 22.0,
        "carbs": 12.0,
        "fat": 18.0,
        "fiber": 3.0,
        "vitamins": ["Vitamin A"],
        "minerals": ["Calcium"],
        "costInr": 150.0,
        "confidenceScore": 95.0,
        "healthRating": "Excellent",
        "aiAdvice": "Great high protein option!"
    }'''
    with patch("app.services.gemini_service.gemini_service._call_gemini_raw", return_value=mock_scan_json):
        response = client.post("/ai/scan-food", json={"image_base64": "data:image/jpeg;base64,abc123fake"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Paneer Tikka"
        assert data["data"]["protein"] == 22.0
