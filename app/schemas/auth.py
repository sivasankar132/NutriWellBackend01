from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    name: str = Field(..., min_length=1, max_length=255)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    user: Dict[str, Any]

class UserAuthResponse(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = "authenticated"
    created_at: Optional[str] = None

class MessageResponse(BaseModel):
    message: str
    status: str = "success"
