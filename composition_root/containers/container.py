import logging
from dataclasses import dataclass

from composition_root.dependencies.microphone_dependency import (
    MicrophoneDependency,
    generate_microphone_dependency,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class Container:
    microphone_dependency: MicrophoneDependency


def BuildContainer(name: str) -> Container:
    logger.info("Building dependency container for %r", name)
    microphone_dependency = generate_microphone_dependency(
        default_fallback_rate=16000,
        target_keywords=(),
    )
    return Container(microphone_dependency=microphone_dependency)
