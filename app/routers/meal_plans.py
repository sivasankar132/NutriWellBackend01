from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.meal_plan import MealPlanCreate, MealPlanUpdate, MealPlanResponse
from app.services.meal_plan_service import meal_plan_service
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/meal-plans", tags=["Meal Plans"])

@router.get(
    "",
    response_model=List[MealPlanResponse],
    summary="Get user meal plans",
    description="Lists all scheduled meal plans and multi-day meal structures for the user."
)
def get_meal_plans(current_user: AuthenticatedUser = Depends(get_current_user)):
    return meal_plan_service.get_meal_plans(user_id=current_user.id)

@router.post(
    "",
    response_model=MealPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a meal plan"
)
def create_meal_plan(
    data: MealPlanCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_plan_service.create_meal_plan(user_id=current_user.id, data=data)

@router.get(
    "/{plan_id}",
    response_model=MealPlanResponse,
    summary="Get meal plan by ID"
)
def get_meal_plan(
    plan_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_plan_service.get_meal_plan_by_id(user_id=current_user.id, plan_id=plan_id)

@router.put(
    "/{plan_id}",
    response_model=MealPlanResponse,
    summary="Update a meal plan"
)
def update_meal_plan(
    plan_id: str,
    data: MealPlanUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_plan_service.update_meal_plan(user_id=current_user.id, plan_id=plan_id, data=data)

@router.delete(
    "/{plan_id}",
    summary="Delete a meal plan"
)
def delete_meal_plan(
    plan_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_plan_service.delete_meal_plan(user_id=current_user.id, plan_id=plan_id)
