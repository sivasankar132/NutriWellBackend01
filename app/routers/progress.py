from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.progress import (
    ProgressRecordCreate,
    ProgressRecordUpdate,
    ProgressRecordResponse,
    ProgressSummaryResponse
)
from app.services.progress_service import progress_service
from app.core.security import get_current_user, AuthenticatedUser

router = APIRouter(prefix="/progress", tags=["Progress & Weight Tracking"])

@router.get(
    "/summary",
    response_model=ProgressSummaryResponse,
    summary="Get user progress summary",
    description="Returns starting weight, current weight, delta, BMI, and logged records."
)
def get_progress_summary(current_user: AuthenticatedUser = Depends(get_current_user)):
    return progress_service.get_progress_summary(user_id=current_user.id)

@router.get(
    "",
    response_model=List[ProgressRecordResponse],
    summary="Get all progress records"
)
def get_progress_records(current_user: AuthenticatedUser = Depends(get_current_user)):
    return progress_service.get_progress_records(user_id=current_user.id)

@router.post(
    "",
    response_model=ProgressRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log weight / progress entry"
)
def create_progress_record(
    data: ProgressRecordCreate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return progress_service.create_progress_record(user_id=current_user.id, data=data)

@router.get(
    "/{record_id}",
    response_model=ProgressRecordResponse,
    summary="Get progress record by ID"
)
def get_progress_record(
    record_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return progress_service.get_progress_record_by_id(user_id=current_user.id, record_id=record_id)

@router.put(
    "/{record_id}",
    response_model=ProgressRecordResponse,
    summary="Update progress record"
)
def update_progress_record(
    record_id: str,
    data: ProgressRecordUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return progress_service.update_progress_record(user_id=current_user.id, record_id=record_id, data=data)

@router.delete(
    "/{record_id}",
    summary="Delete progress record"
)
def delete_progress_record(
    record_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return progress_service.delete_progress_record(user_id=current_user.id, record_id=record_id)
