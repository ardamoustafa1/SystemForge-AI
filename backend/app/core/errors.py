from uuid import uuid4

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _error_response(request: Request, code: str, message: str, status_code: int, details: list[dict] | None = None):
    request_id = getattr(request.state, "request_id", None)
    payload = {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": request_id or str(uuid4()),
        }
    }
    return JSONResponse(status_code=status_code, content=payload)


def http_exception_handler(request: Request, exc: HTTPException):
    return _error_response(
        request=request,
        code="HTTP_ERROR",
        message=str(exc.detail),
        status_code=exc.status_code,
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(str(x) for x in err["loc"]), "reason": err["msg"]} for err in exc.errors()]
    return _error_response(
        request=request,
        code="VALIDATION_ERROR",
        message="Validation failed",
        status_code=422,
        details=details,
    )


def unhandled_exception_handler(request: Request, _: Exception):
    return _error_response(
        request=request,
        code="INTERNAL_ERROR",
        message="Unexpected server error",
        status_code=500,
    )
