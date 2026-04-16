from __future__ import annotations

import asyncio
import logging

from app.workers.export_worker import ExportWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("systemforge.export.runner")


async def _run_forever() -> None:
    worker = ExportWorker()
    logger.info("export_worker_started")
    while True:
        try:
            processed = await worker.process_once()
            if processed == 0:
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0)
        except Exception:
            logger.exception("export_worker_loop_error")
            await asyncio.sleep(1)


def main() -> None:
    asyncio.run(_run_forever())


if __name__ == "__main__":
    main()

