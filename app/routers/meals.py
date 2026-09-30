from typing import List, Optional
from datetime import date as DateType
from fastapi import APIRouter, Depends, Query, status
from app.schemas.meal import (
    MealCreate,
    MealUpdate,
    MealResponse,
    MealItemCreate,
    MealItemUpdate,
    MealItemResponse
)
from app.services.meal_service import meal_service
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/meals", tags=["Meals & Nutrition Tracking"])

@router.get(
    "",
    response_model=List[MealResponse],
    summary="Get user meals",
    description="Retrieves logged meals with full nutritional breakdown for the authenticated user."
)
def get_meals(
    meal_date: Optional[DateType] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.get_meals(user_id=current_user.id, meal_date=meal_date)

@router.post(
    "",
    response_model=MealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new meal",
    description="Logs a meal (breakfast, lunch, dinner, snack) with items and auto-calculates macros."
)
def create_meal(
    data: MealCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.create_meal(user_id=current_user.id, data=data)

@router.get(
    "/{meal_id}",
    response_model=MealResponse,
    summary="Get meal details by ID"
)
def get_meal(
    meal_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.get_meal_by_id(user_id=current_user.id, meal_id=meal_id)

@router.put(
    "/{meal_id}",
    response_model=MealResponse,
    summary="Update meal info"
)
def update_meal(
    meal_id: str,
    data: MealUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.update_meal(user_id=current_user.id, meal_id=meal_id, data=data)

@router.delete(
    "/{meal_id}",
    summary="Delete a meal"
)
def delete_meal(
    meal_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.delete_meal(user_id=current_user.id, meal_id=meal_id)

# ----------------- MEAL ITEMS SUB-RESOURCES ----------------- #

@router.post(
    "/{meal_id}/items",
    response_model=MealItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to a meal"
)
def add_meal_item(
    meal_id: str,
    item: MealItemCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.add_meal_item(user_id=current_user.id, meal_id=meal_id, item=item)

@router.put(
    "/{meal_id}/items/{item_id}",
    response_model=MealItemResponse,
    summary="Update meal item quantity/nutrition"
)
def update_meal_item(
    meal_id: str,
    item_id: str,
    item: MealItemUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.update_meal_item(user_id=current_user.id, meal_id=meal_id, item_id=item_id, item=item)

@router.delete(
    "/{meal_id}/items/{item_id}",
    summary="Remove an item from a meal"
)
def delete_meal_item(
    meal_id: str,
    item_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return meal_service.delete_meal_item(user_id=current_user.id, meal_id=meal_id, item_id=item_id)
