from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.utils.error_handlers import custom_http_exception_handler, generic_exception_handler, ai_contract_exception_handler, AIContractException
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.nutrition import router as nutrition_router
from app.routers.foods import router as foods_router
from app.routers.meals import router as meals_router
from app.routers.meal_plans import router as meal_plans_router
from app.routers.daily_nutrition import router as daily_nutrition_router
from app.routers.progress import router as progress_router
from app.routers.assistant import router as assistant_router
from app.routers.ai import router as ai_router

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Nutri-Well Production Backend API powering nutrition tracking, meal planning, user profiles, and wellness goals.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Exception Handlers
app.add_exception_handler(AIContractException, ai_contract_exception_handler)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://(nutri-well.*|nutriwell.*)\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root & Health Check Endpoints
@app.get("/", tags=["System"])
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "docs": "/docs"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

# Include All Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(nutrition_router)
app.include_router(foods_router)
app.include_router(meals_router)
app.include_router(meal_plans_router)
app.include_router(daily_nutrition_router)
app.include_router(progress_router)
app.include_router(assistant_router)
app.include_router(ai_router)

