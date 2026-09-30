from typing import Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

from app.core.security import get_current_user, AuthenticatedUser
from app.services.user_context_builder import user_context_builder
from app.services.gemini_service import gemini_service
from app.schemas.ai import (
    AISuccessResponse,
    AIChatResult,
    AIScanFoodResult,
    AIWhatShouldIEatResult,
    AIBadDayRecoveryResult,
    AIIfIEatThisResult
)

router = APIRouter(prefix="/ai", tags=["AI Endpoints"])

class AIChatRequest(BaseModel):
    prompt: str

class AIScanFoodRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    image_base64: str = Field(..., alias="image_base64")
    mime_type: str = Field(default="image/jpeg", alias="mime_type")

class AIWhatShouldIEatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    context_mode: str = Field(default="GENERAL", alias="context_mode")

class AIIfIEatThisRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    food_name: str = Field(..., alias="food_name")
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float
    cost_inr: float = Field(default=50.0, alias="cost_inr")


def is_nutrition_scoped_query(prompt: str) -> bool:
    text = prompt.lower().strip()
    
    # Mandatory out-of-scope keyword filters
    unrelated_triggers = [
        "python", "javascript", "code", "programming", "blockchain", "crypto",
        "elon musk", "capital of", "who is elon", "who is steve", "who is bill",
        "write an essay", "write code", "html", "css", "sql query", "president",
        "movie", "song", "actor", "actress", "football", "cricket match"
    ]
    for trigger in unrelated_triggers:
        if trigger in text:
            # Check if it's explicitly asking about nutrition within coding e.g. "python nutrition calculation"
            if not any(nk in text for nk in ["my nutrition", "my meal", "my calories", "my diet"]):
                return False

    nutrition_keywords = [
        "eat", "food", "meal", "recipe", "diet", "nutrition", "calorie", "calories",
        "protein", "carb", "carbs", "fat", "fats", "fiber", "water", "weight",
        "bmi", "bmr", "tdee", "macro", "macros", "vitamin", "mineral", "allergy",
        "allergies", "diabetes", "diabetic", "blood pressure", "hypertension",
        "cholesterol", "health", "vegetarian", "vegan", "eggetarian", "non-veg",
        "snack", "breakfast", "lunch", "dinner", "cook", "dish", "nutriwell",
        "gain", "loss", "maintenance", "muscle", "healthy", "guidance",
        "recommend", "suggestion", "intake", "log", "logged", "swap",
        "substitute", "chia", "oats", "curd", "paneer", "dal", "chicken",
        "egg", "fish", "rice", "roti", "fruit", "vegetable", "what should i",
        "if i eat", "bad day", "recovery", "hi", "hello", "hey", "help"
    ]

    return any(kw in text for kw in nutrition_keywords)


@router.post("/chat", response_model=AISuccessResponse[AIChatResult])
def ai_chat(
    data: AIChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    if not data.prompt or not data.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt text cannot be empty."
        )

    # Application-level scope guardrail check before Gemini call
    if not is_nutrition_scoped_query(data.prompt):
        now_str = datetime.now().strftime("%I:%M %p")
        return AISuccessResponse(
            data=AIChatResult(
                id=f"ai-{int(datetime.now().timestamp()*1000)}",
                sender="ai",
                text="I can help only with nutrition and your NutriWell nutrition data.",
                timestamp=now_str,
                recommendedMeal=None
            )
        )

    user_id = current_user.id
    user_name = (current_user.user_metadata or {}).get("name") or (current_user.email.split("@")[0] if current_user.email else "User")

    # Fetch complete UserContext (including health_conditions, allergies, profile, macros, meals, goals)
    full_user_context = user_context_builder.build_user_context(user_id=user_id, user_name=user_name)

    system_prompt = (
        "You are NutriWell Emerald AI, a clinical dietitian and personalized nutrition assistant. "
        "Strictly adhere to the user's health conditions, allergies, dietary preferences, and macro goals in all suggestions. "
        "Return ONLY a JSON object with schema:\n"
        "{\n"
        "  \"id\": \"string\",\n"
        "  \"sender\": \"ai\",\n"
        "  \"text\": \"string\",\n"
        "  \"timestamp\": \"string\",\n"
        "  \"recommendedMeal\": null | {\"name\": \"string\", \"calories\": 0, \"protein\": 0, \"carbs\": 0, \"fat\": 0, \"fiber\": 0, \"costInr\": 0}\n"
        "}"
    )

    now_str = datetime.now().strftime("%I:%M %p")
    prompt_with_ctx = f"[FULL USER CONTEXT]\n{full_user_context}\n\n[TIMESTAMP]\n{now_str}\n\n[USER PROMPT]\n{data.prompt.strip()}"

    result = gemini_service.generate_structured(
        prompt=prompt_with_ctx,
        schema=AIChatResult,
        system_instruction=system_prompt
    )

    return AISuccessResponse(data=result)


@router.post("/scan-food", response_model=AISuccessResponse[AIScanFoodResult])
def ai_scan_food(
    data: AIScanFoodRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    if not data.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image base64 content is required."
        )

    system_prompt = (
        "You are a clinical dietitian & vision AI. Analyze the food image in detail and return ONLY a JSON object:\n"
        "{\n"
        "  \"name\": \"string\",\n"
        "  \"serving\": \"string\",\n"
        "  \"dietType\": \"Veg\" | \"Non-Veg\" | \"Vegan\" | \"Eggetarian\",\n"
        "  \"calories\": 100,\n"
        "  \"protein\": 5.0,\n"
        "  \"carbs\": 20.0,\n"
        "  \"fat\": 3.0,\n"
        "  \"fiber\": 2.0,\n"
        "  \"vitamins\": [\"string\"],\n"
        "  \"minerals\": [\"string\"],\n"
        "  \"costInr\": 50,\n"
        "  \"confidenceScore\": 90,\n"
        "  \"healthRating\": \"Excellent\" | \"Good\" | \"Moderate\" | \"High Calorie\",\n"
        "  \"aiAdvice\": \"string\"\n"
        "}\n"
        "If the image does not contain recognizable food, set name to 'Unidentified Food', confidenceScore to 10, and explain in aiAdvice."
    )

    result = gemini_service.generate_structured(
        prompt="Analyze this food image in detail. Identify the exact food item and nutritional content.",
        schema=AIScanFoodResult,
        system_instruction=system_prompt,
        image_base64=data.image_base64,
        image_mime_type=data.mime_type
    )

    # Strict check: If Gemini could not identify food or returned zero macros with low confidence / generic name
    name_lower = (result.name or "").lower()
    is_unidentified = any(kw in name_lower for kw in ["unidentified", "unknown", "no food", "not food", "invalid"])
    is_zero_macros = (result.calories == 0 and result.protein == 0 and result.carbs == 0)
    
    if is_unidentified or (is_zero_macros and result.confidence_score < 50):
        raise AIContractException(
            error_code="UNIDENTIFIED_FOOD",
            message=result.ai_advice or "Unable to identify food item in image. Please upload a clear photo of food.",
            status_code=422
        )

    return AISuccessResponse(data=result)


@router.post("/what-should-i-eat", response_model=AISuccessResponse[AIWhatShouldIEatResult])
def ai_what_should_i_eat(
    data: AIWhatShouldIEatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id
    user_name = (current_user.user_metadata or {}).get("name") or "User"
    full_user_context = user_context_builder.build_user_context(user_id=user_id, user_name=user_name)

    system_prompt = (
        "You are NutriWell meal recommendation AI. Analyze the full user context including health conditions, allergies, dietary preferences, and macro targets. "
        "Return ONLY a JSON object with top 3 meal options strictly aligned with user context:\n"
        "{\n"
        "  \"options\": [\n"
        "    {\n"
        "      \"id\": \"opt-1\",\n"
        "      \"title\": \"string\",\n"
        "      \"category\": \"string\",\n"
        "      \"calories\": 0,\n"
        "      \"protein\": 0,\n"
        "      \"costInr\": 0,\n"
        "      \"prepTimeMinutes\": 0,\n"
        "      \"reasonWhy\": \"string\",\n"
        "      \"foodItem\": null\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    prompt = f"[FULL USER CONTEXT]\n{full_user_context}\n\n[CONTEXT MODE]\n{data.context_mode}\n\nProvide top 3 personalized high-protein meal options that respect all allergies, health conditions, and dietary preferences."

    result = gemini_service.generate_structured(
        prompt=prompt,
        schema=AIWhatShouldIEatResult,
        system_instruction=system_prompt
    )

    return AISuccessResponse(data=result)


@router.post("/bad-day-recovery", response_model=AISuccessResponse[AIBadDayRecoveryResult])
def ai_bad_day_recovery(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id
    user_name = (current_user.user_metadata or {}).get("name") or "User"
    full_user_context = user_context_builder.build_user_context(user_id=user_id, user_name=user_name)

    system_prompt = (
        "You are NutriWell bad day recovery coach. Provide an empathetic headline, advice, and recommended recovery meal considering health conditions and restrictions. "
        "Return ONLY a JSON object:\n"
        "{\n"
        "  \"empatheticHeadline\": \"string\",\n"
        "  \"adviceMessage\": \"string\",\n"
        "  \"suggestedEveningAction\": \"string\",\n"
        "  \"recommendedRecoveryMeal\": null\n"
        "}"
    )

    prompt = f"[FULL USER CONTEXT]\n{full_user_context}\n\nGenerate empathetic evening recovery plan based on today's intake and user health context."

    result = gemini_service.generate_structured(
        prompt=prompt,
        schema=AIBadDayRecoveryResult,
        system_instruction=system_prompt
    )

    return AISuccessResponse(data=result)


@router.post("/if-i-eat-this", response_model=AISuccessResponse[AIIfIEatThisResult])
def ai_if_i_eat_this(
    data: AIIfIEatThisRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    user_id = current_user.id
    user_name = (current_user.user_metadata or {}).get("name") or "User"
    full_user_context = user_context_builder.build_user_context(user_id=user_id, user_name=user_name)

    system_prompt = (
        "You are NutriWell impact simulation AI. Return ONLY a JSON object:\n"
        "{\n"
        "  \"foodName\": \"string\",\n"
        "  \"calories\": 0,\n"
        "  \"protein\": 0,\n"
        "  \"carbs\": 0,\n"
        "  \"fat\": 0,\n"
        "  \"fiber\": 0,\n"
        "  \"costInr\": 0,\n"
        "  \"projectedCaloriePct\": 0,\n"
        "  \"projectedProteinPct\": 0,\n"
        "  \"betterSwap\": null,\n"
        "  \"aiAdvice\": \"string\"\n"
        "}"
    )

    prompt = (
        f"[FULL USER CONTEXT]\n{full_user_context}\n\n"
        f"[SIMULATED MEAL]\nFood: {data.food_name} ({data.calories} kcal, {data.protein}g protein, {data.carbs}g carbs, {data.fat}g fat, {data.fiber}g fiber, ₹{data.cost_inr})\n\n"
        f"Simulate impact of eating this meal, calculate projected percentages against user targets, and suggest a better swap if relevant considering health conditions/allergies."
    )

    result = gemini_service.generate_structured(
        prompt=prompt,
        schema=AIIfIEatThisResult,
        system_instruction=system_prompt
    )

    return AISuccessResponse(data=result)
