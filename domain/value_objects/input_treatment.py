from dataclasses import dataclass

from domain.errors import InvalidInputTreatment


@dataclass(frozen=True, slots=True)
class InputTreatment:
    """How the microphone cuts what it hears into utterances.

    The cutting itself is always on (an utterance is what is said between two silences); each of
    the treatments below can be switched on or off on its own.

    Cutting:
      * ``silence_threshold`` is the volume (RMS of 16-bit samples) under which it is silent;
        ``silence_limit_seconds`` of silence end an utterance; speech starts at
        ``silence_threshold * speech_start_factor`` (1 = the same volume that counts as silence,
        a bigger factor makes a blip of noise less likely to start an utterance).

    Treatments of the signal:
      * ``dc_offset_removal``: subtract the slowly changing constant offset of the signal before
        measuring volume.
      * ``volume_smoothing``: measure a smoothed volume (``volume_smoothing_factor``, 0 to 1, is
        the weight of the newest chunk) instead of the raw volume of each chunk, so one loud click
        is not speech.
      * ``noise_floor_tracking``: remember the quietest volume heard and raise the thresholds above
        it (speech starts over 3 times the floor, silence is under 2 times), so a noisy room does
        not count as speech.
      * ``resample_to_hz``: the rate of the audio sent on (linear interpolation); 0 = keep the
        device rate.
    """

    silence_threshold: int = 150
    silence_limit_seconds: float = 2.0
    speech_start_factor: float = 2.0
    dc_offset_removal: bool = False
    volume_smoothing: bool = True
    volume_smoothing_factor: float = 0.1
    noise_floor_tracking: bool = True
    resample_to_hz: int = 0

    def __post_init__(self) -> None:
        if self.silence_threshold < 0:
            raise InvalidInputTreatment("silence_threshold must not be negative")
        if self.silence_limit_seconds <= 0:
            raise InvalidInputTreatment("silence_limit_seconds must be positive")
        if self.speech_start_factor < 1:
            raise InvalidInputTreatment("speech_start_factor must be at least 1")
        if not 0 < self.volume_smoothing_factor <= 1:
            raise InvalidInputTreatment(
                "volume_smoothing_factor must be between 0 (excluded) and 1"
            )
        if self.resample_to_hz < 0:
            raise InvalidInputTreatment("resample_to_hz must not be negative")
