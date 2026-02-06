from fastapi import HTTPException
from typing import Any, Dict, Optional

class AppError(HTTPException):
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        code: str = "generic_error",
        meta: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.meta = meta

class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str = None):
        detail = f"{resource} not found"
        if resource_id:
            detail += f": {resource_id}"
        super().__init__(status_code=404, detail=detail, code="resource_not_found")

class ValidationError(AppError):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail, code="validation_error")

class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(status_code=401, detail=detail, code="unauthorized")

class ForbiddenError(AppError):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=403, detail=detail, code="forbidden")

class InternalServerError(AppError):
    def __init__(self):
        super().__init__(status_code=500, detail="Internal server error", code="internal_error")
