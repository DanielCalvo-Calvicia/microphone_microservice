from fastapi import status

from application.errors import FormatMismatch, MicrophoneUnavailable
from domain.errors import CaptureAlreadyActive, CaptureNotActive, InvalidAudioFormat


def map_error(error: Exception) -> int:
    """Translate an application/domain error into an HTTP status code.

    409  wrong state: capture already active / not active
    422  the requested audio format is invalid or contradicts the active capture
    503  no usable input device
    500  anything else (device read/close failures)
    """
    if isinstance(error, (CaptureAlreadyActive, CaptureNotActive)):
        return status.HTTP_409_CONFLICT
    if isinstance(error, (InvalidAudioFormat, FormatMismatch)):
        return status.HTTP_422_UNPROCESSABLE_CONTENT
    if isinstance(error, MicrophoneUnavailable):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    return status.HTTP_500_INTERNAL_SERVER_ERROR
