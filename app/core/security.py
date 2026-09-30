from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from app.core.config import settings
from app.supabase.client import get_supabase_client

security_scheme = HTTPBearer(auto_error=False)

class AuthenticatedUser(BaseModel):
    id: str  # Supabase Auth UUID
    email: Optional[str] = None
    role: Optional[str] = "authenticated"
    user_metadata: Optional[Dict[str, Any]] = None
    app_metadata: Optional[Dict[str, Any]] = None
    token: Optional[str] = None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> AuthenticatedUser:
    """
    Validates Bearer token against Supabase Auth and returns the authenticated user.
    Never trusts client-supplied user_id.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    supabase = get_supabase_client()
    
    try:
        # Validate directly with Supabase Auth
        response = supabase.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = response.user
        return AuthenticatedUser(
            id=str(user.id),
            email=user.email,
            role=getattr(user, "role", "authenticated"),
            user_metadata=getattr(user, "user_metadata", {}) or {},
            app_metadata=getattr(user, "app_metadata", {}) or {},
            token=token
        )
    except HTTPException:
        raise
    except Exception as e:
        # Fallback local JWT decode if JWT_SECRET is configured
        if settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                user_id = payload.get("sub")
                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token payload."
                    )
                return AuthenticatedUser(
                    id=str(user_id),
                    email=payload.get("email"),
                    role=payload.get("role", "authenticated"),
                    user_metadata=payload.get("user_metadata", {}),
                    app_metadata=payload.get("app_metadata", {}),
                    token=token
                )
            except Exception:
                pass
                
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[AuthenticatedUser]:
    """
    Returns the authenticated user if valid token present, otherwise None.
    """
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
