from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.service.microphone_service_port import MicrophoneServicePort
from application.services.microphone_service import MicrophoneService
from domain.value_objects.input_treatment import InputTreatment


def new_microphone_service(
    capture: AudioCapturePort, name: str, treatment: InputTreatment | None = None
) -> MicrophoneServicePort:
    return MicrophoneService(capture=capture, name=name, treatment=treatment)
