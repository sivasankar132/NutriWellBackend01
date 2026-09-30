from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("nutriwell")

class AIContractException(Exception):
    def __init__(
        self,
        error_code: str = "GEMINI_UNAVAILABLE",
        message: str = "AI generation failed. Please try again.",
        status_code: int = 502
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": exc.detail
        },
        headers=exc.headers
    )

async def ai_contract_exception_handler(request: Request, exc: AIContractException):
    logger.error(f"AI Contract Exception on {request.url.path}: [{exc.error_code}] {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": 500,
            "message": "An unexpected internal server error occurred."
        }
    )
