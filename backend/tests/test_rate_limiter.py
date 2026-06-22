import pytest
from datetime import datetime, timezone
import asyncio
from app.core.rate_limiter import enforce_rate_limit
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_rate_limiter_memory_fallback(monkeypatch):
    from app.core.config import get_settings
    # Patch app_env so it allows memory fallback
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "development")
    
    # Patch get_redis_client to fail
    async def mock_get_redis():
        raise ConnectionError("Redis down")
    monkeypatch.setattr("app.core.rate_limiter.get_redis_client", mock_get_redis)
    
    scope = "test"
    identifier = "limit"
    for i in range(5):
        await enforce_rate_limit(scope, identifier, limit=5, window_seconds=60)
        
    with pytest.raises(HTTPException) as exc:
        await enforce_rate_limit(scope, identifier, limit=5, window_seconds=60)
    assert exc.value.status_code == 429
