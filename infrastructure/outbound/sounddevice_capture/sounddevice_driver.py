"""The only module that imports ``sounddevice``."""

from typing import Any, cast

import sounddevice as sd

from domain.value_objects.audio_format import AudioFormat
from infrastructure.outbound.sounddevice_capture.audio_driver import DeviceInfo, RawInput


def _to_info(index: int, raw: Any) -> DeviceInfo:
    rate = raw.get("default_samplerate")
    return DeviceInfo(
        index=index,
        name=str(raw.get("name")),
        max_input_channels=int(raw.get("max_input_channels", 0)),
        default_samplerate=int(rate) if rate is not None else None,
    )


class SoundDeviceDriver:
    def input_devices(self) -> list[DeviceInfo]:
        return [_to_info(index, raw) for index, raw in enumerate(sd.query_devices())]

    def default_input_index(self) -> int | None:
        default_input = sd.default.device[0]
        return None if default_input is None else int(default_input)

    def device_info(self, index: int) -> DeviceInfo:
        return _to_info(index, sd.query_devices(index))

    def open_input(self, index: int, audio_format: AudioFormat) -> RawInput:
        raw_stream: Any = sd.RawInputStream(
            samplerate=audio_format.sample_rate,
            blocksize=audio_format.chunk_size,
            device=index,
            channels=audio_format.channels,
            dtype="int16",
        )
        try:
            raw_stream.start()
        except Exception:
            raw_stream.close()
            raise
        return cast(RawInput, raw_stream)
