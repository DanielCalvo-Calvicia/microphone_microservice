from contracts.api.microservices.common.availability import AvailabilityResponse
from fastapi.responses import JSONResponse

from application.ports.inbound.microphone_inbound_port import MicrophoneInboundPort
from infrastructure.inbound.http.response.http_envelope import failure, success


async def handle_available(inbound: MicrophoneInboundPort) -> JSONResponse:
    """GET /available: whether an input device is usable (probed without opening it)."""
    try:
        available, reason = await inbound.check_device()
    except Exception as error:
        return failure("check_availability", "Failed to check microphone availability", error)
    return success(
        "check_availability",
        "Microphone availability checked successfully",
        AvailabilityResponse(is_available=available, reason=reason),
    )
