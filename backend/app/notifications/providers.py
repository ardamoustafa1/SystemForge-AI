from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

logger = logging.getLogger("systemforge.notifications.providers")


@dataclass(frozen=True)
class NotificationResult:
    ok: bool
    provider: str
    token: str
    error: str | None = None


class PushProvider(Protocol):
    async def send_fcm(self, *, token: str, title: str, body: str, data: dict) -> NotificationResult: ...
    async def send_apns(self, *, token: str, title: str, body: str, data: dict) -> NotificationResult: ...


class MockPushProvider:
    """
    Mock integration boundary for FCM/APNs.
    In production replace these with real provider clients.
    """

    async def send_fcm(self, *, token: str, title: str, body: str, data: dict) -> NotificationResult:
        if "fail" in token:
            return NotificationResult(ok=False, provider="fcm", token=token, error="mock_fcm_delivery_failed")
        logger.info("mock_fcm_sent", extra={"token": token, "title": title})
        return NotificationResult(ok=True, provider="fcm", token=token)

    async def send_apns(self, *, token: str, title: str, body: str, data: dict) -> NotificationResult:
        if "fail" in token:
            return NotificationResult(ok=False, provider="apns", token=token, error="mock_apns_delivery_failed")
        logger.info("mock_apns_sent", extra={"token": token, "title": title})
        return NotificationResult(ok=True, provider="apns", token=token)


class WebhookPushProvider:
    """
    Production-oriented provider boundary using HTTP webhooks.
    If endpoints are configured, outbound push dispatches are executed over HTTP.
    """

    def __init__(self, *, fcm_url: str | None, apns_url: str | None, timeout_seconds: int = 5) -> None:
        self.fcm_url = (fcm_url or "").strip()
        self.apns_url = (apns_url or "").strip()
        self.timeout_seconds = max(1, int(timeout_seconds))

    async def _post(self, *, provider: str, url: str, token: str, title: str, body: str, data: dict) -> NotificationResult:
        if not url:
            return NotificationResult(ok=False, provider=provider, token=token, error=f"{provider}_webhook_not_configured")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(
                    url,
                    json={"token": token, "title": title, "body": body, "data": data},
                    headers={"content-type": "application/json"},
                )
            if 200 <= resp.status_code < 300:
                return NotificationResult(ok=True, provider=provider, token=token)
            return NotificationResult(ok=False, provider=provider, token=token, error=f"{provider}_http_{resp.status_code}")
        except Exception:
            logger.exception("push_webhook_failed", extra={"provider": provider})
            return NotificationResult(ok=False, provider=provider, token=token, error=f"{provider}_transport_error")

    async def send_fcm(self, *, token: str, title: str, body: str, data: dict) -> NotificationResult:
        return await self._post(provider="fcm", url=self.fcm_url, token=token, title=title, body=body, data=data)

    async def send_apns(self, *, token: str, title: str, body: str, data: dict) -> NotificationResult:
        return await self._post(provider="apns", url=self.apns_url, token=token, title=title, body=body, data=data)
