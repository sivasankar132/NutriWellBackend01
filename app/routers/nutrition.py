from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.schemas.nutrition import NutritionGoalCreate, NutritionGoalUpdate, NutritionGoalResponse
from app.services.nutrition_service import nutrition_service
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/nutrition", tags=["Nutrition Profile & Goals"])

# ----------------- NUTRITION PROFILES ----------------- #

@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get user nutrition profile",
    description="Returns current profile along with computed BMI, BMR, TDEE, and daily macro targets."
)
def get_nutrition_profile(current_user: AuthenticatedUser = Depends(get_current_user)):
    return nutrition_service.get_or_calculate_profile(current_user.id)

@router.post(
    "/profile",
    response_model=ProfileResponse,
    summary="Create or update nutrition profile",
    description="Saves user age, height, weight, activity level, dietary preference, and auto-calculates targets."
)
def create_or_update_profile(
    data: ProfileCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return nutrition_service.upsert_profile(current_user.id, data)

@router.put(
    "/profile",
    response_model=ProfileResponse,
    summary="Update nutrition profile",
    description="Updates existing profile fields and recalculates targets."
)
def update_profile(
    data: ProfileCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return nutrition_service.upsert_profile(current_user.id, data)

# ----------------- NUTRITION GOALS ----------------- #

@router.get(
    "/goals",
    response_model=List[NutritionGoalResponse],
    summary="Get user nutrition goals",
    description="Returns list of nutrition goals defined by the authenticated user."
)
def get_nutrition_goals(current_user: AuthenticatedUser = Depends(get_current_user)):
    return nutrition_service.get_goals(current_user.id)

@router.post(
    "/goals",
    response_model=NutritionGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set a nutrition goal",
    description="Sets a new health goal (weight_loss, muscle_gain, maintenance, healthy_eating)."
)
def create_nutrition_goal(
    data: NutritionGoalCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return nutrition_service.create_goal(current_user.id, data)

@router.put(
    "/goals/{goal_id}",
    response_model=NutritionGoalResponse,
    summary="Update a nutrition goal",
    description="Modifies targets or parameters for a specific goal."
)
def update_nutrition_goal(
    goal_id: str,
    data: NutritionGoalUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return nutrition_service.update_goal(current_user.id, goal_id, data)
