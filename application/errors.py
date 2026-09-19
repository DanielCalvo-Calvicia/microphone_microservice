class ApplicationError(Exception):
    """Base class for failures of a use case that are not business-rule violations."""


class MicrophoneUnavailable(ApplicationError):
    """No capture device or format could be opened."""


class StreamCloseFailed(ApplicationError, RuntimeError):
    """The device could not be released cleanly.

    Also a RuntimeError so callers written against the previous behaviour keep working.
    """
