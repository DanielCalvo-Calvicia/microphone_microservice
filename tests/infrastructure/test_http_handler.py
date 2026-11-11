import base64

import pytest
from contracts.stream.codec import NdjsonDecoder
from contracts.stream.common.base import EventType
from contracts.stream.schemas import MICROPHONE_OUTBOUND
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from application.services.microphone_service import MicrophoneService
from domain.value_objects.audio_format import AudioFormat
from domain.value_objects.input_treatment import InputTreatment
from infrastructure.inbound.http.http_handler import MicrophoneHandler


class FiniteStream(AudioStreamPort):
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

    def on_terminated(self, callback) -> None:
        pass

    async def close(self) -> None:
        pass


class FakePort(AudioCapturePort):
    async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
        return FiniteStream(audio_format.sample_rate)


@pytest.fixture
def client():
    app = FastAPI()
    # the fake capture is loud from its first chunk, which noise-floor tracking would take for the room's noise
    treatment = InputTreatment(volume_smoothing=False, noise_floor_tracking=False)
    app.include_router(MicrophoneHandler(MicrophoneService(FakePort(), treatment=treatment)).router)
    return TestClient(app)


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "success" and body["action"] == "health_check" and body["data"] == {"healthy": True}


def test_available_means_a_usable_device_even_before_start(client):
    body = client.get("/available").json()
    assert body["status"] == "success" and body["data"] == {"is_available": True, "reason": None}


def test_start_then_available_then_stop(client):
    started = client.post("/start", json={"sample_rate": 8000, "channels": 1, "chunk_size": 256})
    assert started.status_code == 200
    assert started.json()["data"]["sample_rate"] == 8000  # MicrophoneConfig

    assert client.get("/available").json()["data"] == {"is_available": True, "reason": None}

    stopped = client.post("/stop")
    assert stopped.status_code == 200 and stopped.json()["data"] is True
    assert client.get("/available").json()["data"] == {"is_available": True, "reason": None}


def test_start_uses_defaults_for_missing_fields(client):
    assert client.post("/start", json={}).json()["data"]["sample_rate"] == 16000


def test_start_twice_returns_error_envelope(client):
    client.post("/start", json={})
    response = client.post("/start", json={})
    body = response.json()
    assert response.status_code == 409  # wrong state
    assert body["status"] == "error" and body["action"] == "start_stream"
    assert "already started" in body["data"]


def test_invalid_parameters_return_error_envelope(client):
    response = client.post("/start", json={"sample_rate": 0})
    assert response.status_code == 422
    assert response.json()["status"] == "error"


def _decode_stream(body: bytes):
    decoder = NdjsonDecoder(MICROPHONE_OUTBOUND)
    return [*decoder.feed(body), *decoder.finish()]


def test_stream_speaks_the_microphone_outbound_contract(client):
    client.post("/start", json={"sample_rate": 22050})
    response = client.get("/stream")
    assert response.status_code == 200
    assert response.headers["x-sample-rate"] == "22050"
    assert response.headers["content-type"].startswith("application/x-ndjson")

    events = _decode_stream(response.content)  # raises ContractViolation on any drift
    assert [event.type for event in events] == [
        EventType.START_STREAM,
        EventType.UTTERANCE,
        EventType.COMPLETED,
    ]
    assert [event.sequence for event in events] == [1, 2, 3]
    started = events[0].payload
    assert (started.sample_rate, started.channels) == (22050, 1)
    utterance = events[1].payload
    assert utterance.sample_rate == 22050
    assert base64.b64decode(utterance.bytes_base64) == b"abcd" * 3  # the 3 loud chunks are one utterance
    assert events[-1].payload.reason == "completed"


def test_capture_failure_mid_stream_is_reported_as_an_error_event():
    class FailingStream(FiniteStream):
        def __aiter__(self):
            async def gen():
                yield b"abcd"
                raise RuntimeError("device unplugged")

            return gen()

    class FailingCapture(AudioCapturePort):
        async def open_stream(self, audio_format: AudioFormat) -> AudioStreamPort:
            return FailingStream(audio_format.sample_rate)

    app = FastAPI()
    app.include_router(MicrophoneHandler(MicrophoneService(FailingCapture())).router)
    with TestClient(app) as failing_client:
        failing_client.post("/start", json={"sample_rate": 16000})
        events = _decode_stream(failing_client.get("/stream").content)

    assert [event.type for event in events] == [EventType.START_STREAM, EventType.ERROR]  # the utterance in progress is lost
    assert events[-1].payload.code == "capture_failed"
    assert "device unplugged" in events[-1].payload.message
    assert events[-1].payload.recoverable is False


def test_stream_when_idle_returns_error_envelope(client):
    response = client.get("/stream")
    assert response.status_code == 409
    assert response.json()["action"] == "get_stream"
    assert response.json()["status"] == "error"


def test_stop_when_idle_succeeds(client):
    assert client.post("/stop").json()["status"] == "success"


def test_stream_with_a_sample_rate_that_differs_from_the_capture_is_a_422(client):
    client.post("/start", json={"sample_rate": 22050})

    mismatch = client.get("/stream?sample_rate=16000")
    same = client.get("/stream?sample_rate=22050")

    assert mismatch.status_code == 422 and "sample_rate=16000" in mismatch.json()["message"]
    assert same.status_code == 200


def test_available_reports_why_the_device_is_unusable():
    class NoDevice(AudioCapturePort):
        async def open_stream(self, audio_format):
            raise AssertionError("must not be opened")

        async def check_device(self):
            return False, "Selected device has no input channels."

    app = FastAPI()
    app.include_router(MicrophoneHandler(MicrophoneService(NoDevice())).router)
    body = TestClient(app).get("/available").json()

    assert body["data"] == {"is_available": False, "reason": "Selected device has no input channels."}
