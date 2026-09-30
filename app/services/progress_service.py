from typing import List, Dict, Any, Optional
from datetime import date as DateType, date
from fastapi import HTTPException, status
from app.supabase.client import get_supabase_client, supabase
from app.schemas.progress import ProgressRecordCreate, ProgressRecordUpdate, ProgressSummaryResponse
from app.services.nutrition_service import nutrition_service
from app.utils.calculations import calculate_bmi

class ProgressService:
    def __init__(self):
        self.supabase = supabase

    def get_progress_records(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            res = (
                self.supabase
                .table("progress_records")
                .select("*")
                .eq("user_id", user_id)
                .order("date", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            err_str = str(e)
            if "PGRST205" in err_str or "schema cache" in err_str.lower():
                return []
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching progress records: {err_str}"
            )

    def get_progress_record_by_id(self, user_id: str, record_id: str) -> Dict[str, Any]:
        try:
            res = (
                self.supabase
                .table("progress_records")
                .select("*")
                .eq("id", record_id)
                .eq("user_id", user_id)
                .execute()
            )
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress record not found.")
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving progress record: {str(e)}"
            )

    def create_progress_record(self, user_id: str, data: ProgressRecordCreate) -> Dict[str, Any]:
        try:
            profile = nutrition_service.get_or_calculate_profile(user_id)
            height = float(profile.get("height") or 170.0)
            weight = float(data.weight)
            
            calculated_bmi = data.bmi
            if not calculated_bmi and height > 0:
                bmi_info = calculate_bmi(weight, height)
                calculated_bmi = bmi_info["bmi"]
                
            payload = {
                "user_id": user_id,
                "date": str(data.date or date.today()),
                "weight": weight,
                "bmi": calculated_bmi,
                "calories_consumed": data.calories_consumed or 0.0,
                "notes": data.notes
            }
            res = self.supabase.table("progress_records").insert(payload).execute()
            if not res.data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create progress record.")
            
            # Optionally update current weight in nutrition profile
            try:
                self.supabase.table("nutrition_profiles").update({"weight": weight}).eq("user_id", user_id).execute()
            except Exception:
                pass
                
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error saving progress record: {str(e)}"
            )

    def update_progress_record(self, user_id: str, record_id: str, data: ProgressRecordUpdate) -> Dict[str, Any]:
        try:
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if "date" in update_data and update_data["date"]:
                update_data["date"] = str(update_data["date"])
                
            if not update_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update.")
                
            res = (
                self.supabase
                .table("progress_records")
                .update(update_data)
                .eq("id", record_id)
                .eq("user_id", user_id)
                .execute()
            )
            if not res.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress record not found or unauthorized.")
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating progress record: {str(e)}"
            )

    def delete_progress_record(self, user_id: str, record_id: str) -> Dict[str, str]:
        try:
            self.supabase.table("progress_records").delete().eq("id", record_id).eq("user_id", user_id).execute()
            return {"status": "success", "message": "Progress record deleted."}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error deleting progress record: {str(e)}"
            )

    def get_progress_summary(self, user_id: str) -> Dict[str, Any]:
        try:
            records = self.get_progress_records(user_id)
            profile = nutrition_service.get_or_calculate_profile(user_id)
            
            # Fetch target weight from goals if available
            target_weight = None
            try:
                goals = self.supabase.table("nutrition_goals").select("target_weight").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
                if goals.data:
                    target_weight = goals.data[0].get("target_weight")
            except Exception:
                pass

            if not records:
                current_weight = float(profile.get("weight") or 0.0) if profile.get("weight") else None
                return {
                    "current_weight": current_weight,
                    "starting_weight": current_weight,
                    "weight_change": 0.0,
                    "current_bmi": profile.get("bmi"),
                    "target_weight": target_weight,
                    "total_logs": 0,
                    "records": []
                }

            # Records are sorted desc by date
            current_record = records[0]
            starting_record = records[-1]
            
            current_weight = float(current_record.get("weight") or 0.0)
            starting_weight = float(starting_record.get("weight") or 0.0)
            weight_change = round(current_weight - starting_weight, 2)
            
            return {
                "current_weight": current_weight,
                "starting_weight": starting_weight,
                "weight_change": weight_change,
                "current_bmi": current_record.get("bmi") or profile.get("bmi"),
                "target_weight": target_weight,
                "total_logs": len(records),
                "records": records
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculating progress summary: {str(e)}"
            )

progress_service = ProgressService()
