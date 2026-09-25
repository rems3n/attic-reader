"""Answer normalization, mirrored by the frontend grader (parity fixtures in
tests/test_course.py → frontend/lib/normalize.fixtures.json).

Two modes:

* lenient (the default until Unit 4): accents, macrons, breves, the iota
  subscript and the *smooth* breathing are ignored; the *rough* breathing is
  kept (ὁ ≠ ὀ, but ἀ = α); final sigma is unified; case, spacing and
  surrounding punctuation are ignored.
* strict: the same, but accents, the iota subscript and both breathings
  count. A grave is treated as an acute, so ``καλὸς ἄνθρωπος`` matches
  ``καλός ἄνθρωπος``.

Answers may use the ``(ν)`` convention for movable ν; ``expand_movable``
turns one such answer into both surface forms.
"""

from __future__ import annotations

import re
import unicodedata

ACUTE = "́"
GRAVE = "̀"
CIRCUMFLEX = "͂"
MACRON = "̄"
BREVE = "̆"
IOTA_SUB = "ͅ"
DIAERESIS = "̈"
SMOOTH = "̓"
ACCENTS = {ACUTE, GRAVE, CIRCUMFLEX}
DROPPED_ALWAYS = {MACRON, BREVE, DIAERESIS}

_PUNCT = re.compile(r"[.,;·!?:«»\"“”‘’'()\[\]{}—–\-…]+")
_SPACES = re.compile(r"\s+")
_GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def expand_movable(answer: str) -> list[str]:
    """``ἐστί(ν)`` → ``["ἐστίν", "ἐστί"]``; other strings unchanged."""
    if "(ν)" not in answer:
        return [answer]
    return [answer.replace("(ν)", "ν"), answer.replace("(ν)", "")]


def normalize_answer(text: str, accents: bool = False) -> str:
    """Canonical comparison key for a typed Greek answer."""
    s = unicodedata.normalize("NFD", (text or "").lower())
    out: list[str] = []
    for ch in s:
        if ch in DROPPED_ALWAYS:
            continue
        if ch in ACCENTS:
            if accents:
                out.append(ACUTE if ch == GRAVE else ch)
            continue
        if ch in {IOTA_SUB, SMOOTH} and not accents:
            continue
        out.append(ch)
    s = "".join(out).replace("ς", "σ")
    s = _PUNCT.sub(" ", s)
    s = _SPACES.sub(" ", s).strip()
    return unicodedata.normalize("NFC", s)


def answers_match(given: str, accepted: list[str], accents: bool = False) -> bool:
    key = normalize_answer(given, accents)
    if not key:
        return False
    for answer in accepted:
        for variant in expand_movable(answer):
            if normalize_answer(variant, accents) == key:
                return True
    return False


def tokens(text: str) -> list[str]:
    """Greek word tokens of a sentence: punctuation stripped, elision mark kept."""
    out = []
    for raw in text.split():
        tok = raw.strip(".,;·!?:«»\"“”()[]{}—–…")
        if tok and _GREEK.search(tok):
            out.append(tok)
    return out
