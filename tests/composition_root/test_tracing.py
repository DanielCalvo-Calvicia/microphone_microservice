import importlib
import sys
import types

from fastapi.testclient import TestClient
from shared_logging.testing import capture

from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig

TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
TRACEPARENT = f"00-{TRACE_ID}-b7ad6b7169203331-01"


def _app(monkeypatch):
    monkeypatch.setitem(sys.modules, "sounddevice", types.ModuleType("sounddevice"))
    for name in (
        "infrastructure.outbound.sounddevice_capture.sounddevice_audio_stream",
        "infrastructure.outbound.sounddevice_capture.sounddevice_audio_capture",
        "composition_root.dependencies.microphone_dependencies",
        "composition_root.containers.http_container",
    ):
        monkeypatch.delitem(sys.modules, name, raising=False)
    module = importlib.import_module("composition_root.containers.http_container")
    return module.new_http_container(ServerConfig.from_env({}), MicrophoneConfig.from_env({})).app


def test_incoming_trace_is_continued_and_logged_with_the_service_name(monkeypatch):
    client = TestClient(_app(monkeypatch))

    with capture("microphone") as logs:
        response = client.get("/health", headers={"traceparent": TRACEPARENT})

    assert response.status_code == 200
    assert response.headers["x-trace-id"] == TRACE_ID
    request_logs = [r for r in logs.records if r["logger"] == "shared_logging.http"]
    assert request_logs and {r["trace_id"] for r in request_logs} == {TRACE_ID}
    assert {r["service"] for r in logs.records} == {"microphone"}


def test_request_without_a_trace_starts_a_new_one(monkeypatch):
    client = TestClient(_app(monkeypatch))

    with capture("microphone"):
        response = client.get("/health")

    assert len(response.headers["x-trace-id"]) == 32
