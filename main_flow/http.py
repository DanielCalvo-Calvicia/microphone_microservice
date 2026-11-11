
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from shared_logging import get_logger, init_logging

from composition_root.containers.http_container import HttpContainer, new_http_container
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig

logger = get_logger(__name__)

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
# A stop (SIGTERM, `docker stop`) waits this long for open requests (a stream, a playback)
# and then cancels them, so the cleanup runs inside Docker's 10 s grace period (R-16).
GRACEFUL_SHUTDOWN_SECONDS = 5


def load_environment(path: Path = _ENV_FILE) -> None:
    """Read the `.env` next to ``main.py``; a missing file is fine, the environment wins."""
    load_dotenv(dotenv_path=path, override=False)


async def run_http() -> None:
    load_environment()
    server_cfg = ServerConfig.from_env()
    microphone_cfg = MicrophoneConfig.from_env()
    init_logging("microphone")

    container = new_http_container(server_cfg, microphone_cfg)
    server = uvicorn.Server(
        uvicorn.Config(
            container.app,
            host=server_cfg.host,
            port=server_cfg.port,
            log_config=None,
            timeout_graceful_shutdown=GRACEFUL_SHUTDOWN_SECONDS,
        )
    )
    logger.info(
        "Starting server",
        service_name=server_cfg.service_name,
        host=server_cfg.host,
        port=server_cfg.port,
    )
    try:
        await server.serve()  # returns after SIGINT/SIGTERM
    finally:
        await _cleanup(container)


async def _cleanup(container: HttpContainer) -> None:
    logger.info("Server stopped; releasing microphone")
    try:
        await container.microphone.stop_stream()
    except Exception:
        logger.exception("Failed to stop microphone stream during cleanup")
    logger.info("Cleanup finished")
