from application.errors import FormatMismatch, MicrophoneUnavailable
from domain.errors import CaptureAlreadyActive, CaptureNotActive, InvalidAudioFormat
from infrastructure.inbound.http.http_error_mapper import map_error


def test_errors_map_to_natural_statuses():
    assert map_error(CaptureAlreadyActive("x")) == 409
    assert map_error(CaptureNotActive("x")) == 409
    assert map_error(InvalidAudioFormat("x")) == 422
    assert map_error(FormatMismatch("x")) == 422
    assert map_error(MicrophoneUnavailable("x")) == 503
    assert map_error(RuntimeError("x")) == 500
