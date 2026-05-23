from dataclasses import dataclass

from composition_root.dependencies.microphone_dependency import (
    generate_microphone_dependency,
    MicrophoneDependency
)

@dataclass(slots=True, frozen=True)
class Container:
    microphone_dependency: MicrophoneDependency

def BuildContainer(name: str):
    print(f"[container] Building dependency container for {name!r}")
    microphone_dependency = generate_microphone_dependency(
        default_fallback_rate=16000,
        target_keywords=[]
    )

    print("[container] Dependency container built")
    return Container(
        microphone_dependency=microphone_dependency
    )
