"""Fitness function: the service and every adapter implement a port, and the ports are the contract.

    inbound adapter (MicrophoneHandler)   implements  MicrophoneInboundPort
    service (MicrophoneService)           implements  MicrophoneServicePort
    outbound adapters (capture, stream)   implement   AudioCapturePort / AudioStreamPort

A new inbound or outbound adapter implements the same port as the others, so its functions are the same.
"""

import ast
from pathlib import Path

import pytest

from application.ports.inbound.microphone_inbound_port import MicrophoneInboundPort
from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from application.ports.service.microphone_service_port import MicrophoneServicePort
from application.services.microphone_service import MicrophoneService
from infrastructure.inbound.http.http_handler import MicrophoneHandler
from infrastructure.outbound.sim_capture.sim_audio_capture import SimAudioCapture
from infrastructure.outbound.sim_capture.sim_audio_stream import SimAudioStream

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("component", "port"),
    [
        (MicrophoneService, MicrophoneServicePort),
        (MicrophoneHandler, MicrophoneInboundPort),
        (SimAudioCapture, AudioCapturePort),
        (SimAudioStream, AudioStreamPort),
    ],
)
def test_each_component_implements_its_port(component, port):
    assert issubclass(component, port)
    assert not component.__abstractmethods__, "a port operation is not implemented"


@pytest.mark.parametrize(
    ("port", "operations"),
    [
        (
            MicrophoneInboundPort,
            {"health", "check_device", "start_stream", "stop_stream", "current_stream"},
        ),
        (MicrophoneServicePort, {"start_stream", "stop_stream", "is_available", "current_stream"}),
        (AudioCapturePort, {"open_stream"}),
    ],
)
def test_the_port_is_the_contract(port, operations):
    assert port.__abstractmethods__ == operations


def _classes(package: str, suffix: str) -> list[tuple[str, ast.ClassDef]]:
    found = []
    for path in sorted((ROOT / "infrastructure" / package).rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.ClassDef) and node.name.endswith(suffix):
                found.append((f"{path.relative_to(ROOT)}:{node.name}", node))
    return found


def _base_names(node: ast.ClassDef) -> set[str]:
    return {base.id for base in node.bases if isinstance(base, ast.Name)}


def test_every_inbound_adapter_implements_the_inbound_port():
    adapters = _classes("inbound", "Handler")
    assert adapters, "no inbound adapter found"
    missing = [name for name, node in adapters if "MicrophoneInboundPort" not in _base_names(node)]
    assert not missing, f"inbound adapters that do not implement MicrophoneInboundPort: {missing}"


def test_every_capture_adapter_implements_the_capture_port():
    adapters = _classes("outbound", "AudioCapture")
    assert adapters, "no capture adapter found"
    missing = [name for name, node in adapters if "AudioCapturePort" not in _base_names(node)]
    assert not missing, f"capture adapters that do not implement AudioCapturePort: {missing}"


def test_every_stream_adapter_implements_the_stream_port():
    adapters = _classes("outbound", "AudioStream")
    assert adapters, "no stream adapter found"
    missing = [name for name, node in adapters if "AudioStreamPort" not in _base_names(node)]
    assert not missing, f"stream adapters that do not implement AudioStreamPort: {missing}"
