import sys
from typing import Optional, AsyncIterator
import sounddevice as sd
import asyncio

# Import your new DTO here
from application.dtos.adapter_outbound_dtos import (
    InitOutboundAdapterDto,
    StartMicrophoneStreamRequestDto,
    StartMicrophoneStreamResponseDto,
    StopMicrophoneStreamRequestDto,
    StopMicrophoneStreamResponseDto,
    MicrophoneAvailabilityRequestDto,
    MicrophoneAvailabilityResponseDto,
    GetStreamRequestDto,
    GetStreamResponseDto
)
from application.ports.adapter_outbound_port import AdapterOutboundPort

import numpy as np

class SoundDeviceAsyncStream(AsyncIterator[bytes]):

    def __init__(self, stream: sd.RawInputStream, chunk_size: int, input_channels: int = 1):
        self._stream = stream
        self._chunk_size = chunk_size
        self._input_channels = input_channels
        self._closed = False
        print(
            "[audio-stream] Initialized "
            f"chunk_size={chunk_size}, input_channels={input_channels}, "
            f"stream_active={getattr(stream, 'active', 'unknown')}"
        )

        # Telemetry counters
        self._chunk_count: int = 0
        self._total_bytes: int = 0
        self._overflow_count: int = 0

    def __aiter__(self):
        print("[audio-stream] __aiter__ called")
        return self

    async def __anext__(self) -> bytes:
        if self._closed:
            print("[audio-stream] __anext__ called after closed; stopping iteration")
            raise StopAsyncIteration

        try:
            print(f"[audio-stream] Reading chunk #{self._chunk_count + 1}")
            data, overflowed = await asyncio.to_thread(
                self._stream.read, 
                self._chunk_size
            )
            print(
                f"[audio-stream] Raw read returned overflowed={overflowed}, "
                f"bytes={len(bytes(data))}"
            )

            chunk = bytes(data)

            # Convert stereo -> mono without audioop
            if self._input_channels > 1:
                print(f"[audio-stream] Downmixing {self._input_channels} channels to mono")
                samples = np.frombuffer(chunk, dtype=np.int16)

                # Reshape into [frames, channels]
                samples = samples.reshape(-1, self._input_channels)

                # Mix down channels (equivalent to 0.5, 0.5)
                mono = samples.mean(axis=1)

                # Convert back to int16 PCM bytes
                chunk = mono.astype(np.int16).tobytes()

            # ── Telemetry (every chunk, single-line overwrite) ──
            self._chunk_count += 1
            self._total_bytes += len(chunk)
            if overflowed:
                self._overflow_count += 1

            self._log_telemetry(chunk, overflowed)

            return chunk

        except asyncio.CancelledError:
            print("[audio-stream] Streaming response was cancelled by client/server")
            self._closed = True
            raise
        except Exception as error:
            print(f"\n  Microphone stream read failed: {error!r}")
            self._closed = True
            raise StopAsyncIteration

    def _log_telemetry(self, chunk: bytes, overflowed: bool) -> None:
        """Overwrite a single console line with live audio telemetry."""
        samples = np.frombuffer(chunk, dtype=np.int16)

        # RMS volume (root mean square)
        rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))

        # Convert RMS to dB (relative to int16 max = 32767)
        rms_db = 20 * np.log10(rms / 32767) if rms > 0 else -float("inf")

        # Peak amplitude
        peak = int(np.max(np.abs(samples)))

        # Visual volume bar (0–30 chars)
        bar_len = min(30, int((rms / 32767) * 30 * 5))  # x5 gain for visibility
        bar = "█" * bar_len + "░" * (30 - bar_len)

        overflow_flag = " ⚠ OVF" if overflowed else ""

        line = (
            f"\r  🎤 #{self._chunk_count:<6}  "
            f"|{bar}|  "
            f"RMS: {rms:>7.1f} ({rms_db:>6.1f} dB)  "
            f"Peak: {peak:>5}  "
            f"{len(chunk):>5}B"
            f"{overflow_flag}"
        )

        # Pad with spaces to clear any leftover characters from previous line
        sys.stdout.write(line.ljust(120))
        sys.stdout.flush()

    async def close(self):
        print(f"[audio-stream] close requested closed={self._closed}")
        if not self._closed:
            # Move to a new line so the close summary doesn't overwrite the live meter
            print(
                f"\n  🎤 Stream closed  |  "
                f"total chunks: {self._chunk_count}  |  "
                f"total bytes: {self._total_bytes}  |  "
                f"overflows: {self._overflow_count}"
            )
        self._closed = True


class MicrophoneAdapter(AdapterOutboundPort):

    default_fallback_rate: int
    target_keywords: list[str]

    started = False
    mic_sample_rate: Optional[int] = None
    mic_chunk_size: Optional[int] = None
    mic_channels: Optional[int] = None

    device_index: Optional[int] = None
    audio_stream: Optional[sd.RawInputStream] = None

    loop_stream: Optional[SoundDeviceAsyncStream] = None
    _mic_stream: Optional[AsyncIterator[bytes]] = None

    # --- UPDATED INIT TO ACCEPT THE DTO ---
    def __init__(self, config: InitOutboundAdapterDto):
        super().__init__()

        # Store configuration primitives internally
        self.default_fallback_rate = config.default_fallback_rate
        self.target_keywords = config.target_keywords
        print(
            "[outbound] MicrophoneAdapter initialized "
            f"default_fallback_rate={self.default_fallback_rate}, "
            f"target_keywords={self.target_keywords}"
        )

    @property
    def sample_rate(self) -> int:
        if self.mic_sample_rate is None:
            print("[outbound] sample_rate requested but no stream is active")
            raise RuntimeError("Microphone sample rate is not available")
        print(f"[outbound] sample_rate requested value={self.mic_sample_rate}")
        return self.mic_sample_rate

    @property
    def chunk_size(self) -> int:
        if self.mic_chunk_size is None:
            print("[outbound] chunk_size requested but no stream is active")
            raise RuntimeError("Microphone chunk size is not available")
        print(f"[outbound] chunk_size requested value={self.mic_chunk_size}")
        return self.mic_chunk_size

    async def start_stream(self, request: StartMicrophoneStreamRequestDto) -> StartMicrophoneStreamResponseDto:
        print(
            "[outbound] start_stream received "
            f"sample_rate={request.sample_rate}, channels={request.channels}, "
            f"chunk_size={request.chunk_size}, started={self.started}"
        )
        if request.sample_rate <= 0 or request.channels <= 0 or request.chunk_size <= 0:
            print("[outbound] start_stream rejected invalid parameters")
            raise ValueError("Invalid microphone stream parameters")
        
        if self.started:
            print("[outbound] start_stream rejected because stream is already started")
            raise RuntimeError("Microphone stream already started")
        
        self.mic_sample_rate = request.sample_rate
        self.mic_channels = request.channels
        self.mic_chunk_size = request.chunk_size

        try:
            print("[outbound] Finding microphone device")
            self.device_index = self.find_microphone_index()
            print(f"Using microphone device index: {self.device_index}")
            
            device_info = sd.query_devices(self.device_index)
            print(f"[outbound] Selected device info: {device_info}")
            # Use our DTO fallback setting if default_samplerate is missing
            default_rate = int(device_info.get('default_samplerate', self.default_fallback_rate))
            
            if self.mic_sample_rate != default_rate:
                print(f"  Warning: Requested rate {self.mic_sample_rate}Hz may not be supported.")
                print(f"  Device default: {default_rate}Hz")
                
        except Exception as e:
            print(f"Error finding microphone: {e}")
            raise RuntimeError("No microphone devices available")

        try:
            print(
                "[outbound] Opening RawInputStream "
                f"samplerate={self.mic_sample_rate}, blocksize={self.mic_chunk_size}, "
                f"device={self.device_index}, channels={self.mic_channels}, dtype=int16"
            )
            self.audio_stream = sd.RawInputStream(
                samplerate=self.mic_sample_rate,
                blocksize=self.mic_chunk_size,
                device=self.device_index,
                channels=self.mic_channels,
                dtype='int16'
            )
            self.audio_stream.start()
            print(f"[outbound] RawInputStream started active={self.audio_stream.active}")
        except Exception as e:
            print(f"  Failed to open at {self.mic_sample_rate}Hz. Retrying with hardware default {default_rate}Hz...")
            self.mic_sample_rate = default_rate
            try:
                print(
                    "[outbound] Retrying RawInputStream with hardware default "
                    f"samplerate={self.mic_sample_rate}, blocksize={self.mic_chunk_size}, "
                    f"device={self.device_index}, channels={self.mic_channels}, dtype=int16"
                )
                self.audio_stream = sd.RawInputStream(
                    samplerate=self.mic_sample_rate,
                    blocksize=self.mic_chunk_size,
                    device=self.device_index,
                    channels=self.mic_channels,
                    dtype='int16'
                )
                self.audio_stream.start()
                print(f"[outbound] RawInputStream retry started active={self.audio_stream.active}")
            except Exception as e2:
                if self.mic_channels == 1:
                    print(f"  Mono failed. Retrying with Stereo (2 channels)...")
                    self.mic_channels = 2
                    print(
                        "[outbound] Retrying RawInputStream in stereo "
                        f"samplerate={self.mic_sample_rate}, blocksize={self.mic_chunk_size}, "
                        f"device={self.device_index}, channels={self.mic_channels}, dtype=int16"
                    )
                    self.audio_stream = sd.RawInputStream(
                        samplerate=self.mic_sample_rate,
                        blocksize=self.mic_chunk_size,
                        device=self.device_index,
                        channels=self.mic_channels,
                        dtype='int16'
                    )
                    self.audio_stream.start()
                    print(f"[outbound] Stereo RawInputStream started active={self.audio_stream.active}")
                else:
                    print(f"[outbound] RawInputStream retry failed: {e2!r}")
                    raise e2

        print("[outbound] Creating async stream wrapper")
        self.loop_stream = SoundDeviceAsyncStream(
            stream=self.audio_stream,
            chunk_size=self.mic_chunk_size,
            input_channels=self.mic_channels
        )
        self._mic_stream = self.loop_stream
        self.started = True
        print(
            "[outbound] Runtime state set "
            f"started={self.started}, device_index={self.device_index}, "
            f"sample_rate={self.mic_sample_rate}, chunk_size={self.mic_chunk_size}, "
            f"channels={self.mic_channels}"
        )
        
        print(f"  Microphone successfully started:")
        print(f"    - Device Index: {self.device_index}")
        print(f"    - Sample Rate: {self.mic_sample_rate}Hz")
        print(f"    - Channels: {self.mic_channels} ({'Mono' if self.mic_channels==1 else 'Stereo'})")
        print(f"    - Chunk Size: {self.mic_chunk_size} frames")

        return StartMicrophoneStreamResponseDto(
            stream=self.loop_stream,
            sample_rate=self.mic_sample_rate,
        )

    async def stop_stream(self, request: StopMicrophoneStreamRequestDto) -> StopMicrophoneStreamResponseDto:
        print(f"[outbound] stop_stream received started={self.started}")
        if not self.started:
            print("[outbound] stop_stream no active stream; returning success")
            return StopMicrophoneStreamResponseDto(success=True)
        try:
            if self.loop_stream is not None:
                print("[outbound] Closing async stream wrapper")
                await self.loop_stream.close()
                self.loop_stream = None
                self._mic_stream = None

            if self.audio_stream is not None:
                print(f"[outbound] Closing RawInputStream active={self.audio_stream.active}")
                if self.audio_stream.active:
                    print("[outbound] Stopping RawInputStream")
                    self.audio_stream.stop()
                print("[outbound] Closing RawInputStream")
                self.audio_stream.close()
                self.audio_stream = None

            print("[outbound] Clearing runtime state")
            self.started = False
            self.device_index = None
            self.mic_sample_rate = None
            self.mic_chunk_size = None
            self.mic_channels = None

            print("[outbound] stop_stream completed")
            return StopMicrophoneStreamResponseDto(success=True)
        except Exception as error:
            print(f"[outbound] stop_stream failed: {error!r}")
            raise RuntimeError(f"Failed to stop microphone stream: {error}") from error

    async def is_available(self, request: MicrophoneAvailabilityRequestDto) -> MicrophoneAvailabilityResponseDto:
        print(f"[outbound] is_available requested started={self.started}")
        return MicrophoneAvailabilityResponseDto(is_available=self.started)

    def mic_stream(self, request: GetStreamRequestDto) -> GetStreamResponseDto:
        print(
            "[outbound] mic_stream requested "
            f"started={self.started}, has_stream={self._mic_stream is not None}, "
            f"sample_rate={self.mic_sample_rate}"
        )
        if not self.started or self._mic_stream is None:
            print("[outbound] mic_stream rejected because stream is not active")
            raise RuntimeError("Microphone stream is not active")
        print("[outbound] mic_stream returning active stream")
        return GetStreamResponseDto(
            stream=self._mic_stream,
            sample_rate=self.mic_sample_rate if self.mic_sample_rate is not None else self.default_fallback_rate
        )

    def find_microphone_index(self) -> int:
        """Programmatically find the best microphone index"""
        devices = sd.query_devices()
        print(f"[outbound] Scanning for microphones; devices_found={len(devices)}")
        
        for i, info in enumerate(devices):
            if int(info.get('max_input_channels', 0)) > 0:
                name: str = str(info.get('name'))
                channels = int(info.get('max_input_channels', 0))
                default_rate = info.get('default_samplerate', 'unknown')
                print(
                    f"[outbound] Found input device id={i}, name={name!r}, "
                    f"max_input_channels={channels}, default_samplerate={default_rate}"
                )
                
                # Uses the keywords parsed directly from our DTO
                if any(key.lower() in name.lower() for key in self.target_keywords):
                    print(f"[outbound] Auto-selected keyword match name={name!r}, id={i}")
                    return i

        try:
            default_input = sd.default.device[0]
            print(f"[outbound] No keyword match; OS default input index={default_input}")
            if default_input is not None:
                default_info = sd.query_devices(default_input)
                print(f"[outbound] Using default input device name={default_info['name']!r}")
                return default_input
            else:
                raise RuntimeError("No default input device configured in OS")
        except Exception:
            print("[outbound] Warning: No microphones found at all")
            raise RuntimeError("No microphone devices available")
