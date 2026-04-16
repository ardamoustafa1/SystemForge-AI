from __future__ import annotations

import asyncio
from typing import Any


def run_async(coro: Any) -> Any:
    """Run async code from sync endpoints executed in threadpool workers."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

