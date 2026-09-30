from typing import List, Dict, Any, Optional
from datetime import date as DateType, date
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.meal import MealCreate, MealUpdate, MealItemCreate, MealItemUpdate
from app.utils.calculations import aggregate_meal_nutrition

class MealService:
    def __init__(self):
        self.supabase = supabase

    def get_meals(self, user_id: str, meal_date: Optional[DateType] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all meals for an authenticated user, optionally filtered by date, with their items and calculated nutrition totals.
        """
        try:
            query = self.supabase.table("meals").select("*, meal_items(*)").eq("user_id", user_id)
            if meal_date:
                query = query.eq("meal_date", str(meal_date))
            query = query.order("created_at", desc=True)
            res = query.execute()
            
            meals_data = res.data or []
            enriched_meals = []
            for meal in meals_data:
                items = meal.get("meal_items", []) or []
                totals = aggregate_meal_nutrition(items)
                enriched_meals.append({
                    "id": meal["id"],
                    "user_id": meal["user_id"],
                    "meal_type": meal["meal_type"],
                    "meal_date": meal.get("meal_date"),
                    "notes": meal.get("notes"),
                    "total_calories": totals["calories"],
                    "total_protein": totals["protein"],
                    "total_carbs": totals["carbs"],
                    "total_fats": totals["fats"],
                    "total_fiber": totals["fiber"],
                    "items": items,
                    "created_at": meal.get("created_at"),
                    "updated_at": meal.get("updated_at")
                })
            return enriched_meals
        except Exception as e:
            err_str = str(e)
            if "PGRST205" in err_str or "schema cache" in err_str.lower():
                return []
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching meals: {err_str}"
            )

    def get_meal_by_id(self, user_id: str, meal_id: str) -> Dict[str, Any]:
        try:
            res = self.supabase.table("meals").select("*, meal_items(*)").eq("id", meal_id).eq("user_id", user_id).execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found.")
            
            meal = res.data[0]
            items = meal.get("meal_items", []) or []
            totals = aggregate_meal_nutrition(items)
            return {
                "id": meal["id"],
                "user_id": meal["user_id"],
                "meal_type": meal["meal_type"],
                "meal_date": meal.get("meal_date"),
                "notes": meal.get("notes"),
                "total_calories": totals["calories"],
                "total_protein": totals["protein"],
                "total_carbs": totals["carbs"],
                "total_fats": totals["fats"],
                "total_fiber": totals["fiber"],
                "items": items,
                "created_at": meal.get("created_at"),
                "updated_at": meal.get("updated_at")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving meal: {str(e)}"
            )

    def create_meal(self, user_id: str, data: MealCreate) -> Dict[str, Any]:
        try:
            meal_payload = {
                "user_id": user_id,
                "meal_type": data.meal_type,
                "meal_date": str(data.meal_date or date.today()),
                "notes": data.notes
            }
            res = self.supabase.table("meals").insert(meal_payload).execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create meal record.")
            
            created_meal = res.data[0]
            meal_id = created_meal["id"]
            
            inserted_items = []
            if data.items:
                items_payload = []
                for item in data.items:
                    item_dict = item.model_dump()
                    item_dict["meal_id"] = meal_id
                    items_payload.append(item_dict)
                items_res = self.supabase.table("meal_items").insert(items_payload).execute()
                inserted_items = items_res.data or []
                
            totals = aggregate_meal_nutrition(inserted_items)
            return {
                "id": meal_id,
                "user_id": user_id,
                "meal_type": created_meal["meal_type"],
                "meal_date": created_meal.get("meal_date"),
                "notes": created_meal.get("notes"),
                "total_calories": totals["calories"],
                "total_protein": totals["protein"],
                "total_carbs": totals["carbs"],
                "total_fats": totals["fats"],
                "total_fiber": totals["fiber"],
                "items": inserted_items,
                "created_at": created_meal.get("created_at"),
                "updated_at": created_meal.get("updated_at")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating meal: {str(e)}"
            )

    def update_meal(self, user_id: str, meal_id: str, data: MealUpdate) -> Dict[str, Any]:
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if "meal_date" in update_data and update_data["meal_date"]:
                update_data["meal_date"] = str(update_data["meal_date"])
                
            if update_data:
                res = self.supabase.table("meals").update(update_data).eq("id", meal_id).eq("user_id", user_id).execute()
                if not res.data:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found or unauthorized.")
            
            return self.get_meal_by_id(user_id, meal_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating meal: {str(e)}"
            )

    def delete_meal(self, user_id: str, meal_id: str) -> Dict[str, str]:
        try:
            res = self.supabase.table("meals").delete().eq("id", meal_id).eq("user_id", user_id).execute()
            return {"status": "success", "message": "Meal deleted successfully."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting meal: {str(e)}"
            )

    def add_meal_item(self, user_id: str, meal_id: str, item: MealItemCreate) -> Dict[str, Any]:
        self.get_meal_by_id(user_id, meal_id)
        
        try:
            item_payload = item.model_dump()
            item_payload["meal_id"] = meal_id
            res = self.supabase.table("meal_items").insert(item_payload).execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to add meal item.")
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error adding meal item: {str(e)}"
            )

    def update_meal_item(self, user_id: str, meal_id: str, item_id: str, item: MealItemUpdate) -> Dict[str, Any]:
        self.get_meal_by_id(user_id, meal_id)
        
        try:
            update_data = {k: v for k, v in item.model_dump().items() if v is not None}
            if not update_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")
                
            res = self.supabase.table("meal_items").update(update_data).eq("id", item_id).eq("meal_id", meal_id).execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal item not found.")
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating meal item: {str(e)}"
            )

    def delete_meal_item(self, user_id: str, meal_id: str, item_id: str) -> Dict[str, str]:
        self.get_meal_by_id(user_id, meal_id)
        
        try:
            self.supabase.table("meal_items").delete().eq("id", item_id).eq("meal_id", meal_id).execute()
            return {"status": "success", "message": "Meal item removed."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting meal item: {str(e)}"
            )

meal_service = MealService()
