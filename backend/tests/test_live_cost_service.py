import pytest
from unittest.mock import AsyncMock, patch
from app.services.live_cost_service import sync_cloud_pricing, get_cloud_pricing, report_workspace_usage, get_workspace_usage

@pytest.mark.asyncio
@patch("app.services.live_cost_service.get_redis_client")
async def test_sync_cloud_pricing(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    res = await sync_cloud_pricing()
    assert "synced_at" in res
    mock_redis.set.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.live_cost_service.get_redis_client")
async def test_get_cloud_pricing(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = b'{"compute_index": 1.05}'
    
    res = await get_cloud_pricing()
    assert res["compute_index"] == 1.05

@pytest.mark.asyncio
@patch("app.services.live_cost_service.get_redis_client")
async def test_report_workspace_usage(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    
    res = await report_workspace_usage(1, 100, "test")
    assert res["monthly_actual_usd"] == 100
    mock_redis.set.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.live_cost_service.get_redis_client")
async def test_get_workspace_usage(mock_get_redis):
    mock_redis = AsyncMock()
    mock_get_redis.return_value = mock_redis
    mock_redis.get.return_value = b'{"monthly_actual_usd": 100}'
    
    res = await get_workspace_usage(1)
    assert res is not None
    assert res["monthly_actual_usd"] == 100
