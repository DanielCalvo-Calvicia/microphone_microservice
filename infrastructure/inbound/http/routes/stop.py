from fastapi.responses import JSONResponse

from application.ports.inbound.microphone_inbound_port import MicrophoneInboundPort
from infrastructure.inbound.http.response.http_envelope import failure, success


async def handle_stop(inbound: MicrophoneInboundPort) -> JSONResponse:
    """POST /stop: stop the capture. Does nothing if none is active."""
    try:
        await inbound.stop_stream()
    except Exception as error:
        return failure("stop_stream", "Failed to stop microphone stream", error)
    return success("stop_stream", "Microphone stream stopped successfully", True)
