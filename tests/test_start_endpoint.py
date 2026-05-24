from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.dtos.services_dtos import (
    GetStreamResponseDto,
    MicrophoneAvailabilityResponseDto,
    StartMicrophoneStreamResponseDto,
    StopMicrophoneStreamResponseDto,
)
from infrastructure.inbound.http.fastapi_adapter import FastApiAdapter


async def _fake_audio_stream():
    yield b"pcm-bytes"


class FakeMicrophoneService:
    async def start_stream(self, request):
        return StartMicrophoneStreamResponseDto(
            stream=_fake_audio_stream(),
            sample_rate=request.sample_rate,
        )

    async def stop_stream(self, request):
        return StopMicrophoneStreamResponseDto(success=True)

    async def is_available(self, request):
        return MicrophoneAvailabilityResponseDto(is_available=True)

    def mic_stream(self, request):
        return GetStreamResponseDto(
            stream=_fake_audio_stream(),
            sample_rate=16000,
        )


def test_start_endpoint_streams_audio_bytes():
    app = FastAPI()
    FastApiAdapter(service_port=FakeMicrophoneService(), app=app)
    client = TestClient(app)

    with client.stream(
        "POST",
        "/start",
        json={"sample_rate": 16000, "channels": 1, "chunk_size": 1024},
    ) as response:
        body = response.read()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/octet-stream")
    assert response.headers["x-action"] == "start_stream"
    assert response.headers["x-sample-rate"] == "16000"
    assert body == b"pcm-bytes"
