"""The simulated capture backend (T-02.2): a generated signal, paced like a real device, through the same ports."""

import asyncio
import math
from array import array

import pytest

from application.dtos.inbound.start_stream_inbound import StartStreamInboundDTO
from application.services.microphone_service import MicrophoneService
from domain.value_objects.audio_format import AudioFormat
from infrastructure.outbound.sim_capture.sim_audio_capture import SimAudioCapture

RATE, CHUNK = 16000, 1024
CHUNK_SECONDS = CHUNK / RATE


class FakeClock:
    """A clock that only moves when somebody sleeps: no test waits for real time."""

    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def new_capture(clock: FakeClock, **kwargs: int) -> SimAudioCapture:
    return SimAudioCapture(sleep=clock.sleep, monotonic=clock.monotonic, **kwargs)


def rms(chunk: bytes) -> float:
    samples = array("h")
    samples.frombytes(chunk)
    return math.sqrt(sum(s * s for s in samples) / len(samples)) if samples else 0.0


async def read(stream, count: int) -> list[bytes]:
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
        if len(chunks) == count:
            break
    return chunks


def run(coro):
    return asyncio.run(coro)


def test_the_device_probe_says_it_is_simulated_and_available():
    ok, reason = run(SimAudioCapture().check_device())
    assert ok is True
    assert reason is not None and "sim" in reason.lower() and "MICROPHONE_BACKEND" in reason


def test_the_stream_has_the_requested_rate_and_chunk_size_and_is_mono_pcm16():
    async def scenario():
        stream = await new_capture(FakeClock()).open_stream(AudioFormat(8000, 1, 256))
        (chunk,) = await read(stream, 1)
        assert stream.sample_rate == 8000
        assert len(chunk) == 256 * 2

    run(scenario())


def test_a_stereo_request_still_gets_mono_audio():
    async def scenario():
        stream = await new_capture(FakeClock()).open_stream(AudioFormat(RATE, 2, CHUNK))
        (chunk,) = await read(stream, 1)
        assert len(chunk) == CHUNK * 2  # one channel: the same downmix the real device gives

    run(scenario())


def test_the_signal_is_room_noise_then_a_loud_tone_then_silence():
    async def scenario():
        stream = await new_capture(FakeClock(), quiet_chunks=3, tone_chunks=4).open_stream(
            AudioFormat(RATE, 1, CHUNK)
        )
        levels = [rms(chunk) for chunk in await read(stream, 12)]
        assert all(0 < level < 50 for level in levels[:3])  # room noise, but not silence
        assert all(level > 3000 for level in levels[3:7])  # the tone
        assert levels[7:] == [0.0] * 5  # then silence, and it stays silent

    run(scenario())


def test_the_stream_is_paced_to_real_time_one_chunk_duration_per_chunk():
    async def scenario():
        clock = FakeClock()
        start = clock.now
        stream = await new_capture(clock).open_stream(AudioFormat(RATE, 1, CHUNK))
        await read(stream, 10)
        assert clock.now - start == pytest.approx(10 * CHUNK_SECONDS)
        assert clock.sleeps == pytest.approx([CHUNK_SECONDS] * 10)

    run(scenario())


def test_a_slow_consumer_does_not_make_the_stream_drift():
    """The device keeps its own time: chunks that are already due are handed over at once, none is sleeping late."""

    async def scenario():
        clock = FakeClock()
        start = clock.now
        stream = await new_capture(clock).open_stream(AudioFormat(RATE, 1, CHUNK))
        await read(stream, 1)
        clock.now += 5 * CHUNK_SECONDS  # the consumer was busy for five chunks
        before = len(clock.sleeps)
        await read(stream, 3)
        assert len(clock.sleeps) == before  # the next chunks were already due: no sleep
        await read(stream, 3)
        assert clock.now - start == pytest.approx(
            7 * CHUNK_SECONDS
        )  # the 7th chunk is due at 7 chunk durations

    run(scenario())


def test_close_ends_the_iteration_is_idempotent_and_does_not_call_the_termination_callback():
    async def scenario():
        stream = await new_capture(FakeClock()).open_stream(AudioFormat(RATE, 1, CHUNK))
        fired: list[int] = []
        stream.on_terminated(lambda: fired.append(1))
        await read(stream, 2)
        await stream.close()
        await stream.close()
        assert [chunk async for chunk in stream] == []
        assert fired == []

    run(scenario())


def test_every_open_starts_the_pattern_again():
    async def scenario():
        capture = new_capture(FakeClock(), quiet_chunks=2, tone_chunks=2)
        first = [
            rms(c) for c in await read(await capture.open_stream(AudioFormat(RATE, 1, CHUNK)), 4)
        ]
        second = [
            rms(c) for c in await read(await capture.open_stream(AudioFormat(RATE, 1, CHUNK)), 4)
        ]
        assert first == second and first[2] > 3000

    run(scenario())


def test_through_the_service_the_pattern_comes_out_as_one_utterance_with_its_pre_roll():
    """The sim is a fake device, not a fake service: the real segmenter cuts it into exactly one utterance."""

    async def scenario():
        clock = FakeClock()
        service = MicrophoneService(new_capture(clock))
        out = await service.start_stream(StartStreamInboundDTO(RATE, 1, CHUNK))
        utterances = []
        async for utterance in out.stream:
            utterances.append(utterance)
            break
        await service.stop_stream()
        assert len(utterances) == 1
        seconds = len(utterances[0]) / 2 / out.sample_rate
        # 80 chunks of tone (5.1 s) plus the pre-roll (the quiet chunks before it) plus the trailing silence
        assert 80 * CHUNK_SECONDS < seconds < 80 * CHUNK_SECONDS + 8
        first_chunk = utterances[0][: CHUNK * 2]
        assert (
            0 < rms(first_chunk) < 50
        )  # it starts with the room noise heard before the tone (pre-roll)
        assert (
            clock.now - 100.0 > 80 * CHUNK_SECONDS
        )  # and it was paced: the whole pattern took its real duration

    run(scenario())


def test_a_consumer_that_goes_away_ends_the_stream_and_fires_the_callback_once():
    async def scenario():
        async def never_wakes(seconds: float) -> None:
            await asyncio.Event().wait()

        capture = SimAudioCapture(sleep=never_wakes, monotonic=FakeClock().monotonic)
        stream = await capture.open_stream(AudioFormat(RATE, 1, CHUNK))
        fired: list[int] = []
        stream.on_terminated(lambda: fired.append(1))
        task = asyncio.create_task(read(stream, 1))
        await asyncio.sleep(0)  # let it block on the first chunk
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert fired == [1]
        assert [chunk async for chunk in stream] == []
        await stream.close()
        assert fired == [1]

    run(scenario())


def test_a_stream_closed_while_waiting_for_a_chunk_ends_without_handing_it_over():
    async def scenario():
        holder = {}

        async def close_while_waiting(seconds: float) -> None:
            await holder["stream"].close()

        capture = SimAudioCapture(sleep=close_while_waiting, monotonic=FakeClock().monotonic)
        holder["stream"] = await capture.open_stream(AudioFormat(RATE, 1, CHUNK))
        assert [chunk async for chunk in holder["stream"]] == []

    run(scenario())


def test_a_close_followed_by_a_cancelled_read_is_not_a_termination():
    async def scenario():
        async def never_wakes(seconds: float) -> None:
            await asyncio.Event().wait()

        stream = await SimAudioCapture(
            sleep=never_wakes, monotonic=FakeClock().monotonic
        ).open_stream(AudioFormat(RATE, 1, CHUNK))
        fired: list[int] = []
        stream.on_terminated(lambda: fired.append(1))
        task = asyncio.create_task(read(stream, 1))
        await asyncio.sleep(0)
        await stream.close()  # an explicit close first ...
        task.cancel()  # ... then the reader goes away
        with pytest.raises(asyncio.CancelledError):
            await task
        assert fired == []

    run(scenario())


def test_the_termination_callback_fires_only_once_even_with_two_readers():
    async def scenario():
        async def never_wakes(seconds: float) -> None:
            await asyncio.Event().wait()

        stream = await SimAudioCapture(
            sleep=never_wakes, monotonic=FakeClock().monotonic
        ).open_stream(AudioFormat(RATE, 1, CHUNK))
        fired: list[int] = []
        stream.on_terminated(lambda: fired.append(1))
        tasks = [asyncio.create_task(read(stream, 1)) for _ in range(2)]
        await asyncio.sleep(0)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        assert fired == [1]

    run(scenario())


def test_the_tone_continues_in_phase_from_one_chunk_to_the_next():
    async def scenario():
        stream = await new_capture(FakeClock(), quiet_chunks=0, tone_chunks=3).open_stream(
            AudioFormat(RATE, 1, CHUNK)
        )
        chunks = await read(stream, 3)
        samples = array("h")
        samples.frombytes(b"".join(chunks))
        for n in (0, 1, CHUNK - 1, CHUNK, CHUNK + 1, 2 * CHUNK + 7):
            assert samples[n] == int(8000 * math.sin(2 * math.pi * 300 * n / RATE))

    run(scenario())
