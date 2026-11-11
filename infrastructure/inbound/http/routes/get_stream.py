from fastapi import status
from fastapi.responses import JSONResponse, StreamingResponse

from application.errors import FormatMismatch
from application.ports.inbound.microphone_inbound_port import MicrophoneInboundPort
from infrastructure.inbound.http.response.http_envelope import failure
from infrastructure.inbound.http.response.stream_events import (
    NDJSON_MEDIA_TYPE,
    ndjson_audio_events,
)
from infrastructure.inbound.http.response.stream_headers import stream_headers


async def handle_get_stream(
    inbound: MicrophoneInboundPort, sample_rate: int | None
) -> StreamingResponse | JSONResponse:
    """GET /stream: the event stream of the capture started with ``POST /start``.

    The format was fixed by ``/start``; ``sample_rate`` repeated here must match it.
    """
    try:
        result = inbound.current_stream()
        if sample_rate is not None and sample_rate != result.sample_rate:
            raise FormatMismatch(
                f"sample_rate={sample_rate} differs from the capture's {result.sample_rate}"
            )
    except Exception as error:
        return failure("get_stream", "Failed to retrieve microphone stream", error)
    return StreamingResponse(
        ndjson_audio_events(result.stream, result.sample_rate),
        media_type=NDJSON_MEDIA_TYPE,
        status_code=status.HTTP_200_OK,
        headers=stream_headers(
            "get_stream", "success", "Microphone stream retrieved successfully", result.sample_rate
        ),
    )
