from typing import Optional
from datetime import date as DateType
from fastapi import APIRouter, Depends, Query, status
from app.schemas.daily_nutrition import DailyNutritionCreate, DailyNutritionSummary
from app.services.daily_nutrition_service import daily_nutrition_service
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter(tags=["Daily Nutrition Tracking"])

@router.get(
    "/nutrition/daily",
    response_model=DailyNutritionSummary,
    summary="Get today's daily nutrition breakdown",
    description="Calculates calories and macro intake vs target for today."
)
def get_today_nutrition(
    target_date: Optional[DateType] = Query(None, description="Optional target date (YYYY-MM-DD)"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return daily_nutrition_service.get_daily_nutrition(user_id=current_user.id, target_date=target_date)

@router.get(
    "/nutrition/daily/{log_date}",
    response_model=DailyNutritionSummary,
    summary="Get nutrition breakdown for a specific date"
)
def get_date_nutrition(
    log_date: DateType,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return daily_nutrition_service.get_daily_nutrition(user_id=current_user.id, target_date=log_date)

@router.post(
    "/nutrition/daily",
    response_model=DailyNutritionSummary,
    status_code=status.HTTP_200_OK,
    summary="Log daily water / nutrition intake"
)
def log_daily_nutrition(
    data: DailyNutritionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return daily_nutrition_service.log_daily_nutrition(user_id=current_user.id, data=data)
