from collections.abc import AsyncIterable, AsyncIterator

from domain.entities.utterance_segmenter import UtteranceSegmenter


async def utterances_of(
    chunks: AsyncIterable[bytes], segmenter: UtteranceSegmenter
) -> AsyncIterator[bytes]:
    """The utterances in a live capture, each as soon as the silence that ends it has passed.

    When the capture is closed, the utterance in progress is handed over too. When it fails, the
    error propagates and the half utterance is lost.
    """
    async for chunk in chunks:
        for utterance in segmenter.feed(chunk):
            yield utterance
    tail = segmenter.flush()
    if tail:
        yield tail
