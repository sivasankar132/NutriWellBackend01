from fastapi import APIRouter, Depends
from app.core.security import get_current_user, AuthenticatedUser
from app.routers.ai import ai_chat, AIChatRequest
from app.schemas.ai import AISuccessResponse, AIChatResult

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

@router.post(
    "/chat",
    response_model=AISuccessResponse[AIChatResult],
    summary="Send prompt to AI Assistant",
    description="Delegates to /ai/chat conforming to the Critical AI Contract."
)
def chat_with_assistant(
    data: AIChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    return ai_chat(data=data, current_user=current_user)
