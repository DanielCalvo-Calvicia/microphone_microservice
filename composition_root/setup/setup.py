import logging
import os

import uvicorn

from composition_root.containers.container import Container, BuildContainer

NAME: str = "Microphone Microservice"
HOST: str = "127.0.0.1"
PORT: int = 8000

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Honor LOG_LEVEL (defaults to INFO)."""
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


async def setup() -> None:
    configure_logging()
    logger.info("%s - starting server on %s:%s", NAME, HOST, PORT)

    container = BuildContainer(name=NAME)
    config = uvicorn.Config(container.microphone_dependency.app, host=HOST, port=PORT)
    server = uvicorn.Server(config)

    try:
        # serve() blocks and shuts down gracefully on Ctrl+C / termination signals.
        await server.serve()
    finally:
        await _cleanup(container)


async def _cleanup(container: Container) -> None:
    logger.info("Server stopped; releasing microphone")
    try:
        await container.microphone_dependency.service.stop_stream()
    except Exception:
        logger.exception("Failed to stop microphone stream during cleanup")
    logger.info("Cleanup finished")
