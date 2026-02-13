"""Worker entry point."""

import asyncio
import logging
import signal
import sys

from app.config import settings
from app.engine import SchedulerEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def _init_sentry() -> None:
    """Initialize Sentry for the worker if configured."""
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment="worker",
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info("Sentry initialized for worker")
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry init")


async def main():
    """Main entry point."""
    _init_sentry()
    engine = SchedulerEngine()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def handle_signal():
        logger.info("Received shutdown signal")
        asyncio.create_task(engine.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    logger.info("Starting EzMsg Worker")
    await engine.start()
    logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
