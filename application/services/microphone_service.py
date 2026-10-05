import asyncio

from shared_logging import get_logger

from application.dtos.start_stream_inbound import StartStreamInboundDTO
from application.dtos.stream_outbound import StreamOutboundDTO
from application.ports.inbound.microphone_streaming_port import MicrophoneStreamingPort
from application.ports.outbound.audio_capture_port import AudioCapturePort
from application.ports.outbound.audio_stream_port import AudioStreamPort
from application.services.utterance_stream import utterances_of
from domain.entities.microphone import Microphone
from domain.entities.utterance_segmenter import UtteranceSegmenter
from domain.errors import CaptureNotActive
from domain.value_objects.audio_format import AudioFormat
from domain.value_objects.input_treatment import InputTreatment

logger = get_logger(__name__)


class MicrophoneService(MicrophoneStreamingPort):
    """Orchestrates the microphone use cases. Business rules live in the domain.

    The stream it hands out is not the raw capture: it is the capture cut into utterances
    (``UtteranceSegmenter``, treated as ``treatment`` says), one item per finished utterance, at
    the sample rate of ``StreamOutboundDTO``.
    """

    def __init__(
        self,
        capture: AudioCapturePort,
        name: str = "Microphone",
        treatment: InputTreatment | None = None,
    ) -> None:
        self.name = name
        self._capture = capture
        self._treatment = treatment or InputTreatment()
        self._microphone = Microphone()
        self._stream: AudioStreamPort | None = None
        self._utterances: StreamOutboundDTO | None = None
        # start/stop are read-modify-write sequences that await the device.
        self._lock = asyncio.Lock()
        logger.info("MicrophoneService initialized", name=name)

    async def start_stream(self, request: StartStreamInboundDTO) -> StreamOutboundDTO:
        requested = AudioFormat(
            sample_rate=request.sample_rate,
            channels=request.channels,
            chunk_size=request.chunk_size,
        )
        async with self._lock:
            self._microphone.ensure_idle()
            stream = await self._capture.open_stream(requested)
            self._microphone.start(requested.with_sample_rate(stream.sample_rate))
            self._stream = stream
            segmenter = UtteranceSegmenter(self._treatment, stream.sample_rate)
            self._utterances = StreamOutboundDTO(
                sample_rate=segmenter.output_sample_rate, stream=utterances_of(stream, segmenter)
            )
            stream.on_terminated(lambda: self._handle_stream_terminated(stream))
        logger.info(
            "Microphone stream started",
            device_sample_rate=stream.sample_rate,
            sample_rate=self._utterances.sample_rate,
        )
        return self._utterances

    async def stop_stream(self) -> None:
        async with self._lock:
            if not self._microphone.is_capturing or self._stream is None:
                return
            await self._stream.close()  # StreamCloseFailed propagates; capture stays active
            self._stream = None
            self._utterances = None
            self._microphone.stop()
        logger.info("Microphone stream stopped")

    async def check_device(self) -> tuple[bool, str | None]:
        return await self._capture.check_device()

    def is_available(self) -> bool:
        return self._microphone.is_capturing

    def current_stream(self) -> StreamOutboundDTO:
        if self._utterances is None or not self._microphone.is_capturing:
            raise CaptureNotActive("Microphone stream is not active")
        return self._utterances

    def _handle_stream_terminated(self, stream: AudioStreamPort) -> None:
        """The stream died on its own (device failure or consumer gone); go back to idle."""
        if self._stream is not stream:
            return
        logger.warning("Microphone stream terminated unexpectedly; capture is idle again")
        self._stream = None
        self._utterances = None
        self._microphone.stop()
