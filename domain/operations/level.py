import math
from array import array


def samples_of(pcm: bytes) -> "array[int]":
    """The 16-bit samples of ``pcm`` (a trailing odd byte is ignored)."""
    samples: array[int] = array("h")
    samples.frombytes(pcm[: len(pcm) - len(pcm) % 2])
    return samples


def mean(samples: "array[int]") -> float:
    return sum(samples) / len(samples) if samples else 0.0


def rms(samples: "array[int]", offset: float = 0.0) -> float:
    """The volume of ``samples``: root of the mean square after subtracting ``offset`` from each."""
    if not samples:
        return 0.0
    if offset:
        return math.sqrt(sum((sample - offset) ** 2 for sample in samples) / len(samples))
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))
