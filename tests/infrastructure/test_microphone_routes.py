import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.ports.microphone_port import AudioStream, MicrophonePort
from application.services.microphone_service import MicrophoneService
from domain.value_objects.audio_format import AudioFormat
from infrastructure.inbound.http.routes.microphone_routes import build_microphone_router


class FiniteStream(AudioStream):
    def __init__(self, sample_rate: int):
        self._sample_rate = sample_rate

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def __aiter__(self):
        async def gen():
            for _ in range(3):
                yield b"abcd"
        return gen()

    async def close(self) -> None:
        pass


class FakePort(MicrophonePort):
    async def open_stream(self, audio_format: AudioFormat) -> AudioStream:
        return FiniteStream(audio_format.sample_rate)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(build_microphone_router(MicrophoneService(FakePort())))
    return TestClient(app)


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "success" and body["action"] == "health_check" and body["data"] is None


def test_available_is_false_before_start(client):
    body = client.get("/available").json()
    assert body["status"] == "success" and body["data"] is False


def test_start_then_available_then_stop(client):
    started = client.post("/start", json={"sample_rate": 8000, "channels": 1, "chunk_size": 256})
    assert started.status_code == 200
    assert started.json()["data"] == {"sample_rate": 8000}

    assert client.get("/available").json()["data"] is True

    stopped = client.post("/stop")
    assert stopped.status_code == 200 and stopped.json()["data"] is True
    assert client.get("/available").json()["data"] is False


def test_start_uses_defaults_for_missing_fields(client):
    assert client.post("/start", json={}).json()["data"] == {"sample_rate": 16000}


def test_start_twice_returns_error_envelope(client):
    client.post("/start", json={})
    response = client.post("/start", json={})
    body = response.json()
    assert response.status_code == 500
    assert body["status"] == "error" and body["action"] == "start_stream"
    assert "already started" in body["data"]


def test_invalid_parameters_return_error_envelope(client):
    response = client.post("/start", json={"sample_rate": 0})
    assert response.status_code == 500
    assert response.json()["status"] == "error"


def test_stream_returns_audio_bytes_and_headers(client):
    client.post("/start", json={"sample_rate": 22050})
    response = client.get("/stream")
    assert response.status_code == 200
    assert response.content == b"abcd" * 3
    assert response.headers["x-sample-rate"] == "22050"
    assert response.headers["content-type"] == "application/octet-stream"


def test_stream_when_idle_returns_error_envelope(client):
    response = client.get("/stream")
    assert response.status_code == 500
    assert response.json()["action"] == "get_stream"
    assert response.json()["status"] == "error"


def test_stop_when_idle_succeeds(client):
    assert client.post("/stop").json()["status"] == "success"
