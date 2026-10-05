from array import array

from domain.operations.level import samples_of


class LinearResampler:
    """Converts 16-bit mono PCM from one rate to another by linear interpolation, chunk by chunk.

    State is kept between chunks, so cutting a stream into chunks at any place gives exactly the
    same output as converting it whole (positions are exact fractions, so nothing drifts);
    ``reset`` starts a new, independent stream.
    """

    def __init__(self, from_hz: int, to_hz: int) -> None:
        if from_hz <= 0 or to_hz <= 0:
            raise ValueError("both rates must be positive")
        self._from = from_hz
        self._to = to_hz
        self._last: int | None = None  # the last input sample of the previous chunk
        # where the next output sample is: input samples after ``_last``, times ``to_hz``
        self._position = 0

    def reset(self) -> None:
        self._last = None
        self._position = 0

    def process(self, pcm: bytes) -> bytes:
        incoming = samples_of(pcm)
        if not incoming:
            return b""
        source: list[int] | array[int]
        if self._last is None:
            source = incoming
            position = 0
        else:
            source = [self._last, *incoming]
            position = self._position
        output: array[int] = array("h")
        limit = (len(source) - 1) * self._to  # the last position that has a next sample to use
        while position < limit:
            index, remainder = divmod(position, self._to)
            low = source[index]
            output.append(low + (source[index + 1] - low) * remainder // self._to)
            position += self._from
        self._last = source[-1]
        self._position = position - limit
        return output.tobytes()
