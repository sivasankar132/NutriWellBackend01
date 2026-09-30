from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Body, status
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.profile import UserProfileUpdateRequest, UserProfileResponse
from app.services.user_service import user_service
from app.core.security import get_current_user, AuthenticatedUser
from app.services.nutrition_service import nutrition_service

router = APIRouter(tags=["Users & Profile"])

@router.get(
    "/users/me",
    response_model=UserProfileResponse,
    summary="Get current user profile and health targets",
    description="Returns the authenticated user's profile, including personal details, dietary preferences, and computed BMR/TDEE/macro targets."
)
def get_current_user_profile(current_user: AuthenticatedUser = Depends(get_current_user)):
    user_data = user_service.get_user_by_auth_id(current_user.id)
    profile_data = nutrition_service.get_or_calculate_profile(current_user.id)
    
    name = current_user.user_metadata.get("name") or (user_data.get("name") if user_data else "")
    
    return UserProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        name=name,
        age=profile_data.get("age"),
        gender=profile_data.get("gender"),
        height=profile_data.get("height"),
        weight=profile_data.get("weight"),
        activity_level=profile_data.get("activity_level", "Moderately Active"),
        dietary_preference=profile_data.get("dietary_preference", "Veg"),
        food_preferences=profile_data.get("food_preferences", []) or [],
        allergies=profile_data.get("allergies", []) or [],
        medical_or_dietary_restrictions=profile_data.get("medical_or_dietary_restrictions", []) or [],
        nutrition_goal=profile_data.get("nutrition_goal", "maintenance"),
        bmi=profile_data.get("bmi"),
        bmi_category=profile_data.get("bmi_category"),
        bmr=profile_data.get("bmr"),
        tdee=profile_data.get("tdee"),
        daily_calorie_target=profile_data.get("daily_calorie_target"),
        daily_protein_target=profile_data.get("daily_protein_target"),
        daily_carbs_target=profile_data.get("daily_carbs_target"),
        daily_fat_target=profile_data.get("daily_fat_target"),
        daily_water_target_ml=profile_data.get("daily_water_target_ml"),
        created_at=profile_data.get("created_at"),
        updated_at=profile_data.get("updated_at")
    )

@router.put(
    "/users/me",
    response_model=UserProfileResponse,
    summary="Update current user profile",
    description="Updates the authenticated user's personal details, body measurements, dietary preferences, and nutrition goals."
)
def update_current_user_profile(
    data: UserProfileUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    # 1. Update user name in public.users and user metadata if supplied
    if data.name:
        try:
            user_data = user_service.get_user_by_auth_id(current_user.id)
            if user_data and "id" in user_data:
                user_service.update_user(user_data["id"], UserUpdate(name=data.name))
        except Exception:
            pass
        if current_user.user_metadata is None:
            current_user.user_metadata = {}
        current_user.user_metadata["name"] = data.name

    # 2. Upsert profile metrics
    updated_profile = nutrition_service.upsert_profile(current_user.id, data)
    
    return UserProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        name=data.name or current_user.user_metadata.get("name"),
        age=updated_profile.get("age"),
        gender=updated_profile.get("gender"),
        height=updated_profile.get("height"),
        weight=updated_profile.get("weight"),
        activity_level=updated_profile.get("activity_level", "Moderately Active"),
        dietary_preference=updated_profile.get("dietary_preference", "Veg"),
        food_preferences=updated_profile.get("food_preferences", []) or [],
        allergies=updated_profile.get("allergies", []) or [],
        medical_or_dietary_restrictions=updated_profile.get("medical_or_dietary_restrictions", []) or [],
        nutrition_goal=updated_profile.get("nutrition_goal", "maintenance"),
        bmi=updated_profile.get("bmi"),
        bmi_category=updated_profile.get("bmi_category"),
        bmr=updated_profile.get("bmr"),
        tdee=updated_profile.get("tdee"),
        daily_calorie_target=updated_profile.get("daily_calorie_target"),
        daily_protein_target=updated_profile.get("daily_protein_target"),
        daily_carbs_target=updated_profile.get("daily_carbs_target"),
        daily_fat_target=updated_profile.get("daily_fat_target"),
        daily_water_target_ml=updated_profile.get("daily_water_target_ml"),
        created_at=updated_profile.get("created_at"),
        updated_at=updated_profile.get("updated_at")
    )

# ----------------- PRESERVED EXISTING ROUTES ----------------- #

@router.get(
    "/users",
    summary="List all users",
    description="Preserved endpoint: Retrieves all registered users from public.users."
)
def get_users():
    return user_service.get_users()

@router.post(
    "/users",
    summary="Create a user",
    description="Preserved endpoint: Inserts a user into public.users."
)
def create_user(
    name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    body: Optional[UserCreate] = None
):
    user_name = name or (body.name if body else None)
    user_email = email or (body.email if body else None)
    
    if not user_name or not user_email:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="name and email are required parameters."
        )
        
    return user_service.create_user(UserCreate(name=user_name, email=user_email))

@router.put(
    "/users/{user_id}",
    summary="Update a user by ID",
    description="Preserved endpoint: Updates a user record in public.users."
)
def update_user(
    user_id: int,
    name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    body: Optional[UserUpdate] = None
):
    user_name = name or (body.name if body else None)
    user_email = email or (body.email if body else None)
    
    return user_service.update_user(user_id, UserUpdate(name=user_name, email=user_email))
