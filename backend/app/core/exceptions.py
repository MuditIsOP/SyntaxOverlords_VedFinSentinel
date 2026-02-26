from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
import structlog

logger = structlog.get_logger()

class VedFinException(Exception):
    def __init__(self, status_code: int, type_uri: str, title: str, detail: str, extension_members: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.type_uri = type_uri
        self.title = title
        self.detail = detail
        self.extension_members = extension_members or {}

class UserNotFoundException(VedFinException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=404,
            type_uri="https://vedfin.com/errors/user-not-found",
            title="User Not Found",
            detail=f"User with ID {user_id} does not exist in the system.",
            extension_members={"user_id": user_id}
        )

class InvalidTransactionException(VedFinException):
    def __init__(self, reason: str):
        super().__init__(
            status_code=400,
            type_uri="https://vedfin.com/errors/invalid-transaction",
            title="Invalid Transaction Payload",
            detail=reason
        )

class PredictionFailedException(VedFinException):
    def __init__(self, reason: str):
        super().__init__(
            status_code=500,
            type_uri="https://vedfin.com/errors/prediction-failed",
            title="Prediction Engine Failure",
            detail=reason
        )

async def rfc7807_exception_handler(request: Request, exc: VedFinException):
    error_payload = {
        "type": exc.type_uri,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url),
        **exc.extension_members
    }
    
    logger.error("API Error", **error_payload)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload,
        media_type="application/problem+json"
    )

async def global_exception_handler(request: Request, exc: Exception):
    error_payload = {
        "type": "https://vedfin.com/errors/internal-server-error",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "An unexpected error occurred processing the request.",
        "instance": str(request.url),
    }
    
    logger.error("Unhandled Exception", exc_info=exc, **error_payload)
    
    return JSONResponse(
        status_code=500,
        content=error_payload,
        media_type="application/problem+json"
    )
