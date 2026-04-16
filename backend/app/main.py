from uuid import uuid4
import logging
import sentry_sdk
import time

from fastapi import FastAPI
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.lifespan import app_lifespan
from app.core.metrics import observe_request

settings = get_settings()


def _enforce_security_baseline() -> None:
    env = settings.app_env.lower()
    if env in {"development", "dev", "test", "testing"}:
        return
    if settings.jwt_secret.strip() in {"", "change-me"} or len(settings.jwt_secret.strip()) < 32:
        raise RuntimeError("Insecure JWT secret for non-development environment")
    if not settings.cookie_secure:
        raise RuntimeError("cookie_secure must be true in non-development environments")


_enforce_security_baseline()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=1.0,
    )

app = FastAPI(title=settings.app_name, lifespan=app_lifespan)
logger = logging.getLogger("systemforge.api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id", str(uuid4()))
    started = time.perf_counter()
    if request.url.path.endswith("/designs") and request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_generation_payload_bytes:
            raise HTTPException(status_code=413, detail="Request payload too large")
    response = await call_next(request)
    # Apply baseline browser-side hardening headers for every API response.
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    if settings.cookie_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    response.headers.setdefault("X-API-Version", settings.api_version)
    response.headers.setdefault("X-API-Deprecation-Policy", settings.api_deprecation_policy_url)
    if settings.api_deprecated_after:
        response.headers.setdefault("Deprecation", settings.api_deprecated_after)
    if settings.api_sunset_at:
        response.headers.setdefault("Sunset", settings.api_sunset_at)
    prefix = f"{settings.api_prefix}/public"
    if request.url.path.startswith(prefix):
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    observe_request(path=request.url.path, method=request.method, status_code=response.status_code, elapsed_ms=elapsed_ms)
    logger.info(
        "request_completed",
        extra={
            "request_id": request.state.request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    response.headers["x-request-id"] = request.state.request_id
    return response


app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


app.include_router(api_router, prefix=settings.api_prefix)
