"""MICROPHONE_BACKEND picks the capture adapter before the sounddevice driver is imported (T-02.3, ADR-007)."""

import importlib
import sys
import types

import pytest
from fastapi.testclient import TestClient

from infrastructure.config.microphone_config import MicrophoneConfig
from infrastructure.config.server_config import ServerConfig

REAL_ADAPTER_PACKAGE = "infrastructure.outbound.sounddevice_capture"


def fresh_container_module(monkeypatch: pytest.MonkeyPatch, sounddevice):
    """Re-import the composition root as if the process had just started, with ``sounddevice`` as given."""
    monkeypatch.setitem(sys.modules, "sounddevice", sounddevice)
    for name in list(sys.modules):
        if name.startswith(("composition_root", REAL_ADAPTER_PACKAGE)):
            monkeypatch.delitem(sys.modules, name)
    return importlib.import_module("composition_root.containers.http_container")


def build(module, **env: str):
    return module.new_http_container(
        ServerConfig.from_env({}), MicrophoneConfig.from_env(dict(env))
    )


def test_sim_starts_with_sounddevice_unimportable_and_nothing_imports_it(monkeypatch):
    module = fresh_container_module(
        monkeypatch, None
    )  # `import sounddevice` now raises ImportError
    with pytest.raises(ImportError):
        import sounddevice  # noqa: F401

    container = build(module, MICROPHONE_BACKEND="sim")

    client = TestClient(container.app)
    assert client.get("/health").json()["status"] == "success"
    assert not any(name.startswith(REAL_ADAPTER_PACKAGE) for name in sys.modules)


def test_sim_answers_available_true_and_says_it_is_simulated(monkeypatch):
    module = fresh_container_module(monkeypatch, None)
    container = build(module, MICROPHONE_BACKEND="sim")

    data = TestClient(container.app).get("/available").json()["data"]

    assert data["is_available"] is True
    assert "sim" in data["reason"].lower() and "MICROPHONE_BACKEND" in data["reason"]


def test_real_is_the_default_and_needs_the_sounddevice_module(monkeypatch):
    module = fresh_container_module(monkeypatch, None)
    with pytest.raises(ImportError):
        build(module)  # nothing set: the real adapter, which needs PortAudio's module
    with pytest.raises(ImportError):
        build(module, MICROPHONE_BACKEND="real")


def test_real_does_not_report_a_reason_and_is_built_from_the_driver_module(monkeypatch):
    stub = types.ModuleType("sounddevice")
    module = fresh_container_module(monkeypatch, stub)
    container = build(module, MICROPHONE_BACKEND="real")
    assert container.microphone.is_available() is False
    assert any(name.startswith(REAL_ADAPTER_PACKAGE) for name in sys.modules)


class RecordingLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []

    def warning(self, message: str, **fields: object) -> None:
        self.records.append(("warning", message))

    def info(self, message: str, **fields: object) -> None:
        self.records.append(("info", message))


def test_sim_is_announced_once_at_start_with_a_warning_and_real_logs_nothing_new(monkeypatch):
    from composition_root.dependencies import audio_capture_dependency as deps

    recorder = RecordingLogger()
    monkeypatch.setattr(deps, "logger", recorder)
    monkeypatch.setitem(sys.modules, "sounddevice", types.ModuleType("sounddevice"))

    deps.new_audio_capture(MicrophoneConfig.from_env({"MICROPHONE_BACKEND": "sim"}))
    assert recorder.records == [("warning", "Microphone backend is simulated")]

    recorder.records.clear()
    deps.new_audio_capture(MicrophoneConfig.from_env({}))
    assert recorder.records == []


def test_the_sim_wiring_builds_the_adapter_with_the_documented_pattern(monkeypatch):
    from composition_root.dependencies import audio_capture_dependency as deps
    from infrastructure.outbound.sim_capture.sim_audio_capture import (
        QUIET_CHUNKS,
        TONE_CHUNKS,
        SimAudioCapture,
    )

    capture = deps.new_audio_capture(MicrophoneConfig.from_env({"MICROPHONE_BACKEND": "sim"}))

    assert isinstance(capture, SimAudioCapture)
    assert (QUIET_CHUNKS, TONE_CHUNKS) == (
        5,
        80,
    )  # the pattern of the seed: 0.3 s of noise, 5 s of tone
    assert (capture._quiet_chunks, capture._tone_chunks) == (QUIET_CHUNKS, TONE_CHUNKS)
