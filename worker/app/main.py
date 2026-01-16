"""Worker entry point."""

import asyncio
import logging
import signal
import sys

from app.engine import SchedulerEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point."""
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
