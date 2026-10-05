import math
from array import array

from domain.operations.level import mean, rms, samples_of
from domain.operations.resample import LinearResampler
from domain.value_objects.input_treatment import InputTreatment

_DC_OFFSET_KEEP = 0.95  # the offset follows the signal slowly: 95% old value, 5% of each chunk mean
_NOISE_FLOOR_START_FACTOR = 3.0
_NOISE_FLOOR_END_FACTOR = 2.0


class UtteranceSegmenter:
    """Cuts a stream of PCM chunks into utterances.

    Feed it the chunks as they are captured; it hands back each utterance when the silence that
    ends it has lasted ``silence_limit_seconds``. An utterance starts when the volume reaches the
    start threshold and keeps the silence that ended it. Which treatments measure the volume is
    ``InputTreatment``'s business.
    """

    def __init__(self, treatment: InputTreatment, sample_rate: int) -> None:
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self._treatment = treatment
        self._rate = sample_rate
        self._limit_samples = math.ceil(treatment.silence_limit_seconds * sample_rate)
        self._resampler = (
            LinearResampler(sample_rate, treatment.resample_to_hz)
            if treatment.resample_to_hz and treatment.resample_to_hz != sample_rate
            else None
        )
        self._offset = 0.0
        self._smoothed = 0.0
        self._floor = math.inf
        self._speaking = False
        self._silent_samples = 0
        self._utterance = bytearray()

    @property
    def output_sample_rate(self) -> int:
        """The rate of the utterances this hands back."""
        return self._treatment.resample_to_hz if self._resampler is not None else self._rate

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def feed(self, chunk: bytes) -> list[bytes]:
        """Takes in one chunk; returns the utterances it finished (none, or one)."""
        samples = samples_of(chunk)
        if not samples:
            return []
        volume = self._measure(samples)
        start, end = self._thresholds()
        if not self._speaking and volume >= start:
            self._speaking = True
            self._silent_samples = 0
        if not self._speaking:
            return []
        resampler = self._resampler
        self._utterance.extend(resampler.process(chunk) if resampler is not None else chunk)
        self._silent_samples = self._silent_samples + len(samples) if volume < end else 0
        if self._silent_samples >= self._limit_samples:
            return [self._finish()]
        return []

    def flush(self) -> bytes | None:
        """The stream ended: the utterance in progress, if any."""
        return self._finish() if self._speaking else None

    def _measure(self, samples: "array[int]") -> int:
        treatment = self._treatment
        if treatment.dc_offset_removal:
            self._offset = self._offset * _DC_OFFSET_KEEP + mean(samples) * (1 - _DC_OFFSET_KEEP)
        raw = rms(samples, self._offset)
        if treatment.noise_floor_tracking and 0 < raw < self._floor:
            self._floor = raw
        if not treatment.volume_smoothing:
            return int(raw)
        weight = treatment.volume_smoothing_factor
        self._smoothed = self._smoothed * (1 - weight) + raw * weight
        return int(self._smoothed)

    def _thresholds(self) -> tuple[int, int]:
        """The volume that starts an utterance and the volume under which it is silent."""
        treatment = self._treatment
        start = int(treatment.silence_threshold * treatment.speech_start_factor)
        end = treatment.silence_threshold
        if treatment.noise_floor_tracking and self._floor != math.inf:
            start = max(start, int(self._floor * _NOISE_FLOOR_START_FACTOR))
            end = max(end, int(self._floor * _NOISE_FLOOR_END_FACTOR))
        return start, end

    def _finish(self) -> bytes:
        utterance = bytes(self._utterance)
        self._utterance.clear()
        self._speaking = False
        self._silent_samples = 0
        if self._resampler is not None:
            self._resampler.reset()
        return utterance
