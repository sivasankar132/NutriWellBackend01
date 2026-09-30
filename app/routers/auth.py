from fastapi import APIRouter, Depends, status
from app.schemas.auth import SignUpRequest, LoginRequest, AuthTokenResponse, UserAuthResponse, MessageResponse
from app.services.auth_service import auth_service
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/signup",
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED,
    description="Registers a new account in Supabase Auth and sets up user profile."
)
def signup(data: SignUpRequest):
    return auth_service.signup(data)

@router.post(
    "/register",
    summary="Register a new user (Alias)",
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
def register(data: SignUpRequest):
    return auth_service.signup(data)

@router.post(
    "/login",
    response_model=AuthTokenResponse,
    summary="User Login",
    description="Authenticates credentials against Supabase Auth and returns JWT tokens."
)
def login(data: LoginRequest):
    return auth_service.login(data)

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User Logout",
    description="Terminates the current user session in Supabase."
)
def logout(current_user: AuthenticatedUser = Depends(get_current_user)):
    return auth_service.logout(current_user.token or "")

@router.get(
    "/me",
    response_model=UserAuthResponse,
    summary="Get Current Authenticated User",
    description="Returns the authenticated user details extracted from the validated Supabase JWT."
)
def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    name = current_user.user_metadata.get("name") if current_user.user_metadata else None
    return UserAuthResponse(
        id=current_user.id,
        email=current_user.email,
        name=name,
        role=current_user.role
    )
