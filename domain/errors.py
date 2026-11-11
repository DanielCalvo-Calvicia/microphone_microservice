"""Domain errors.

They also inherit from the matching builtin exception so that callers written
against the pre-refactor behaviour (``ValueError`` / ``RuntimeError``) keep working.
"""


class DomainError(Exception):
    """Base class for every business-rule violation raised by the domain."""


class InvalidAudioFormat(DomainError, ValueError):
    """The requested audio format violates an invariant (e.g. non-positive rate)."""


class CaptureAlreadyActive(DomainError, RuntimeError):
    """The microphone is already capturing; it must be stopped first."""


class CaptureNotActive(DomainError, RuntimeError):
    """The operation requires an active capture but the microphone is idle."""


class InvalidInputTreatment(DomainError, ValueError):
    """A setting of the input treatment is out of range (e.g. a negative silence threshold)."""
