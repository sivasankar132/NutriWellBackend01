from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.nutrition import router as nutrition_router
from app.routers.foods import router as foods_router
from app.routers.meals import router as meals_router
from app.routers.meal_plans import router as meal_plans_router
from app.routers.daily_nutrition import router as daily_nutrition_router
from app.routers.progress import router as progress_router

__all__ = [
    "auth_router",
    "users_router",
    "nutrition_router",
    "foods_router",
    "meals_router",
    "meal_plans_router",
    "daily_nutrition_router",
    "progress_router"
]
