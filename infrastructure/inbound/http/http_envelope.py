import logging
import time
from typing import Any

from fastapi import status
from fastapi.responses import JSONResponse

from infrastructure.inbound.http.http_error_mapper import map_error

logger = logging.getLogger(__name__)


def success(
    action: str, message: str, data: Any = None
) -> JSONResponse:  # noqa: ANN401 - JSON payload is arbitrary
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "action": action,
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": message,
            "timestamp": time.time(),
            "data": data,
        },
    )


def failure(action: str, message: str, error: Exception) -> JSONResponse:
    logger.error("%s failed: %r", action, error)
    code = map_error(error)
    return JSONResponse(
        status_code=code,
        content={
            "action": action,
            "status": "error",
            "status_code": code,
            "message": f"{message}: {error}",
            "timestamp": time.time(),
            "data": str(error),
        },
    )
