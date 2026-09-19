import importlib
import sys
import types

from fastapi.testclient import TestClient

from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig


def test_container_wires_an_app_that_answers_health(monkeypatch):
    monkeypatch.setitem(sys.modules, "sounddevice", types.ModuleType("sounddevice"))
    for name in (
        "infrastructure.outbound.sounddevice_capture.sounddevice_audio_stream",
        "infrastructure.outbound.sounddevice_capture.sounddevice_audio_capture",
        "composition_root.dependencies.microphone_dependencies",
        "composition_root.containers.http_container",
    ):
        monkeypatch.delitem(sys.modules, name, raising=False)
    module = importlib.import_module("composition_root.containers.http_container")

    container = module.new_http_container(ServerConfig.from_env({}), MicrophoneConfig.from_env({}))

    body = TestClient(container.app).get("/health").json()
    assert body["status"] == "success" and body["action"] == "health_check"
    assert container.microphone.is_available() is False
