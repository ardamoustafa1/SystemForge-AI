from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.config import get_settings
from app.core.redis import get_redis_client


async def _check_worker(worker: str) -> int:
    settings = get_settings()
    redis = get_redis_client()
    try:
        pong = await redis.ping()
        if not pong:
            return 1
        if worker == "outbox":
            await redis.exists(f"{settings.outbox_stream_prefix}:delivery")
        elif worker == "delivery":
            await redis.exists(f"{settings.outbox_stream_prefix}:delivery")
        elif worker == "notification":
            await redis.exists(f"{settings.outbox_stream_prefix}:notify")
        elif worker == "export":
            await redis.exists(f"{settings.outbox_stream_prefix}:export")
        return 0
    except Exception:
        return 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=["outbox", "delivery", "notification", "export"], required=True)
    args = parser.parse_args()
    rc = asyncio.run(_check_worker(args.worker))
    sys.exit(rc)


if __name__ == "__main__":
    main()
