from typing import Dict, Any
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.auth import SignUpRequest, LoginRequest, AuthTokenResponse

class AuthService:
    def __init__(self):
        self.supabase = supabase

    def signup(self, data: SignUpRequest) -> Dict[str, Any]:
        """
        Signs up a user in Supabase Auth and registers them in public.users table.
        Auto-confirms the email so the user can immediately log in.
        """
        try:
            user_id = None
            access_token = ""
            refresh_token = ""
            
            # 1. Create confirmed user via Admin API
            try:
                admin_user_res = self.supabase.auth.admin.create_user({
                    "email": data.email,
                    "password": data.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "name": data.name
                    }
                })
                if admin_user_res and admin_user_res.user:
                    user_id = admin_user_res.user.id
            except Exception as admin_err:
                admin_msg = str(admin_err)
                if "already registered" in admin_msg.lower() or "already exists" in admin_msg.lower():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="A user with this email address already exists."
                    )
                # Fallback to standard sign_up if admin create is restricted
                auth_response = self.supabase.auth.sign_up({
                    "email": data.email,
                    "password": data.password,
                    "options": {
                        "data": {
                            "name": data.name
                        }
                    }
                })
                if not auth_response or not auth_response.user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Registration failed: {admin_msg}"
                    )
                user_id = auth_response.user.id
                if auth_response.session:
                    access_token = auth_response.session.access_token
                    refresh_token = auth_response.session.refresh_token

            # 2. Automatically generate session / login tokens if not present
            if not access_token:
                try:
                    login_res = self.supabase.auth.sign_in_with_password({
                        "email": data.email,
                        "password": data.password
                    })
                    if login_res and login_res.session:
                        access_token = login_res.session.access_token
                        refresh_token = login_res.session.refresh_token
                except Exception:
                    pass

            # 3. Sync to public.users table
            try:
                self.supabase.table("users").upsert({
                    "auth_user_id": str(user_id),
                    "name": data.name,
                    "email": data.email
                }, on_conflict="email").execute()
            except Exception:
                pass
            
            return {
                "message": "User registered successfully.",
                "user": {
                    "id": str(user_id),
                    "email": data.email,
                    "name": data.name
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email address already exists."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sign up error: {error_msg}"
            )

    def login(self, data: LoginRequest) -> AuthTokenResponse:
        """
        Authenticates the user with Supabase Auth and returns JWT tokens.
        """
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": data.email,
                "password": data.password
            })
            
            if not auth_response or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password."
                )
            
            session = auth_response.session
            user = auth_response.user
            user_metadata = getattr(user, "user_metadata", {}) or {}
            
            return AuthTokenResponse(
                access_token=session.access_token,
                token_type="bearer",
                expires_in=session.expires_in,
                refresh_token=session.refresh_token,
                user={
                    "id": str(user.id),
                    "email": user.email,
                    "name": user_metadata.get("name", user.email.split("@")[0]),
                    "role": getattr(user, "role", "authenticated")
                }
            )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

    def logout(self, token: str) -> Dict[str, str]:
        """
        Logs out the user session from Supabase.
        """
        try:
            self.supabase.auth.sign_out()
            return {"message": "Logged out successfully.", "status": "success"}
        except Exception:
            return {"message": "Logged out.", "status": "success"}

auth_service = AuthService()
