import pytest
from unittest.mock import AsyncMock, patch
from app.services.abuse_analytics_service import record_abuse_event, get_abuse_summary

@pytest.mark.asyncio
@patch("app.services.abuse_analytics_service.get_redis_client")
async def test_record_abuse_event(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    await record_abuse_event("test_event", "user1", 80)
    assert mock_redis.incrby.call_count >= 1
    mock_redis.xadd.assert_called()

@pytest.mark.asyncio
@patch("app.services.abuse_analytics_service.get_redis_client")
async def test_get_abuse_summary(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    # scan returns a tuple (cursor, keys)
    mock_redis.scan.side_effect = [(0, [b"abuse:counter:2026-06-22:test_event"]), (0, [])]
    mock_redis.get.return_value = b"5"
    
    res = await get_abuse_summary(1)
    assert res["test_event"] == 5
