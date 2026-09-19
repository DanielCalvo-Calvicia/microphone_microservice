from fastapi import status


def map_error(error: Exception) -> int:
    """Translate an application/domain error into an HTTP status code.

    Behaviour-preserving default: every failure is 500, exactly as before the refactor.
    To adopt the natural mapping (decision D4), add:
        InvalidAudioFormat      -> 422
        CaptureAlreadyActive    -> 409
        CaptureNotActive        -> 409
        MicrophoneUnavailable   -> 503
    """
    return status.HTTP_500_INTERNAL_SERVER_ERROR
