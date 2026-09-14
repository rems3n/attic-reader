"""Accent placement helpers for paradigm generation.

Conventions
-----------
* Words are handled in NFC. Macrons (ᾱ ῑ ῡ) may be used *internally* to mark
  long vowels; `finish()` strips them before a form is shown to a learner.
* Unmarked α ι υ count as short unless the caller says otherwise.
* Syllables are counted from the end: 1 = ultima, 2 = penult, 3 = antepenult.
"""

from __future__ import annotations

import unicodedata

from greek_accentuation.characters import strip_length
from greek_accentuation.syllabify import syllabify

ACUTE = "́"
GRAVE = "̀"
CIRCUMFLEX = "͂"
MACRON = "̄"
BREVE = "̆"
IOTA_SUB = "ͅ"
ACCENTS = {ACUTE, GRAVE, CIRCUMFLEX}
VOWELS = "αεηιουω"
LONG_VOWELS = "ηω"
SHORT_VOWELS = "εο"
DIPHTHONGS = {"αι", "ει", "οι", "υι", "αυ", "ευ", "ου", "ηυ", "ωυ"}


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def nfd(text: str) -> str:
    return unicodedata.normalize("NFD", text)


def strip_accent(word: str) -> str:
    """Remove acute/grave/circumflex, keep breathing, macron and iota subscript."""
    return nfc("".join(ch for ch in nfd(word) if ch not in ACCENTS))


def finish(word: str) -> str:
    """Final learner-facing spelling: NFC, no macrons/breves."""
    return nfc(strip_length(nfd(word)))


def syllables(word: str) -> list[str]:
    return syllabify(nfc(word))


def _nucleus(syllable: str) -> tuple[str, set[str]]:
    """Base vowels of a syllable and the diacritics attached to them."""
    base = ""
    marks: set[str] = set()
    for ch in nfd(syllable):
        if ch in VOWELS:
            base += ch
        elif unicodedata.combining(ch) and base:
            marks.add(ch)
    return base, marks


def syllable_is_long(syllable: str, final: bool = False) -> bool:
    """Metrical vowel length for accent purposes (final -αι/-οι count short)."""
    base, marks = _nucleus(syllable)
    if not base:
        return False
    if MACRON in marks or CIRCUMFLEX in marks or IOTA_SUB in marks:
        return True
    if BREVE in marks:
        return False
    if len(base) >= 2:
        pair = base[-2:]
        # final -αι/-οι count short only when nothing follows them (λόγοι, χῶραι;
        # but λόγοις, χώραις are long)
        ends_open = nfd(syllable).rstrip("".join(chr(c) for c in range(0x300, 0x370))).endswith(tuple(VOWELS))
        if final and pair in {"αι", "οι"} and ends_open:
            return False
        if pair in DIPHTHONGS:
            return True
    return base[-1] in LONG_VOWELS


def accent_position(word: str) -> tuple[int, str] | None:
    """(syllable index from the end, accent kind) of an accented word, or None."""
    sylls = syllables(word)
    for i, syll in enumerate(reversed(sylls), start=1):
        _, marks = _nucleus(syll)
        if CIRCUMFLEX in marks:
            return i, "circumflex"
        if ACUTE in marks or GRAVE in marks:
            return i, "acute"
    return None


def _accent_syllable(syllable: str, kind: str) -> str:
    """Put an acute/circumflex on the syllable's vowel (second vowel of a diphthong)."""
    mark = CIRCUMFLEX if kind == "circumflex" else ACUTE
    chars = list(nfd(syllable))
    # find vowel positions
    vowel_idx = [i for i, ch in enumerate(chars) if ch in VOWELS]
    if not vowel_idx:
        return syllable
    # diphthong → accent on the second vowel; otherwise the (only/last) vowel
    target = vowel_idx[-1]
    if len(vowel_idx) >= 2:
        pair = chars[vowel_idx[-2]] + chars[vowel_idx[-1]]
        # a diaeresis on the second vowel means no diphthong
        after_second = chars[vowel_idx[-1] + 1 : vowel_idx[-1] + 3]
        if pair in DIPHTHONGS and "̈" not in after_second:
            target = vowel_idx[-1]
        else:
            target = vowel_idx[-1]
    # insert the accent after breathing/macron but before iota subscript
    j = target + 1
    while j < len(chars) and unicodedata.combining(chars[j]) and chars[j] != IOTA_SUB:
        j += 1
    chars.insert(j, mark)
    return nfc("".join(chars))


def accentuate(word: str, from_end: int, kind: str = "acute") -> str:
    """Accent `word` (accent-free or not) on the syllable `from_end` (1 = ultima)."""
    bare = strip_accent(word)
    sylls = syllables(bare)
    if from_end < 1 or from_end > len(sylls):
        from_end = min(max(from_end, 1), len(sylls))
    idx = len(sylls) - from_end
    sylls[idx] = _accent_syllable(sylls[idx], kind)
    return nfc("".join(sylls))


def persistent(form: str, from_start: int, ultima_kind: str = "acute") -> str:
    """Keep the accent on syllable `from_start` (0-based) if the law of
    limitation allows; otherwise move it forward. Chooses acute/circumflex
    from vowel length. `ultima_kind` is used when the accent ends on the ultima
    (gen./dat. of oxytones want a circumflex)."""
    bare = strip_accent(form)
    sylls = syllables(bare)
    n = len(sylls)
    from_end = n - from_start
    ultima_long = syllable_is_long(sylls[-1], final=True)
    if from_end > 3:
        from_end = 3
    if from_end == 3 and ultima_long:
        from_end = 2
    if from_end == 2:
        penult_long = syllable_is_long(sylls[-2])
        kind = "circumflex" if penult_long and not ultima_long else "acute"
    elif from_end == 1:
        kind = ultima_kind
        if kind == "circumflex" and not ultima_long:
            kind = "acute"
    else:
        kind = "acute"
    return accentuate(bare, from_end, kind)


def recessive(form: str) -> str:
    """Verb-style recessive accent: as far from the end as the ultima allows."""
    bare = strip_accent(form)
    sylls = syllables(bare)
    n = len(sylls)
    ultima_long = syllable_is_long(sylls[-1], final=True)
    if n >= 3 and not ultima_long:
        return accentuate(bare, 3, "acute")
    if n >= 2:
        penult_long = syllable_is_long(sylls[-2])
        return accentuate(bare, 2, "circumflex" if penult_long and not ultima_long else "acute")
    return accentuate(bare, 1, "circumflex" if ultima_long else "acute")


def accent_from_start(word: str) -> int:
    """0-based index (from the start) of the accented syllable of `word`."""
    pos = accent_position(word)
    n = len(syllables(word))
    if pos is None:
        return max(n - 1, 0)
    return n - pos[0]
