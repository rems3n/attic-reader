"""Small, testable Classical Attic grapheme-to-phoneme MVP.

This module intentionally avoids a neural model. Rules are explicit so they can be
reviewed against a chosen reconstructed pronunciation and changed independently of
TTS. Accent is currently rendered as learner-friendly stress rather than historical
pitch accent.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .normalize import normalize_polytonic

GREEK_WORD_RE = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]+", re.UNICODE)

ACUTE = "\u0301"
GRAVE = "\u0300"
CIRCUMFLEX = "\u0342"
SMOOTH = "\u0313"
ROUGH = "\u0314"
IOTA_SUBSCRIPT = "\u0345"
DIAERESIS = "\u0308"
MACRON = "\u0304"
BREVE = "\u0306"

VOWELS = set("αεηιουω")

SINGLE = {
    "α": "a",
    "ε": "e",
    "η": "ɛː",
    "ι": "i",
    "ο": "o",
    "υ": "y",
    "ω": "ɔː",
    "β": "b",
    "γ": "g",
    "δ": "d",
    "ζ": "zd",
    "θ": "tʰ",
    "κ": "k",
    "λ": "l",
    "μ": "m",
    "ν": "n",
    "ξ": "ks",
    "π": "p",
    "ρ": "r",
    "σ": "s",
    "ς": "s",
    "τ": "t",
    "φ": "pʰ",
    "χ": "kʰ",
    "ψ": "ps",
}

# Approximate late-5th/4th-c. Attic learner target. These are deliberately
# centralized because ει/ου and long diphthongs are period-sensitive.
DIPHTHONGS = {
    "αι": "ai̯",
    "ει": "eː",
    "οι": "oi̯",
    "υι": "yi̯",
    "αυ": "au̯",
    "ευ": "eu̯",
    "ηυ": "ɛːu̯",
    "ου": "uː",
}

PUNCT = {
    ",": ",",
    ".": ".",
    ";": "?",
    "·": ",",
    ":": ":",
    "!": "!",
    "?": "?",
    "—": "—",
    "-": "-",
}


@dataclass(frozen=True)
class Grapheme:
    base: str
    marks: frozenset[str]

    @property
    def rough(self) -> bool:
        return ROUGH in self.marks

    @property
    def accented(self) -> bool:
        return bool({ACUTE, GRAVE, CIRCUMFLEX} & self.marks)

    @property
    def diaeresis(self) -> bool:
        return DIAERESIS in self.marks

    @property
    def iota_subscript(self) -> bool:
        return IOTA_SUBSCRIPT in self.marks

    @property
    def long_alpha_iota(self) -> bool:
        return self.base in {"α", "ι", "υ"} and MACRON in self.marks


def _graphemes(word: str) -> list[Grapheme]:
    nfd = unicodedata.normalize("NFD", word.lower())
    out: list[Grapheme] = []
    for ch in nfd:
        if unicodedata.combining(ch):
            if out:
                prior = out[-1]
                out[-1] = Grapheme(prior.base, prior.marks | {ch})
            continue
        out.append(Grapheme(ch, frozenset()))
    return out


def _word_ipa(word: str) -> str:
    gs = _graphemes(word)
    phonemes: list[str] = []
    stress_target: int | None = None
    i = 0

    while i < len(gs):
        g = gs[i]
        nxt = gs[i + 1] if i + 1 < len(gs) else None

        pair = g.base + nxt.base if nxt else ""
        pair_is_diphthong = (
            nxt is not None
            and g.base in VOWELS
            and nxt.base in VOWELS
            and pair in DIPHTHONGS
            and not nxt.diaeresis
        )

        # In polytonic spelling, the breathing on an initial diphthong is written
        # over the second vowel (e.g. αἱ), but applies to the whole onset.
        if g.rough or (pair_is_diphthong and nxt is not None and nxt.rough):
            phonemes.append("h")

        if pair_is_diphthong:
            if g.accented or nxt.accented:
                stress_target = len(phonemes)
            phonemes.append(DIPHTHONGS[pair])
            i += 2
            continue

        if g.accented:
            stress_target = len(phonemes)

        # Gamma nasal before another velar.
        if g.base == "γ" and nxt and nxt.base in {"γ", "κ", "χ", "ξ"}:
            phonemes.append("ŋ")
            i += 1
            continue

        sound = SINGLE.get(g.base)
        if sound is None:
            phonemes.append(g.base)
        else:
            if g.long_alpha_iota and sound in {"a", "i", "y"}:
                sound += "ː"
            # For the MVP we pronounce subscript/adscript iota in a conservative
            # learner reconstruction. This policy is isolated for easy revision.
            if g.iota_subscript and g.base in {"α", "η", "ω"}:
                sound += "i̯"
            phonemes.append(sound)
        i += 1

    # Mark lexical accent as stress for the learner mode. Historical pitch-accent
    # rendering will be a separate mode later.
    if stress_target is not None and stress_target < len(phonemes):
        phonemes[stress_target] = "ˈ" + phonemes[stress_target]

    return "".join(phonemes)


def attic_ipa(text: str) -> str:
    text = normalize_polytonic(text)
    pieces: list[str] = []
    pos = 0

    for match in GREEK_WORD_RE.finditer(text):
        if match.start() > pos:
            gap = text[pos : match.start()]
            pieces.append("".join(PUNCT.get(c, c) for c in gap))
        pieces.append(_word_ipa(match.group(0)))
        pos = match.end()

    if pos < len(text):
        pieces.append("".join(PUNCT.get(c, c) for c in text[pos:]))

    ipa = "".join(pieces)
    ipa = re.sub(r"\s+", " ", ipa).strip()
    return ipa
