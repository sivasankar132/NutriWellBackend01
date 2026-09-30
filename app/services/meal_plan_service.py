from typing import List, Dict, Any, Optional
from datetime import date as DateType, date
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.meal_plan import MealPlanCreate, MealPlanUpdate, MealPlanItemCreate

class MealPlanService:
    def __init__(self):
        self.supabase = supabase

    def get_meal_plans(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = (
                self.supabase
                .table("meal_plans")
                .select("*, meal_plan_items(*)")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            plans = res.data or []
            for plan in plans:
                plan["items"] = plan.get("meal_plan_items", []) or []
            return plans
        except Exception as e:
            err_str = str(e)
            if "PGRST205" in err_str or "schema cache" in err_str.lower():
                return []
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching meal plans: {err_str}"
            )

    def get_meal_plan_by_id(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        try:
            res = (
                self.supabase
                .table("meal_plans")
                .select("*, meal_plan_items(*)")
                .eq("id", plan_id)
                .eq("user_id", user_id)
                .execute()
            )
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found.")
            plan = res.data[0]
            plan["items"] = plan.get("meal_plan_items", []) or []
            return plan
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching meal plan: {str(e)}"
            )

    def create_meal_plan(self, user_id: str, data: MealPlanCreate) -> Dict[str, Any]:
        try:
            plan_payload = {
                "user_id": user_id,
                "name": data.name,
                "description": data.description,
                "start_date": str(data.start_date or date.today()),
                "end_date": str(data.end_date) if data.end_date else None
            }
            res = self.supabase.table("meal_plans").insert(plan_payload).execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create meal plan.")
                
            created_plan = res.data[0]
            plan_id = created_plan["id"]
            
            inserted_items = []
            if data.items:
                items_payload = []
                for item in data.items:
                    item_dict = item.model_dump()
                    item_dict["meal_plan_id"] = plan_id
                    items_payload.append(item_dict)
                items_res = self.supabase.table("meal_plan_items").insert(items_payload).execute()
                inserted_items = items_res.data or []
                
            created_plan["items"] = inserted_items
            return created_plan
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating meal plan: {str(e)}"
            )

    def update_meal_plan(self, user_id: str, plan_id: str, data: MealPlanUpdate) -> Dict[str, Any]:
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if "start_date" in update_data and update_data["start_date"]:
                update_data["start_date"] = str(update_data["start_date"])
            if "end_date" in update_data and update_data["end_date"]:
                update_data["end_date"] = str(update_data["end_date"])
                
            if update_data:
                res = self.supabase.table("meal_plans").update(update_data).eq("id", plan_id).eq("user_id", user_id).execute()
                if not res.data:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found or unauthorized.")
                    
            return self.get_meal_plan_by_id(user_id, plan_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating meal plan: {str(e)}"
            )

    def delete_meal_plan(self, user_id: str, plan_id: str) -> Dict[str, str]:
        try:
            self.supabase.table("meal_plans").delete().eq("id", plan_id).eq("user_id", user_id).execute()
            return {"status": "success", "message": "Meal plan deleted successfully."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting meal plan: {str(e)}"
            )

meal_plan_service = MealPlanService()
