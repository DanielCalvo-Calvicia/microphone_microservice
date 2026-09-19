from domain.errors import CaptureAlreadyActive, InvalidAudioFormat
from infrastructure.inbound.http.http_error_mapper import map_error


def test_every_error_currently_maps_to_500():
    assert map_error(CaptureAlreadyActive("x")) == 500
    assert map_error(InvalidAudioFormat("x")) == 500
    assert map_error(RuntimeError("x")) == 500
