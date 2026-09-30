from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.food import FoodCreate, FoodUpdate, FoodResponse
from app.services.food_service import food_service
from app.core.security import get_optional_user, get_current_user, AuthenticatedUser

router = APIRouter(prefix="/foods", tags=["Food Database"])

@router.get(
    "",
    response_model=List[FoodResponse],
    summary="List and search foods",
    description="Returns public food catalog with optional search and category filters."
)
def list_foods(
    search: Optional[str] = Query(None, description="Search keyword for food name"),
    category: Optional[str] = Query(None, description="Category filter (Protein, Carbs, Vegetables, etc.)"),
    diet_type: Optional[str] = Query(None, description="Diet filter (Veg, Non-Veg, Vegan, Eggetarian)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return food_service.get_foods(
        category=category,
        diet_type=diet_type,
        search=search,
        limit=limit,
        offset=offset
    )

@router.get(
    "/search",
    response_model=List[FoodResponse],
    summary="Search foods by query",
    description="Convenience endpoint to query foods by keyword."
)
def search_foods(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=50)
):
    return food_service.get_foods(search=q, limit=limit)

@router.get(
    "/{food_id}",
    response_model=FoodResponse,
    summary="Get food details by ID"
)
def get_food(food_id: str):
    return food_service.get_food_by_id(food_id)

@router.post(
    "",
    response_model=FoodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom food item",
    description="Authenticated user can add a custom food item with nutritional values."
)
def create_food(
    data: FoodCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return food_service.create_food(data, user_id=current_user.id)

@router.put(
    "/{food_id}",
    response_model=FoodResponse,
    summary="Update custom food item"
)
def update_food(
    food_id: str,
    data: FoodUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return food_service.update_food(food_id, data, user_id=current_user.id)

@router.delete(
    "/{food_id}",
    summary="Delete custom food item"
)
def delete_food(
    food_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return food_service.delete_food(food_id, user_id=current_user.id)
