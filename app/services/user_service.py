from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self):
        self.supabase = supabase

    def get_users(self) -> List[Dict[str, Any]]:
        """
        Retrieves all users (preserves existing functionality).
        """
        try:
            response = self.supabase.table("users").select("*").execute()
            return response.data or []
        except Exception as e:
            err_str = str(e)
            if "PGRST205" in err_str or "schema cache" in err_str.lower():
                return []
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch users: {err_str}"
            )

    def create_user(self, data: UserCreate) -> Dict[str, Any]:
        """
        Creates a user in public.users table (preserves existing POST /users).
        """
        try:
            response = self.supabase.table("users").insert({
                "name": data.name,
                "email": data.email
            }).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user record."
                )
            return response.data[0] if isinstance(response.data, list) else response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating user: {str(e)}"
            )

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found."
                )
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user: {str(e)}"
            )

    def get_user_by_auth_id(self, auth_user_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.supabase.table("users").select("*").eq("auth_user_id", auth_user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception:
            return None

    def update_user(self, user_id: int, data: UserUpdate) -> Dict[str, Any]:
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No update fields provided."
                )
            
            response = (
                self.supabase
                .table("users")
                .update(update_data)
                .eq("id", user_id)
                .execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or update failed."
                )
            return response.data[0] if isinstance(response.data, list) else response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating user: {str(e)}"
            )

user_service = UserService()
