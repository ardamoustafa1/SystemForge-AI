from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.workers.outbox_relay import OutboxRelayWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("systemforge.outbox.runner")


async def _run_forever() -> None:
    settings = get_settings()
    worker = OutboxRelayWorker()
    poll_seconds = max(settings.outbox_relay_poll_ms, 100) / 1000.0

    logger.info(
        "outbox_relay_started",
        extra={
            "poll_seconds": poll_seconds,
            "batch_size": settings.outbox_relay_batch_size,
        },
    )

    while True:
        try:
            processed = await worker.process_once()
            if processed == 0:
                await asyncio.sleep(poll_seconds)
            else:
                # Yield event loop quickly under load.
                await asyncio.sleep(0)
        except Exception:
            logger.exception("outbox_relay_loop_error")
            await asyncio.sleep(poll_seconds)


def main() -> None:
    asyncio.run(_run_forever())


if __name__ == "__main__":
    main()
