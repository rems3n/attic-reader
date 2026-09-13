"""Word timings from Kokoro's per-token predicted durations.

Kokoro's duration predictor emits one integer frame count per input token
(BOS + one per phoneme character + EOS). The decoder upsamples frames to
audio at a fixed hop, so the boundary of each character in the audio is the
cumulative frame count scaled to samples. Word boundaries in our phoneme
strings are spaces (the G2P joins word IPA with the source text's gaps), and
Greek words in the source sentence appear in the same order, so word k of the
sentence ↔ the k-th space-separated phoneme token that contains a letter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..greek.g2p import GREEK_WORD_RE
from .kokoro import SAMPLE_RATE, has_speech

_TOKEN_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class WordTiming:
    start: int  # char offset of the word in the sentence text
    end: int
    t0: float  # seconds from the start of the sentence clip
    t1: float

    def as_dict(self) -> dict[str, float | int]:
        return {"start": self.start, "end": self.end, "t0": round(self.t0, 3), "t1": round(self.t1, 3)}


def char_boundaries(phonemes: str, pred_dur: list[int], n_samples: int) -> list[float] | None:
    """Seconds at which each character of ``phonemes`` starts, plus the end.

    ``pred_dur`` may or may not include the BOS/EOS tokens; both lengths are
    accepted. Returns None when the lengths cannot be reconciled.
    """
    n = len(phonemes)
    durs = [max(0, int(d)) for d in pred_dur]
    if len(durs) == n + 2:
        lead, body = durs[0], durs[1:-1]
    elif len(durs) == n:
        lead, body = 0, durs
    else:
        return None
    total = sum(durs)
    if total <= 0 or n_samples <= 0:
        return None
    seconds_per_frame = (n_samples / SAMPLE_RATE) / total
    bounds: list[float] = []
    acc = lead
    for d in body:
        bounds.append(acc * seconds_per_frame)
        acc += d
    bounds.append(acc * seconds_per_frame)
    return bounds


def token_spans(phonemes: str) -> list[tuple[int, int]]:
    """(start, end) char spans of space-separated tokens that carry speech."""
    return [(m.start(), m.end()) for m in _TOKEN_RE.finditer(phonemes) if has_speech(m.group(0))]


def align_words(
    sentence: str,
    chunks: list[tuple[str, list[int] | None, int]],
    pause_samples: int = 0,
) -> list[WordTiming] | None:
    """Map Greek words of ``sentence`` onto phoneme tokens across its chunks.

    ``chunks`` are ``(phonemes, pred_dur, n_samples)`` in render order, joined
    by ``pause_samples`` of silence. Returns None when any chunk lacks
    durations or the token/word counts disagree (no highlighting rather than
    a wrong one).
    """
    words = [(m.start(), m.end()) for m in GREEK_WORD_RE.finditer(sentence)]
    timings: list[WordTiming] = []
    offset = 0.0
    token_times: list[tuple[float, float]] = []
    for index, (phonemes, pred_dur, n_samples) in enumerate(chunks):
        if pred_dur is None:
            return None
        bounds = char_boundaries(phonemes, pred_dur, n_samples)
        if bounds is None:
            return None
        for start, end in token_spans(phonemes):
            token_times.append((offset + bounds[start], offset + bounds[end]))
        offset += n_samples / SAMPLE_RATE
        if index < len(chunks) - 1:
            offset += pause_samples / SAMPLE_RATE
    if len(token_times) != len(words):
        return None
    for (start, end), (t0, t1) in zip(words, token_times):
        timings.append(WordTiming(start, end, t0, t1))
    return timings
