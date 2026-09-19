import logging

import uvicorn

from composition_root.containers.http_container import HttpContainer, new_http_container
from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig
from main_flow.logging_setup import configure_logging

logger = logging.getLogger(__name__)


async def run_http() -> None:
    server_cfg = ServerConfig.from_env()
    microphone_cfg = MicrophoneConfig.from_env()
    configure_logging(server_cfg.log_level)

    container = new_http_container(server_cfg, microphone_cfg)
    server = uvicorn.Server(
        uvicorn.Config(container.app, host=server_cfg.host, port=server_cfg.port)
    )
    logger.info(
        "%s - starting server on %s:%s", server_cfg.service_name, server_cfg.host, server_cfg.port
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
