from application.errors import MicrophoneUnavailable, StreamCloseFailed


def map_open_error(error: Exception) -> MicrophoneUnavailable:
    return MicrophoneUnavailable(f"Could not open a microphone stream: {error}")


def map_close_error(error: Exception) -> StreamCloseFailed:
    return StreamCloseFailed(f"Failed to stop microphone stream: {error}")
