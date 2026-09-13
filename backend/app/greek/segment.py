"""Sentence segmentation for polytonic Greek.

Splits on the Greek sentence-final marks (full stop, Greek question mark ``;``
or U+037E, ano teleia ``·``, ``!``, ``?``) and on newlines while preserving the
exact character span of every sentence in the *original* string, so a UI can
highlight or edit the source text without re-deriving offsets.

This module is orthography-level only. It knows nothing about phonemes or TTS
providers; per-sentence synthesis builds on it.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

# Characters that end a sentence. The Greek question mark is written as ";" or
# as U+037E; the ano teleia (U+00B7 / U+0387) marks a strong clause boundary and
# is treated as sentence-final for learner playback (one pause per clause).
TERMINATORS = frozenset(".;··;!?")

# Characters that may trail a terminator and still belong to the same sentence
# (closing quotes and brackets, repeated dots of an ellipsis).
TRAILING = frozenset("\"'”’»)]}›")

_WS_RE = re.compile(r"\s")


@dataclass(frozen=True)
class Sentence:
    index: int
    text: str
    start: int
    end: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    """Shrink [start, end) so it excludes leading/trailing whitespace."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def segment_sentences(text: str) -> list[Sentence]:
    """Return sentences with spans into ``text`` (``text[start:end] == sentence.text``)."""
    sentences: list[Sentence] = []
    n = len(text)
    seg_start = 0
    i = 0

    def flush(end: int) -> None:
        nonlocal seg_start
        s, e = _trim(text, seg_start, end)
        if e > s:
            sentences.append(Sentence(len(sentences), text[s:e], s, e))
        seg_start = end

    while i < n:
        ch = text[i]
        if ch == "\n" or ch == "\r":
            flush(i)
            i += 1
            seg_start = i
            continue
        if ch in TERMINATORS:
            j = i + 1
            # Absorb runs such as "..." or "?!" and closing quotes/brackets.
            while j < n and (text[j] in TERMINATORS or text[j] in TRAILING):
                j += 1
            flush(j)
            i = j
            continue
        i += 1

    flush(n)
    return sentences


def segment_sentences_dicts(text: str) -> list[dict[str, object]]:
    return [s.as_dict() for s in segment_sentences(text)]
