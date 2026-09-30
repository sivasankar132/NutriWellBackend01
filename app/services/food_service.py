from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.food import FoodCreate, FoodUpdate

FALLBACK_FOODS = [
    {"id": "f1001", "name": "Boiled Egg", "category": "Protein", "serving_size": "1 large (50g)", "serving_unit": "piece", "calories": 78.0, "protein": 6.3, "carbs": 0.6, "fats": 5.3, "fiber": 0.0, "diet_type": "Eggetarian", "is_custom": False},
    {"id": "f1002", "name": "Grilled Chicken Breast", "category": "Protein", "serving_size": "100g", "serving_unit": "g", "calories": 165.0, "protein": 31.0, "carbs": 0.0, "fats": 3.6, "fiber": 0.0, "diet_type": "Non-Veg", "is_custom": False},
    {"id": "f1003", "name": "Paneer (Cottage Cheese)", "category": "Protein", "serving_size": "100g", "serving_unit": "g", "calories": 265.0, "protein": 18.3, "carbs": 3.4, "fats": 20.8, "fiber": 0.0, "diet_type": "Veg", "is_custom": False},
    {"id": "f1004", "name": "Cooked Yellow Dal", "category": "Protein", "serving_size": "1 cup (200g)", "serving_unit": "cup", "calories": 180.0, "protein": 12.0, "carbs": 28.0, "fats": 2.5, "fiber": 7.0, "diet_type": "Veg", "is_custom": False},
    {"id": "f1005", "name": "Whole Wheat Roti", "category": "Carbs", "serving_size": "1 medium (35g)", "serving_unit": "piece", "calories": 104.0, "protein": 3.1, "carbs": 21.0, "fats": 0.5, "fiber": 3.2, "diet_type": "Vegan", "is_custom": False},
    {"id": "f1006", "name": "Cooked Brown Rice", "category": "Carbs", "serving_size": "1 cup (150g)", "serving_unit": "cup", "calories": 165.0, "protein": 3.5, "carbs": 35.0, "fats": 1.4, "fiber": 2.8, "diet_type": "Vegan", "is_custom": False},
    {"id": "f1007", "name": "Spinach (Palak)", "category": "Vegetables", "serving_size": "1 cup (180g)", "serving_unit": "cup", "calories": 41.0, "protein": 5.3, "carbs": 6.7, "fats": 0.5, "fiber": 4.3, "diet_type": "Vegan", "is_custom": False},
    {"id": "f1008", "name": "Banana", "category": "Fruits", "serving_size": "1 medium (118g)", "serving_unit": "piece", "calories": 105.0, "protein": 1.3, "carbs": 27.0, "fats": 0.3, "fiber": 3.1, "diet_type": "Vegan", "is_custom": False}
]

class FoodService:
    def __init__(self):
        self.supabase = supabase

    def get_foods(
        self,
        category: Optional[str] = None,
        diet_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieves public foods and custom foods.
        """
        try:
            query = self.supabase.table("foods").select("*")
            
            if search:
                query = query.ilike("name", f"%{search}%")
            if category:
                query = query.eq("category", category)
            if diet_type:
                query = query.eq("diet_type", diet_type)
                
            query = query.order("name").range(offset, offset + limit - 1)
            res = query.execute()
            if res.data:
                return res.data
        except Exception as e:
            err_str = str(e)
            if "PGRST205" not in err_str and "schema cache" not in err_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error searching foods: {err_str}"
                )

        # Fallback to local catalog if table is not yet seeded
        results = FALLBACK_FOODS
        if search:
            results = [f for f in results if search.lower() in f["name"].lower()]
        if category:
            results = [f for f in results if f["category"].lower() == category.lower()]
        if diet_type:
            results = [f for f in results if f["diet_type"].lower() == diet_type.lower()]
        return results[offset:offset + limit]

    def get_food_by_id(self, food_id: str) -> Dict[str, Any]:
        try:
            res = self.supabase.table("foods").select("*").eq("id", food_id).execute()
            if res.data:
                return res.data[0]
        except Exception:
            pass

        # Check in fallback
        for f in FALLBACK_FOODS:
            if f["id"] == food_id:
                return f

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found."
        )

    def create_food(self, data: FoodCreate, user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            food_dict = data.model_dump()
            if user_id:
                food_dict["created_by"] = user_id
                food_dict["is_custom"] = True
                
            res = self.supabase.table("foods").insert(food_dict).execute()
            if not res.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create food item."
                )
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating food item: {str(e)}"
            )

    def update_food(self, food_id: str, data: FoodUpdate, user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if not update_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
                
            query = self.supabase.table("foods").update(update_data).eq("id", food_id)
            if user_id:
                query = query.eq("created_by", user_id)
                
            res = query.execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found or unauthorized.")
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating food item: {str(e)}"
            )

    def delete_food(self, food_id: str, user_id: Optional[str] = None) -> Dict[str, str]:
        try:
            query = self.supabase.table("foods").delete().eq("id", food_id)
            if user_id:
                query = query.eq("created_by", user_id)
            res = query.execute()
            return {"status": "success", "message": "Food item deleted."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting food item: {str(e)}"
            )

food_service = FoodService()
