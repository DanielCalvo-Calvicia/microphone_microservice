import os
from collections.abc import Mapping
from dataclasses import dataclass

from domain.value_objects.input_treatment import InputTreatment

_TRUE = {"1", "true", "yes", "on"}


def _flag(env: Mapping[str, str], name: str, default: bool) -> bool:
    value = env.get(name, "").strip().lower()
    return default if value == "" else value in _TRUE


@dataclass(slots=True, frozen=True)
class MicrophoneConfig:
    fallback_sample_rate: int
    target_keywords: tuple[str, ...]
    show_meter: bool
    treatment: InputTreatment

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "MicrophoneConfig":
        raw_keywords = env.get("MICROPHONE_TARGET_KEYWORDS", "")
        return cls(
            fallback_sample_rate=int(env.get("MICROPHONE_FALLBACK_SAMPLE_RATE", "16000")),
            target_keywords=tuple(k.strip() for k in raw_keywords.split(",") if k.strip()),
            show_meter=env.get("MICROPHONE_SHOW_METER", "true").lower() in {"1", "true", "yes"},
            treatment=cls._treatment_from(env),
        )

    @staticmethod
    def _treatment_from(env: Mapping[str, str]) -> InputTreatment:
        defaults = InputTreatment()

        def number(name: str, default: float) -> float:
            raw = env.get(name, "").strip()
            return float(raw) if raw else default

        return InputTreatment(
            silence_threshold=int(
                number("MICROPHONE_SILENCE_THRESHOLD", defaults.silence_threshold)
            ),
            silence_limit_seconds=number(
                "MICROPHONE_SILENCE_LIMIT_SECONDS", defaults.silence_limit_seconds
            ),
            speech_start_factor=number(
                "MICROPHONE_SPEECH_START_FACTOR", defaults.speech_start_factor
            ),
            dc_offset_removal=_flag(
                env, "MICROPHONE_DC_OFFSET_REMOVAL", defaults.dc_offset_removal
            ),
            volume_smoothing=_flag(env, "MICROPHONE_VOLUME_SMOOTHING", defaults.volume_smoothing),
            volume_smoothing_factor=number(
                "MICROPHONE_VOLUME_SMOOTHING_FACTOR", defaults.volume_smoothing_factor
            ),
            noise_floor_tracking=_flag(
                env, "MICROPHONE_NOISE_FLOOR_TRACKING", defaults.noise_floor_tracking
            ),
            resample_to_hz=int(number("MICROPHONE_RESAMPLE_TO_HZ", defaults.resample_to_hz)),
        )
