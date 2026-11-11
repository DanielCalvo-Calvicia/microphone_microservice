from contracts.api.microservices.microphone.start import MicrophoneConfig
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from application.dtos.inbound.start_stream_inbound import StartStreamInboundDTO
from application.ports.inbound.microphone_inbound_port import MicrophoneInboundPort
from infrastructure.inbound.http.response.http_envelope import failure, success

_DEFAULTS = StartStreamInboundDTO()


class StartStreamBody(BaseModel):
    """HTTP transport model for ``POST /start``. Never crosses into application/."""

    sample_rate: int = _DEFAULTS.sample_rate
    channels: int = _DEFAULTS.channels
    chunk_size: int = _DEFAULTS.chunk_size


async def handle_start_stream(
    body: StartStreamBody, inbound: MicrophoneInboundPort
) -> JSONResponse:
    """POST /start: open the capture. The answer carries the accepted configuration."""
    try:
        result = await inbound.start_stream(
            StartStreamInboundDTO(
                sample_rate=body.sample_rate,
                channels=body.channels,
                chunk_size=body.chunk_size,
            )
        )
    except Exception as error:
        return failure("start_stream", "Failed to start microphone stream", error)
    return success(
        "start_stream",
        "Microphone stream started successfully",
        MicrophoneConfig(sample_rate=result.sample_rate, channels=1, chunk_size=body.chunk_size),
    )
