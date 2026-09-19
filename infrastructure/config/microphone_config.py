import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class MicrophoneConfig:
    fallback_sample_rate: int
    target_keywords: tuple[str, ...]
    show_meter: bool

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "MicrophoneConfig":
        raw_keywords = env.get("MICROPHONE_TARGET_KEYWORDS", "")
        return cls(
            fallback_sample_rate=int(env.get("MICROPHONE_FALLBACK_SAMPLE_RATE", "16000")),
            target_keywords=tuple(k.strip() for k in raw_keywords.split(",") if k.strip()),
            show_meter=env.get("MICROPHONE_SHOW_METER", "true").lower() in {"1", "true", "yes"},
        )
