"""Cancelling the microphone stream over a real socket must reach the capture device.

ASGI test transports cannot model a client that walks away mid-stream, so this runs the real
application under uvicorn and disconnects a real HTTP client.
"""

import asyncio
import socket
import threading
import time
from collections.abc import Iterator

import httpx
import pytest
import uvicorn
from contracts.stream.codec import iter_events
from contracts.stream.common.base import EventType
from contracts.stream.schemas import MICROPHONE_OUTBOUND
from fastapi import FastAPI

from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from application.services.microphone_service import MicrophoneService
from domain.value_objects.audio_format import AudioFormat
from infrastructure.inbound.http.http_handler import MicrophoneHandler


class EndlessStream(AudioStreamPort):
    """Captures forever; remembers when the consumer went away."""

    def __init__(self, sample_rate: int) -> None:
        self._sample_rate = sample_rate
        self.chunks_read = 0
        self.cancelled = threading.Event()

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def __aiter__(self):
        return self

    async def __anext__(self) -> bytes:
        try:
            await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            self.cancelled.set()
            raise
        self.chunks_read += 1
        return b"\x01\x00" * 160

    def on_terminated(self, callback) -> None:
        pass

    async def close(self) -> None:
        pass


class Capture(AudioCapturePort):
    def __init__(self) -> None:
        self.stream: EndlessStream | None = None

    async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
        self.stream = EndlessStream(audio_format.sample_rate)
        return self.stream


@pytest.fixture
def running() -> Iterator[tuple[str, Capture]]:
    capture = Capture()
    app = FastAPI()
    app.include_router(MicrophoneHandler(MicrophoneService(capture)).router)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None, lifespan="off")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        assert time.monotonic() < deadline, "server did not start"
        time.sleep(0.01)
    yield f"http://127.0.0.1:{port}", capture
    server.should_exit = True
    thread.join(timeout=10)


def test_events_flow_in_order_and_a_client_that_disconnects_cancels_the_capture(
    running: tuple[str, Capture],
) -> None:
    base_url, capture = running

    async def run() -> list[EventType]:
        async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
            assert (await client.post("/start", json={"sample_rate": 16000})).status_code == 200
            seen: list[EventType] = []
            async with client.stream("GET", "/stream") as response:
                async for event in iter_events(response.aiter_bytes(), MICROPHONE_OUTBOUND):
                    seen.append(event.type)
                    if len(seen) == 4:
                        break  # the consumer walks away mid-stream
            return seen

    seen = asyncio.run(run())

    assert seen == [EventType.START_STREAM, EventType.PARTIAL, EventType.PARTIAL, EventType.PARTIAL]
    assert capture.stream is not None
    assert capture.stream.cancelled.wait(timeout=5), "the disconnect never reached the capture iterator"
