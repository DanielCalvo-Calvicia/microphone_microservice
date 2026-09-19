from array import array

SAMPLE_WIDTH_BYTES = 2  # 16-bit signed PCM, native byte order


def downmix_to_mono(pcm: bytes, channels: int) -> bytes:
    """Average interleaved 16-bit PCM channels into a single mono channel.

    Each output sample is the arithmetic mean of one frame, truncated toward zero.
    """
    if channels < 1:
        raise ValueError("channels must be >= 1")
    if channels == 1:
        return pcm
    if len(pcm) % (SAMPLE_WIDTH_BYTES * channels) != 0:
        raise ValueError("PCM buffer is not a whole number of frames")

    samples = array("h")
    samples.frombytes(pcm)
    frames = zip(*[iter(samples)] * channels)
    return array("h", (int(sum(frame) / channels) for frame in frames)).tobytes()
