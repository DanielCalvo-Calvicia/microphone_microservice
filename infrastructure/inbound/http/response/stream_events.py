"""Frames a live PCM capture as the microphone's outbound stream contract (NDJSON events)."""

import base64
import time
from collections.abc import AsyncIterable, AsyncIterator

from contracts.stream.codec import EventSequencer, encode_ndjson
from contracts.stream.common.error import ErrorEvent, ErrorEventDTO
from contracts.stream.microservices.microphone.outbound.completed import (
    MicrophoneCompletedOutboundEvent,
    MicrophoneCompletedOutboundEventDTO,
)
from contracts.stream.microservices.microphone.outbound.stream_started import (
    MicrophoneStreamStartedEvent,
    MicrophoneStreamStartedEventDTO,
)
from contracts.stream.microservices.microphone.outbound.utterance import (
    MicrophoneUtteranceEvent,
    MicrophoneUtteranceEventDTO,
)
from shared_logging import get_logger

logger = get_logger(__name__)

NDJSON_MEDIA_TYPE = "application/x-ndjson"
CAPTURE_CHANNELS = 1  # the capture adapter always downmixes to mono int16


async def ndjson_audio_events(
    utterances: AsyncIterable[bytes], sample_rate: int
) -> AsyncIterator[bytes]:
    """``stream_started``, one ``utterance`` per finished utterance (PCM16 mono at ``sample_rate``),
    then ``completed`` (or ``error``).

    ``completed.output_bytes_base64`` is empty: an open-ended capture never accumulates its audio,
    the utterances already carried all of it.
    """
    events = EventSequencer()
    started_at = time.monotonic()
    yield encode_ndjson(
        events.next(
            MicrophoneStreamStartedEvent,
            MicrophoneStreamStartedEventDTO(
                message="Microphone stream started",
                sample_rate=sample_rate,
                channels=CAPTURE_CHANNELS,
            ),
        )
    )
    try:
        async for utterance in utterances:
            if utterance:
                yield encode_ndjson(
                    events.next(
                        MicrophoneUtteranceEvent,
                        MicrophoneUtteranceEventDTO(
                            bytes_base64=base64.b64encode(utterance).decode("ascii"),
                            sample_rate=sample_rate,
                        ),
                    )
                )
    except Exception as error:
        logger.error("Microphone capture failed mid-stream", error=error)
        yield encode_ndjson(
            events.next(
                ErrorEvent,
                ErrorEventDTO(code="capture_failed", message=str(error), recoverable=False),
            )
        )
        return
    logger.info(
        "Microphone stream completed", events=events.last, seconds=time.monotonic() - started_at
    )
    yield encode_ndjson(
        events.next(
            MicrophoneCompletedOutboundEvent,
            MicrophoneCompletedOutboundEventDTO(reason="completed", output_bytes_base64=""),
        )
    )
