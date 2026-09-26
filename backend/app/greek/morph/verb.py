"""Complete conjugation of Classical Attic verbs from their principal parts.

Pipeline: principal parts (DCC) → tense stems (augment/reduplication removed,
compound prefixes recognised) → forms from the ending tables in
`verb_endings.py` with recessive accent unless the ending fixes it → contraction
for -άω/-έω/-όω presents and contract futures. Irregular verbs (εἰμί, εἶμι,
φημί, οἶδα …) are spelled out in `verb_tables.py`.

Output: {"kind": "verb", "lemma", "principal_parts", "class", "notes", "systems":
  [{"id", "label", "tables": [{"tense", "voice", "mood", "cells": [{"tag", "forms"}]}]}]}
"""

from __future__ import annotations

import re
import unicodedata

from . import verb_endings as E
from . import verb_tables as T
from .accent import (
    ACUTE,
    CIRCUMFLEX,
    VOWELS,
    accent_position,
    accentuate,
    finish,
    nfc,
    nfd,
    recessive,
    strip_accent,
    syllable_is_long,
    syllables,
)

SMOOTH = "̓"
ROUGH = "̔"

# canonical prefix → (before a consonant, before a smooth vowel, before a rough vowel)
PREFIX_SHAPES: dict[str, tuple[str, str, str]] = {
    "ἀπο": ("ἀπο", "ἀπ", "ἀφ"), "κατα": ("κατα", "κατ", "καθ"), "παρα": ("παρα", "παρ", "παρ"),
    "δια": ("δια", "δι", "δι"), "ἐπι": ("ἐπι", "ἐπ", "ἐφ"), "ὑπο": ("ὑπο", "ὑπ", "ὑφ"),
    "ὑπερ": ("ὑπερ", "ὑπερ", "ὑπερ"), "περι": ("περι", "περι", "περι"), "προσ": ("προσ", "προσ", "προσ"),
    "προ": ("προ", "προ", "προ"), "συν": ("συν", "συν", "συν"), "ἐκ": ("ἐκ", "ἐξ", "ἐξ"),
    "εἰσ": ("εἰσ", "εἰσ", "εἰσ"), "ἐν": ("ἐν", "ἐν", "ἐν"), "ἀνα": ("ἀνα", "ἀν", "ἀν"),
    "μετα": ("μετα", "μετ", "μεθ"), "ἀντι": ("ἀντι", "ἀντ", "ἀνθ"), "ἀμφι": ("ἀμφι", "ἀμφ", "ἀμφ"),
}
# every surface form → canonical
PREFIX_SURFACE: dict[str, str] = {}
for _canon, _shapes in PREFIX_SHAPES.items():
    for _sh in _shapes:
        PREFIX_SURFACE.setdefault(_sh, _canon)
for _sh, _canon in {"συμ": "συν", "συγ": "συν", "συλ": "συν", "συ": "συν", "ἐμ": "ἐν", "ἐγ": "ἐν", "ἐξ": "ἐκ", "καθ": "κατα", "ἀφ": "ἀπο"}.items():
    PREFIX_SURFACE.setdefault(_sh, _canon)
PREFIXES = sorted(PREFIX_SURFACE, key=len, reverse=True)
PREFIX_VARIANTS = {sh: [PREFIX_SHAPES[c][1], PREFIX_SHAPES[c][2]] for sh, c in PREFIX_SURFACE.items()}


def prefix_before(canon: str, following: str) -> str:
    """Shape of a prefix before `following` (a stem, possibly with breathing)."""
    cons, smooth, rough = PREFIX_SHAPES[canon]
    d = nfd(following)
    if not d or d[0] not in VOWELS:
        first = d[:1]
        if canon == "συν":
            if first in "πβφμψ":
                return "συμ"
            if first in "κγχξ":
                return "συγ"
            if first == "λ":
                return "συλ"
            if first == "σ" and len(d) > 1 and d[1] not in VOWELS:
                return "συ"
        if canon == "ἐν":
            if first in "πβφμψ":
                return "ἐμ"
            if first in "κγχξ":
                return "ἐγ"
        return cons
    return rough if ROUGH in d[:3] else smooth


def attach_prefix(canon: str, stem: str) -> str:
    """Prefix + stem, dropping the now word-internal breathing of the stem."""
    if not canon:
        return stem
    shape = prefix_before(canon, stem)
    d = nfd(stem)
    d = "".join(ch for i, ch in enumerate(d) if not (ch in (SMOOTH, ROUGH) and i < 4))
    return nfc(shape + d)

# augment of an initial vowel: short → long
AUGMENT_VOWEL = {"α": "η", "ε": "η", "ο": "ω", "ι": "ῑ", "υ": "ῡ", "αι": "ῃ", "ει": "ῃ", "οι": "ῳ", "αυ": "ηυ", "ευ": "ηυ"}


def _has_accent(s: str) -> bool:
    return accent_position(s) is not None


def _breathing(word: str) -> str:
    d = nfd(word)
    for ch in d[:3]:
        if ch in (SMOOTH, ROUGH):
            return ch
    return SMOOTH


def _starts_with_vowel(word: str) -> bool:
    return nfd(word)[:1] in VOWELS


def _is_diphthong(a: str, b: str) -> bool:
    return (a + b) in {"αι", "ει", "οι", "υι", "αυ", "ευ", "ου", "ηυ", "ωυ"}


_KNOWN_BREATHINGS: dict[str, str] | None = None


def _known_breathing(base: str) -> str | None:
    """Breathing of a simplex verb in the lexicon (αἱρέω → rough) for compounds
    whose prefix shape (ἀν-, παρ-, δι-) cannot show it."""
    global _KNOWN_BREATHINGS
    if _KNOWN_BREATHINGS is None:
        _KNOWN_BREATHINGS = {}
        try:
            from ...vocab import load_entries

            for e in load_entries():
                if e["kind"] != "verb":
                    continue
                d = nfd(e["lemma"])
                if d[0] in VOWELS:
                    key = "".join(ch for ch in d if not unicodedata.combining(ch))
                    _KNOWN_BREATHINGS[key] = ROUGH if ROUGH in d[:3] else SMOOTH
        except Exception:  # pragma: no cover
            pass
    key = "".join(ch for ch in nfd(base) if not unicodedata.combining(ch))
    return _KNOWN_BREATHINGS.get(key)


def _restore_breathing(surface_prefix: str, base: str) -> str:
    """A compound's base loses its breathing mark; the prefix shape (or the
    simplex verb in the lexicon) tells us which it was."""
    d = nfd(base)
    if not d or d[0] not in VOWELS or SMOOTH in d[:3] or ROUGH in d[:3]:
        return base
    canon = PREFIX_SURFACE[surface_prefix]
    shapes = PREFIX_SHAPES[canon]
    if shapes[1] != shapes[2]:
        rough = surface_prefix == shapes[2]
        mark = ROUGH if rough else SMOOTH
    else:
        mark = _known_breathing(base) or SMOOTH
    units = _units(base)
    if len(units) > 1 and units[1][0] in VOWELS and _is_diphthong(units[0][0], units[1][0]):
        units[1] = [units[1][0], mark] + units[1][1:]
    else:
        units[0] = [units[0][0], mark] + units[0][1:]
    return nfc("".join("".join(u) for u in units))


def _augment_matches(base: str, remainder: str) -> bool:
    """Is `remainder` (after the prefix) a plausible augmented form of `base`?"""
    b = _units(strip_accent(base))
    r = _units(strip_accent(remainder))
    if not b or not r:
        return False
    if b[0][0] not in VOWELS:
        return r[0][0] in {"ε", "η"}  # η: suppletive aorists (συν-ήνεγκα)
    two = b[0][0] + (b[1][0] if len(b) > 1 and b[1][0] in VOWELS and _is_diphthong(b[0][0], b[1][0]) else "")
    expected = nfd(AUGMENT_VOWEL.get(two, two))[0]
    # ε: syllabic augment on a vowel-initial stem (ἵστημι → ἔστην) or ε+ε → ει
    return r[0][0] in {expected, two[0], "ε"}


def split_prefix(present: str, parts: dict, compound: bool | None) -> tuple[str, str, str]:
    """(canonical prefix, prefix shape seen before the augment, base with its
    breathing restored) for a compound verb.

    A verb counts as a compound only when one of its augmented principal
    parts shows the augment *after* a known prefix (ἀπο-θνῄσκω: ἀπ-έθανον),
    or when overrides say so."""
    if compound is False:
        return "", "", present
    bare = strip_accent(present)
    augmented_parts = [f.lstrip("-") for k in ("aorist", "aorist-2", "aorist-passive", "imperfect") for f in parts.get(k, [])]
    fallback = None
    candidates: list[tuple[str, str, str]] = []
    for pre in PREFIXES:
        if not (bare.startswith(pre) and len(bare) > len(pre) + 2):
            continue
        base = _restore_breathing(pre, present[len(pre):])
        canon = PREFIX_SURFACE[pre]
        for variant in sorted(set(PREFIX_SHAPES[canon][1:]), key=len, reverse=True):
            for f in augmented_parts:
                fb = strip_accent(f)
                if fb.startswith(variant) and len(fb) > len(variant) and nfd(fb[len(variant):])[0] in VOWELS:
                    if _augment_matches(base, f[len(variant):]):
                        candidates.append((canon, variant, base))
                        break
            else:
                continue
            break
        if compound and fallback is None:
            fallback = (canon, PREFIX_SHAPES[canon][1], base)
    # ἀν-αιρέω beats ἀνα-ιρέω: prefer the split whose base is a verb we know
    for c in candidates:
        if _known_breathing(c[2]) is not None or nfd(c[2])[0] not in VOWELS:
            return c
    if candidates:
        return candidates[0]
    return fallback or ("", "", present)


def unaugment(form: str, base_present: str) -> str:
    """Remove the augment from `form` (a stem without prefix), guided by the
    initial of the present stem: ἐλυσ → λυσ, ἠκουσ → ἀκουσ, ᾠκησ → οἰκησ,
    εἰχ → ἐχ, ἐσχ → σχ (syllabic augment before a consonant)."""
    f = _units(strip_accent(form))
    p = _units(strip_accent(base_present))
    if not f:
        return form
    f0 = f[0][0]
    f1 = f[1][0] if len(f) > 1 else ""
    if f0 == "ε" and f1 == "ρ" and len(f) > 2 and f[2][0] == "ρ":
        return nfc("ῥ" + "".join("".join(u) for u in f[3:]))  # ἐρρήθην → ῥηθ-
    if f0 == "ε" and f1 and f1 not in VOWELS:
        return nfc("".join("".join(u) for u in f[1:]))  # syllabic augment
    if f0 == "ε" and f1 in VOWELS and p[0][0] in VOWELS and not _is_diphthong(f0, f1):
        return nfc("".join("".join(u) for u in p[:1]) + "".join("".join(u) for u in f[2:]))  # ἑώρων, ἑάλων
    if p[0][0] not in VOWELS:
        # suppletive vowel-initial stem after a consonant-initial present (ἤνεγκα → ἐνεγκ-)
        shortened = {"η": "ε", "ω": "ο"}.get(f0)
        if shortened:
            return nfc(shortened + "".join(f[0][1:]) + "".join("".join(u) for u in f[1:]))
        return nfc("".join("".join(u) for u in f))
    # temporal augment: replace the form's initial vowel group by the present's
    pv = 2 if len(p) > 1 and p[1][0] in VOWELS and _is_diphthong(p[0][0], p[1][0]) else 1
    fv = 2 if f1 and f1 in VOWELS and (_is_diphthong(f0, f1) or f0 + f1 == "ηυ") else 1
    return nfc("".join("".join(u) for u in p[:pv]) + "".join("".join(u) for u in f[fv:]))


# ---------------------------------------------------------------------------
# joining stems and endings
# ---------------------------------------------------------------------------


def _paren(ending: str) -> tuple[str, str]:
    return (ending[:-3], "(ν)") if ending.endswith("(ν)") else (ending, "")


def join(stem: str, ending: str, accent: str | int | None = None, optative: bool = False) -> str:
    form, paren = _join_raw(stem, ending, accent, optative)
    return finish(form) + paren


def _join_raw(stem: str, ending: str, accent: str | int | None = None, optative: bool = False) -> tuple[str, str]:
    """stem + ending with the right accent, macrons kept (see join).

    accent: None → recessive; "penult" → acute/circumflex on the penult;
    "ultima" → oxytone; ("perispomenon") → circumflex on the ultima.
    Endings with their own accent keep it.
    """
    end, paren = _paren(ending)
    if _has_accent(end):
        form = strip_accent(stem) + end
    elif accent is None:
        form = recessive(stem + end, optative=optative)
    elif accent == "penult":
        sylls = syllables(strip_accent(stem + end))
        if len(sylls) == 1:
            form = accentuate(stem + end, 1, "circumflex" if syllable_is_long(sylls[-1], True) else "acute")
        else:
            kind = "circumflex" if syllable_is_long(sylls[-2]) and not syllable_is_long(sylls[-1], True) else "acute"
            form = accentuate(stem + end, 2, kind)
    elif accent == "ultima":
        form = accentuate(stem + end, 1, "acute")
    elif accent == "perispomenon":
        form = accentuate(stem + end, 1, "circumflex")
    else:
        form = recessive(stem + end)
    return form, paren


def _cells(tags, forms) -> list[dict]:
    out = []
    for tag, f in zip(tags, forms):
        if f is None:
            continue
        out.append({"tag": tag, "forms": f if isinstance(f, list) else [f]})
    return out


def _with_2sg(cells: list[dict], form: str) -> list[dict]:
    for c in cells:
        if c["tag"] == "2sg":
            c["forms"] = [form]
    return cells


def finite(stem: str, endings: list, accent=None, optative: bool = False, floor: int = 0) -> list[dict]:
    forms = []
    for e in endings:
        if e is None:
            forms.append(None)
        elif isinstance(e, list):
            forms.append(_dedupe([_floor("".join(_join_raw(stem, x, accent, optative)), floor) for x in e]))
        else:
            forms.append(_floor("".join(_join_raw(stem, e, accent, optative)), floor))
    return _cells(E.PERSONS, forms)


def _floor(form: str, floor: int) -> str:
    """In compounds the accent never recedes before the augment: παρεῖχον, not
    πάρειχον. `floor` = number of prefix syllables."""
    core, paren = (form[:-3], "(ν)") if form.endswith("(ν)") else (form, "")
    if not floor:
        return finish(core) + paren
    pos = accent_position(core)
    sylls = syllables(core)
    if pos is None:
        return finish(core) + paren
    idx_from_start = len(sylls) - pos[0]
    if idx_from_start >= floor:
        return finish(core) + paren
    target_from_end = len(sylls) - floor
    ultima_long = syllable_is_long(sylls[-1], True)
    if target_from_end == 2:
        kind = "circumflex" if syllable_is_long(sylls[-2]) and not ultima_long else "acute"
    elif target_from_end == 1:
        kind = "circumflex" if ultima_long else "acute"
    else:
        kind = "acute"
    return finish(accentuate(core, target_from_end, kind)) + paren


def _floor_cells(cells: list[dict], floor: int) -> list[dict]:
    for c in cells:
        c["forms"] = [_floor(f, floor) for f in c["forms"]]
    return cells


def _prefix_syllables(v: "VerbInfo", stem: str) -> int:
    """Syllables of the prefix as it appears at the start of `stem` (0 if none)."""
    if not v.prefix:
        return 0
    for sh in sorted(set(PREFIX_SHAPES[v.prefix]) | {"συμ", "συγ", "συλ", "ἐμ", "ἐγ"}, key=len, reverse=True):
        if strip_accent(stem).startswith(sh):
            return len(syllables(sh))
    return 0


def _dedupe(forms: list[str]) -> list[str]:
    out: list[str] = []
    for f in forms:
        if f not in out:
            out.append(f)
    return out


def participle(stem: str, endings: tuple, accent=None) -> list[dict]:
    """`accent` may be a single value for the neuter (λῦον) or a 4-tuple per
    gender + genitive (first aorist: λύσας, λύσασα, λῦσαν, λύσαντος)."""
    m, f, n, mg = endings
    if isinstance(accent, tuple):
        am, af, an, ag = accent
    else:
        am, af, an, ag = None, None, accent, None
    return _cells(("m", "f", "n", "mg"), [join(stem, m, am), join(stem, f, af), join(stem, n, an), join(stem, mg, ag)])


def table(tense: str, voice: str, mood: str, cells: list[dict], note: str | None = None) -> dict:
    t = {"tense": tense, "voice": voice, "mood": mood, "cells": cells}
    if note:
        t["note"] = note
    return t


# ---------------------------------------------------------------------------
# contraction
# ---------------------------------------------------------------------------

def _units(text: str) -> list[list[str]]:
    """Split NFD text into [base char + its combining marks] units."""
    out: list[list[str]] = []
    for ch in nfd(text):
        if unicodedata.combining(ch) and out:
            out[-1].append(ch)
        else:
            out.append([ch])
    return out


def contract(stem_vowel: str, stem: str, ending: str, optative: bool = False) -> str:
    """Contract `stem` + stem vowel with a thematic ending.

    The accent is placed recessively on the uncontracted form; a contracted
    syllable takes a circumflex if the accent stood on its first vowel and an
    acute if it stood on the second (subject to the usual limits).
    """
    end, paren = _paren(ending)
    end_nfd = nfd(end)
    m = re.match(r"([αεηιουω])([\u0300-\u036f]*)([ιυ]?)([\u0300-\u036f]*)", end_nfd)
    if not m:
        return join(stem + stem_vowel, ending)
    v1, marks1, v2, marks2 = m.groups()
    table_ = E.CONTRACT[stem_vowel]
    key = v1 + v2 if (v1 + v2) in table_ else v1
    if key == v1:
        v2, marks2 = "", ""
    tail = end_nfd[len(v1) + len(marks1) + len(v2) + len(marks2):]
    iota_sub = "\u0345" in (marks1 + marks2)
    result = table_[key]
    n_pre = len(_units(strip_accent(stem)))
    uncontracted = strip_accent(stem) + stem_vowel + v1 + v2 + nfc(tail)
    rec = recessive(uncontracted, optative=optative)
    units = _units(rec)
    stem_units = units[:n_pre]
    sv = units[n_pre]
    ev = units[n_pre + 1 : n_pre + 1 + len(v1) + len(v2)]
    tail_units = units[n_pre + 1 + len(v1) + len(v2):]
    accented = lambda u: any(c in (ACUTE, CIRCUMFLEX) for c in u[1:])
    if accented(sv):
        kind = "circumflex"
    elif any(accented(u) for u in ev):
        kind = "acute"
    else:
        kind = None
    res_nfd = nfd(result)
    res_units = _units(res_nfd)
    if iota_sub and "\u0345" not in res_nfd:
        res_units[-1].append("\u0345")
    if paren and not tail:
        paren = ""  # ἐτίμα, ἐποίει, ἐδήλου: no movable ν after a contracted vowel
    if kind is None:
        body = "".join("".join(u) for u in stem_units + res_units + tail_units)
        return finish(nfc(body)) + paren
    plain_body = "".join("".join(u) for u in stem_units) + "".join("".join(u) for u in res_units) + "".join("".join(u) for u in tail_units)
    plain_body = strip_accent(nfc(plain_body))
    sylls = syllables(plain_body)
    idx_from_end = len(syllables(nfc("".join("".join(u) for u in res_units + tail_units))))
    if kind == "circumflex":
        if idx_from_end == 2 and syllable_is_long(sylls[-1], not optative):
            kind = "acute"
        if idx_from_end > 2:
            kind = "acute"
    form = accentuate(plain_body, idx_from_end, kind)
    return finish(form) + paren


def contract_finite(stem_vowel: str, stem: str, endings: list, optative: bool = False) -> list[dict]:
    forms = []
    for e in endings:
        if e is None:
            forms.append(None)
        elif isinstance(e, list):
            forms.append(_dedupe([contract(stem_vowel, stem, x, optative) for x in e]))
        else:
            forms.append(contract(stem_vowel, stem, e, optative))
    return _cells(E.PERSONS, forms)


def contract_participle(stem_vowel: str, stem: str, endings: tuple) -> list[dict]:
    forms = [contract(stem_vowel, stem, e) for e in endings]
    if endings == E.PART_ACT:
        # the neuter keeps the circumflex of the masculine (τιμῶν, ποιοῦν, δηλοῦν)
        m_form = forms[0]
        forms[2] = {"α": m_form, "η": m_form, "ε": m_form[:-2] + "οῦν" if m_form.endswith("ῶν") else m_form, "ο": m_form[:-2] + "οῦν" if m_form.endswith("ῶν") else m_form}[stem_vowel]
    return _cells(("m", "f", "n", "mg"), forms)


# ---------------------------------------------------------------------------
# stem analysis
# ---------------------------------------------------------------------------


class VerbInfo:
    def __init__(self, entry: dict):
        self.entry = entry
        self.lemma = entry["lemma"]
        morph = entry.get("morph", {})
        self.parts: dict[str, list[str]] = {k: list(v) for k, v in morph.get("parts", {}).items()}
        self.extra: dict[str, list[str]] = morph.get("extra", {})
        self.subclass = entry.get("subclass", "verb-omega")
        ov = morph.get("verb", {})
        self.ov = ov
        self.deponent = ov.get("deponent", self.subclass == "verb-deponent" or strip_accent(self.lemma).endswith("μαι"))
        self.impersonal = self.subclass == "verb-impersonal"
        present = self.parts.get("present", [self.lemma])[0]
        self.present = present
        self.prefix, self.prefix_v, self.base = split_prefix(present, {**self.parts, "imperfect": self.extra.get("imperfect", [])}, ov.get("compound"))
        self.notes: list[str] = []


def _strip_ending(form: str, endings: tuple[str, ...]) -> str | None:
    bare = strip_accent(form)
    for e in endings:
        if bare.endswith(e) and len(bare) > len(e):
            return strip_accent(form)[: -len(e)]
    return None


# presents whose stem vowel is long but unmarked (λῦε, λῦσαι, θῦσαι)
LONG_VERB_STEMS = {"λύω": "λῡω", "θύω": "θῡω", "φύω": "φῡω", "κωλύω": "κωλῡω", "δύω": "δῡω"}


def present_stem(v: VerbInfo) -> tuple[str, str | None]:
    """(stem, contract vowel or None) of the base present (prefix removed)."""
    base = LONG_VERB_STEMS.get(v.base, v.base)
    bare = strip_accent(base)
    for vowel in ("α", "ε", "ο"):
        for end in (vowel + "ω", vowel + "ομαι"):
            if bare.endswith(end) and len(bare) > len(end):
                stem = bare[: -len(end)]
                if v.ov.get("contract") == "eta":
                    return stem, "η"
                return stem, vowel
    for end in ("ομαι", "ω"):
        if bare.endswith(end):
            return bare[: -len(end)], None
    return bare, None


def augment_stem(base_stem: str) -> str:
    """Add the augment to an unaugmented, prefix-less stem."""
    units = _units(base_stem)
    if units[0][0] in VOWELS:
        breathing = _breathing(base_stem)
        two = units[0][0] + (units[1][0] if len(units) > 1 and units[1][0] in VOWELS else "")
        if len(two) == 2 and two in AUGMENT_VOWEL:
            new, rest = AUGMENT_VOWEL[two], units[2:]
        else:
            new, rest = AUGMENT_VOWEL.get(units[0][0], units[0][0]), units[1:]
        nu = _units(new)
        # keep iota subscript / macron of the new vowel; breathing goes on the last vowel letter
        nu[-1] = [nu[-1][0], breathing] + nu[-1][1:]
        return nfc("".join("".join(u) for u in nu + rest))
    return nfc("ε" + SMOOTH + base_stem)


def _ei_augment(v: VerbInfo) -> bool:
    """ἐάω, ἐργάζομαι, ἕπομαι, ἔχω: an initial ε augments to ει (seen in the DCC aorist)."""
    if v.ov.get("ei_augment") is not None:
        return bool(v.ov["ei_augment"])
    if nfd(strip_accent(v.base))[:1] != "ε":
        return False
    for f in v.parts.get("aorist", []) + v.extra.get("imperfect", []):
        fb = strip_accent(f.lstrip("-"))
        if v.prefix:
            for prev in sorted(set(PREFIX_SHAPES[v.prefix]), key=len, reverse=True):
                if fb.startswith(prev):
                    fb = fb[len(prev):]
                    break
        if fb.startswith("ει") or fb.startswith("εἰ") or fb.startswith("εἱ"):
            return True
    return False


def augmented(v: VerbInfo, base_stem: str) -> str:
    if v.ov.get("imperfect_stem"):
        return v.ov["imperfect_stem"]
    aug = augment_stem(base_stem)
    if _ei_augment(v):
        units = _units(base_stem)
        units[0] = ["ε", *[m for m in units[0][1:] if m in (SMOOTH, ROUGH)]]
        rest = "".join("".join(u) for u in units[1:])
        breathing = _breathing(base_stem)
        aug = nfc("ε" + "ι" + breathing + rest)
    return attach_prefix(v.prefix, aug) if v.prefix else aug


def with_prefix(v: VerbInfo, stem: str) -> str:
    return attach_prefix(v.prefix, stem) if v.prefix else stem


def _keep_length(form: str) -> str:
    """Strip accents but remember a circumflexed α/ι/υ as long (ἀφῖγμαι → ἀφῑγμαι)."""
    units = _units(form)
    out = []
    for u in units:
        if u[0] in "αιυ" and CIRCUMFLEX in u[1:]:
            u = [u[0]] + [m for m in u[1:] if m != CIRCUMFLEX] + ["\u0304"]
        out.append("".join(u))
    return strip_accent(nfc("".join(out)))


def _ensure_breathing(stem: str) -> str:
    d = nfd(stem)
    if d and d[0] in VOWELS and SMOOTH not in d[:3] and ROUGH not in d[:3]:
        units = _units(stem)
        if len(units) > 1 and units[1][0] in VOWELS and _is_diphthong(units[0][0], units[1][0]):
            units[1] = [units[1][0], SMOOTH] + units[1][1:]
        else:
            units[0] = [units[0][0], SMOOTH] + units[0][1:]
        return nfc("".join("".join(u) for u in units))
    return stem


def _lengthen(v: VerbInfo, stem: str, augmented: bool = False) -> str:
    """λυσ → λῡσ for the few verbs with a long unmarked stem vowel."""
    long_base = LONG_VERB_STEMS.get(v.base)
    if not long_base:
        return stem
    plain = strip_accent(v.base)[:-1]          # λυ
    marked = strip_accent(long_base)[:-1]      # λῡ
    if augmented:
        return stem.replace("ἐ" + plain, "ἐ" + marked, 1) if stem.startswith("ἐ" + plain) else stem
    return marked + stem[len(plain):] if stem.startswith(plain) else stem


def _strip_prefix(v: VerbInfo, stem: str) -> str:
    """An override stem may be written with the compound's prefix (ἐξελθ for
    ἐξέρχομαι); the builders add the prefix themselves, so drop it here."""
    if not v.prefix:
        return stem
    bare = strip_accent(stem)
    for sh in sorted(set(PREFIX_SHAPES[v.prefix]), key=len, reverse=True):
        if bare.startswith(sh) and len(bare) > len(sh) + 1:
            return _restore_breathing(sh, stem[len(sh):])
    return stem


def aorist_stems(v: VerbInfo) -> dict:
    """Classify the aorist(s): {'type': 'sigma'|'thematic'|'root'|'kappa', 'aug': augmented stem, 'stem': plain stem}."""
    out = {}
    forms = v.parts.get("aorist", [])
    a2 = v.parts.get("aorist-2", []) + v.parts.get("aorist-2-middle", [])
    a1 = v.parts.get("aorist-1", [])
    candidates: list[tuple[str, str]] = []
    for f in forms:
        label = "2" if f in a2 else ("1" if f in a1 else "?")
        candidates.append((f, label))
    for f in a2:
        if f not in forms:
            candidates.append((f, "2"))
    passive_like = [f for f, _ in candidates if strip_accent(f).endswith("θην")]
    for f in passive_like:
        if f not in v.parts.get("aorist-passive", []):
            v.parts.setdefault("aorist-passive", []).append(f)
    candidates = [(f, l) for f, l in candidates if f not in passive_like]
    seen_stems: dict[str, dict] = {}
    for f, label in candidates:
        f = f.lstrip("-")
        bare = strip_accent(f)
        prefix_v = ""
        body = f
        if v.prefix:
            for prev in sorted(set(PREFIX_SHAPES[v.prefix]), key=len, reverse=True):
                if bare.startswith(prev):
                    prefix_v = prev
                    body = f[len(prev):]
                    break
        # decide the type from the ending
        if bare.endswith("μην"):
            typ = "thematic-mid" if re.search(r"[^σ]ομην$", bare) or bare.endswith("ομην") else "sigma-mid"
            if bare.endswith("αμην"):
                typ = "sigma-mid"
        elif re.search(r"(ωκα|ηκα|ῆκα|ἧκα)$", bare) and v.subclass == "verb-mi":
            typ = "kappa"
        elif bare.endswith(("ον", "ομην")):
            typ = "thematic"
        elif re.search(r"(ην|ων|υν)$", bare) and (label == "2" or v.subclass in {"verb-mi", "verb-irregular"} or bare.endswith("ων")):
            typ = "root"
        elif bare.endswith("α"):
            typ = "sigma"
        else:
            typ = "sigma"
        # plain stem: unaugment the body
        if typ in {"thematic", "thematic-mid"}:
            stem_aug = strip_accent(body)[:-2] if typ == "thematic" else strip_accent(body)[:-4]
        elif typ in {"sigma", "sigma-mid", "kappa"}:
            stem_aug = strip_accent(body)[:-1] if typ == "sigma" else (strip_accent(body)[:-4] if typ == "sigma-mid" else strip_accent(body)[:-2])
        else:  # root: ἔβην → ἐβη
            stem_aug = strip_accent(body)[:-1]
        plain = unaugment(stem_aug, v.base) if not v.ov.get("no_augment") else stem_aug
        plain = _lengthen(v, plain)
        stem_aug = _lengthen(v, stem_aug, augmented=True)
        if not prefix_v:
            stem_aug = _ensure_breathing(stem_aug)
        if typ == "sigma" and v.ov.get("aorist_stem_1"):
            plain = _strip_prefix(v, v.ov["aorist_stem_1"])
        elif v.ov.get("aorist_stem") and typ != "sigma" or (v.ov.get("aorist_stem") and typ == "sigma" and label != "?"):
            plain = _strip_prefix(v, v.ov["aorist_stem"])
        if not prefix_v and not v.prefix:
            plain = _ensure_breathing(plain)
        rec = {"type": typ, "aug": (prefix_v + stem_aug), "stem": plain, "form": f, "prefix_v": prefix_v, "alt_aug": []}
        if (typ, plain) in seen_stems:
            seen_stems[(typ, plain)]["alt_aug"].append(prefix_v + stem_aug)  # ηὗρον / εὗρον
            continue
        seen_stems[(typ, plain)] = rec
        key = "aorist-2" if typ in {"thematic", "thematic-mid", "root"} and "aorist" in out else "aorist"
        if typ == "root" and "aorist" in out and out["aorist"]["type"] == "sigma":
            key = "aorist-root"
        out[key] = rec
    return out


# ---------------------------------------------------------------------------
# tense-system builders
# ---------------------------------------------------------------------------


def present_system(v: VerbInfo) -> list[dict]:
    stem, cv = present_stem(v)
    p = v.prefix
    tables = []
    act = not v.deponent
    if (v.subclass == "verb-mi" or strip_accent(v.base).endswith(("αμαι", "υμαι"))) and not cv:
        return mi_present_system(v)
    if cv:
        s = with_prefix(v, stem)
        mono = not any(ch in VOWELS for ch in nfd(strip_accent(stem)))  # πλέω, δέω: only εε/εει contract
        cvx = cv if not (cv == "ε" and mono) else None
        ctr = (lambda ends, opt=False: contract_finite(cv, s, ends, opt)) if cvx else (lambda ends, opt=False: _mono_contract(s, ends, opt))
        pctr = (lambda ends: contract_participle(cv, s, ends)) if cvx else (lambda ends: participle(s + "ε", ends))
        aug_stem = _imperfect_stem(v, stem, cv)
        _fl = _prefix_syllables(v, aug_stem)
        ctr_aug = (lambda ends: _floor_cells(contract_finite(cv, aug_stem, ends), _fl)) if cvx else (lambda ends: _floor_cells(_mono_contract(aug_stem, ends), _fl))
        inf_act = {"α": "ᾶν", "ε": "εῖν", "ο": "οῦν", "η": "ῆν"}[cv] if cvx else "εῖν"
        inf_mp = {"α": "ᾶσθαι", "ε": "εῖσθαι", "ο": "οῦσθαι", "η": "ῆσθαι"}[cv] if cvx else "εῖσθαι"
        if act:
            tables += [
                table("present", "active", "indicative", ctr(E.PRES_ACT_IND)),
                table("present", "active", "subjunctive", ctr(E.SUBJ_ACT)),
                table("present", "active", "optative", _contract_optative_act(cv if cvx else None, s)),
                table("present", "active", "imperative", ctr(E.IMPER_ACT)),
                table("present", "active", "infinitive", _cells(["inf"], [join(s, inf_act)])),
                table("present", "active", "participle", pctr(E.PART_ACT)),
                table("imperfect", "active", "indicative", ctr_aug(E.IMPF_ACT)),
            ]
        mp = "middle" if v.deponent else "middle/passive"
        tables += [
            table("present", mp, "indicative", ctr(E.PRES_MP_IND)),
            table("present", mp, "subjunctive", ctr(E.SUBJ_MP)),
            table("present", mp, "optative", ctr(E.OPT_MP, True)),
            table("present", mp, "imperative", ctr(E.IMPER_MP)),
            table("present", mp, "infinitive", _cells(["inf"], [join(s, inf_mp)])),
            table("present", mp, "participle", pctr(E.PART_MP)),
            table("imperfect", mp, "indicative", ctr_aug(E.IMPF_MP)),
        ]
        return tables
    s = with_prefix(v, stem)
    aug_stem = _imperfect_stem(v, stem, cv=None)
    if act:
        tables += [
            table("present", "active", "indicative", finite(s, E.PRES_ACT_IND)),
            table("present", "active", "subjunctive", finite(s, E.SUBJ_ACT)),
            table("present", "active", "optative", finite(s, E.OPT_ACT, optative=True)),
            table("present", "active", "imperative", finite(s, E.IMPER_ACT)),
            table("present", "active", "infinitive", _cells(["inf"], [join(s, E.INF_ACT)])),
            table("present", "active", "participle", participle(s, E.PART_ACT, "penult")),
            table("imperfect", "active", "indicative", finite(aug_stem, E.IMPF_ACT, floor=_prefix_syllables(v, aug_stem))),
        ]
    mp = "middle" if v.deponent else "middle/passive"
    tables += [
        table("present", mp, "indicative", finite(s, E.PRES_MP_IND)),
        table("present", mp, "subjunctive", finite(s, E.SUBJ_MP)),
        table("present", mp, "optative", finite(s, E.OPT_MP, optative=True)),
        table("present", mp, "imperative", finite(s, E.IMPER_MP)),
        table("present", mp, "infinitive", _cells(["inf"], [join(s, E.INF_MP)])),
        table("present", mp, "participle", participle(s, E.PART_MP)),
        table("imperfect", mp, "indicative", finite(aug_stem, E.IMPF_MP, floor=_prefix_syllables(v, aug_stem))),
    ]
    return tables


def _imperfect_stem(v: VerbInfo, stem: str, cv: str | None) -> str:
    """Augmented present stem; a DCC-given imperfect (εἶχον, ἑώρων, ᾤμην) wins."""
    given = [strip_accent(x) for x in v.extra.get("imperfect", [])]
    for g in given:
        for end in ("ομην", "μην", "ων", "ον", "ην", "ουν", "ει"):
            if g.endswith(end) and len(g) > len(end):
                core = g[: -len(end)]
                return core if cv is None else (core[:-1] if cv and end in ("ων", "ουν") and core.endswith(cv) else core)
    return augmented(v, stem)


def _mono_contract(stem: str, endings: list, optative: bool = False) -> list[dict]:
    """πλέω-type: ε contracts only with ε and ει."""
    forms = []
    for e in endings:
        if e is None:
            forms.append(None)
            continue
        es = e if isinstance(e, list) else [e]
        out = []
        for x in es:
            end, paren = _paren(x)
            if end.startswith("ε"):  # ε contracts only with ε / ει: πλεῖτε, πλεῖ, πλεῖν
                out.append(contract("ε", stem, x, optative))
            else:
                out.append(join(stem + "ε", x, None, optative))
        forms.append(out if len(out) > 1 else out[0])
    return _cells(E.PERSONS, forms)


def _contract_optative_act(cv: str | None, stem: str) -> list[dict]:
    if cv is None:
        return _mono_contract(stem, E.OPT_ACT)
    sg = ["οιην", "οιης", "οιη"]
    pl = ["οιμεν", "οιτε", "οιεν"]
    forms = [contract(cv, stem, e, True) for e in sg] + [[contract(cv, stem, e, True), contract(cv, stem, alt, True)] for e, alt in zip(pl, ["οιημεν", "οιητε", "οιησαν"])]
    # Attic: -οίην sg, -οῖμεν pl (also -οίημεν)
    return _cells(E.PERSONS, forms)


def mi_present_system(v: VerbInfo) -> list[dict]:
    bare = strip_accent(v.base)
    p = v.prefix
    tables = []
    key = None
    for k, ends in (("ω/ο", "ωμι"), ("η/ε", "ημι"), ("ῡ/υ", "υμι"), ("η/α", "ημι")):
        if bare.endswith(ends):
            key = k
            break
    if bare.endswith("αμαι"):  # δύναμαι, ἐπίσταμαι
        key = "η/α"
    if bare.endswith("υμαι"):
        key = "ῡ/υ"
    if key is None:
        return []
    if bare.endswith("στημι") or v.ov.get("mi_vowel") == "α":
        key = "η/α"
    stem = bare[:-3] if bare.endswith(("ωμι", "ημι", "υμι")) else bare[:-4]
    ends = E.MI_PRES[key]
    if bare.endswith("αμαι"):
        # δύναμαι: subjunctive and optative are recessive (δύνωμαι, δυναίμην)
        ends = {**ends, "subj_mp": ["ωμαι", "ῃ", "ηται", "ωμεθα", "ησθε", "ωνται"],
                "opt_mp": ["αιμην", "αιο", "αιτο", "αιμεθα", "αισθε", "αιντο"]}
    s = with_prefix(v, stem)
    aug = _imperfect_stem(v, stem, cv=None)
    act = not v.deponent
    if act:
        tables += [
            table("present", "active", "indicative", finite(s, ends["act_ind"])),
            table("present", "active", "subjunctive", finite(s, ends["subj_act"])),
            table("present", "active", "optative", finite(s, ends["opt_act"], optative=True)),
            table("present", "active", "imperative", finite(s, ends["imper_act"])),
            table("present", "active", "infinitive", _cells(["inf"], [join(s, ends["inf_act"])])),
            table("present", "active", "participle", participle(s, ends["part_act"])),
            table("imperfect", "active", "indicative", finite(aug, ends["impf_act"], floor=_prefix_syllables(v, aug))),
        ]
    mp = "middle" if v.deponent else "middle/passive"
    tables += [
        table("present", mp, "indicative", finite(s, ends["mp_ind"])),
        table("present", mp, "subjunctive", finite(s, ends["subj_mp"])),
        table("present", mp, "optative", finite(s, ends["opt_mp"], optative=True)),
        table("present", mp, "imperative", finite(s, ends["imper_mp"])),
        table("present", mp, "infinitive", _cells(["inf"], [join(s, ends["inf_mp"])])),
        table("present", mp, "participle", participle(s, ends["part_mp"])),
        table("imperfect", mp, "indicative", finite(aug, ends["impf_mp"], floor=_prefix_syllables(v, aug))),
    ]
    return tables


def future_system(v: VerbInfo) -> list[dict]:
    tables = []
    for f in v.parts.get("future", []):
        f = f.lstrip("-")
        bare = strip_accent(f)
        if bare.endswith(("ῶ", "ω")) and accent_position(f) == (1, "circumflex"):
            stem = f[:-1]
            tables += _contract_future(stem, active=True, middle=not v.ov.get("no_future_middle", False), vowel=v.ov.get("future_contract", "ε"))
        elif bare.endswith("ουμαι") and accent_position(f) == (2, "circumflex"):
            stem = f[:-5]
            tables += _contract_future(stem, active=False, middle=True)
        elif bare.endswith("ομαι"):
            stem = strip_accent(f)[:-4]
            tables += _thematic_future(stem, active=False, middle=True)
        elif bare.endswith("ω"):
            stem = _lengthen(v, strip_accent(f)[:-1])
            tables += _thematic_future(stem, active=True, middle=not v.deponent and not v.ov.get("no_future_middle", False))
        elif bare.endswith("ει") and v.impersonal:
            tables.append(table("future", "active", "indicative", _cells(["3sg"], [f])))
    # future passive from the aorist passive stem
    for ap in v.parts.get("aorist-passive", [])[:1]:
        stem = _aorist_passive_stem(v, ap)
        if stem:
            s = stem + E.FUTP
            tables += [
                table("future", "passive", "indicative", finite(s, E.PRES_MP_IND)),
                table("future", "passive", "optative", finite(s, E.OPT_MP, optative=True)),
                table("future", "passive", "infinitive", _cells(["inf"], [join(s, E.INF_MP)])),
                table("future", "passive", "participle", participle(s, E.PART_MP)),
            ]
    return tables


def _thematic_future(stem: str, active: bool, middle: bool) -> list[dict]:
    out = []
    if active:
        out += [
            table("future", "active", "indicative", finite(stem, E.PRES_ACT_IND)),
            table("future", "active", "optative", finite(stem, E.OPT_ACT, optative=True)),
            table("future", "active", "infinitive", _cells(["inf"], [join(stem, E.INF_ACT)])),
            table("future", "active", "participle", participle(stem, E.PART_ACT, "penult")),
        ]
    if middle:
        out += [
            table("future", "middle", "indicative", finite(stem, E.PRES_MP_IND)),
            table("future", "middle", "optative", finite(stem, E.OPT_MP, optative=True)),
            table("future", "middle", "infinitive", _cells(["inf"], [join(stem, E.INF_MP)])),
            table("future", "middle", "participle", participle(stem, E.PART_MP)),
        ]
    return out


def _contract_future(stem: str, active: bool, middle: bool, vowel: str = "ε") -> list[dict]:
    out = []
    note = "Contract (‘Attic’) future: -έω endings contract like ποιέω." if vowel == "ε" else "Attic future in -ῶ, -ᾷς, -ᾷ: contracts like τιμάω."
    inf_act, inf_mid = ("εῖν", "εῖσθαι") if vowel == "ε" else ("ᾶν", "ᾶσθαι")
    if active:
        out += [
            table("future", "active", "indicative", contract_finite(vowel, stem, E.PRES_ACT_IND), note),
            table("future", "active", "optative", _contract_optative_act(vowel, stem)),
            table("future", "active", "infinitive", _cells(["inf"], [join(stem, inf_act)])),
            table("future", "active", "participle", contract_participle(vowel, stem, E.PART_ACT)),
        ]
    if middle:
        out += [
            table("future", "middle", "indicative", contract_finite(vowel, stem, E.PRES_MP_IND), note),
            table("future", "middle", "optative", contract_finite(vowel, stem, E.OPT_MP, True)),
            table("future", "middle", "infinitive", _cells(["inf"], [join(stem, inf_mid)])),
            table("future", "middle", "participle", contract_participle(vowel, stem, E.PART_MP)),
        ]
    return out


def _alt_indicative(cells: list[dict], aug: str, alts: list[str], endings: list) -> list[dict]:
    for alt in alts:
        live = [e for e in endings if e is not None]
        for c, e in zip(cells, live):
            es = e if isinstance(e, list) else [e]
            c["forms"] = _dedupe(c["forms"] + [join(alt, x) for x in es])
    return cells


def aorist_system(v: VerbInfo) -> list[dict]:
    tables = []
    stems = aorist_stems(v)
    for key in ("aorist", "aorist-2", "aorist-root"):
        rec = stems.get(key)
        if not rec:
            continue
        typ, aug, stem = rec["type"], rec["aug"], rec["stem"]
        stem_p = with_prefix(v, stem)
        label = "aorist" if key == "aorist" else ("second aorist" if typ != "root" else "root aorist")
        if typ == "sigma" or typ == "sigma-mid":
            act = typ == "sigma"                      # an active form (ἔδεισα) is active even for deponents
            mid = (not v.deponent) and not v.ov.get("no_aorist_middle", False)
            if typ == "sigma-mid":
                act, mid = False, True
            if act:
                tables += [
                    table(label, "active", "indicative", finite(aug, E.AOR1_ACT_IND, floor=_prefix_syllables(v, aug))),
                    table(label, "active", "subjunctive", finite(stem_p, E.AOR1_SUBJ_ACT)),
                    table(label, "active", "optative", finite(stem_p, E.AOR1_OPT_ACT, optative=True)),
                    table(label, "active", "imperative", finite(stem_p, [None, None, "ατω", None, "ατε", "αντων"]) and _with_2sg(finite(stem_p, E.AOR1_IMPER_ACT), join(stem_p, "ον", "penult"))),
                    table(label, "active", "infinitive", _cells(["inf"], [join(stem_p, E.AOR1_INF_ACT, "penult")])),
                    table(label, "active", "participle", participle(stem_p, E.AOR1_PART_ACT, ("penult", None, "penult", None))),
                ]
            if mid:
                tables += [
                    table(label, "middle", "indicative", finite(aug, E.AOR1_MID_IND, floor=_prefix_syllables(v, aug))),
                    table(label, "middle", "subjunctive", finite(stem_p, E.AOR1_SUBJ_MP)),
                    table(label, "middle", "optative", finite(stem_p, E.AOR1_OPT_MID, optative=True)),
                    table(label, "middle", "imperative", finite(stem_p, [None, "αι", "ασθω", None, "ασθε", "ασθων"])),
                    table(label, "middle", "infinitive", _cells(["inf"], [join(stem_p, E.AOR1_INF_MID)])),
                    table(label, "middle", "participle", participle(stem_p, E.AOR1_PART_MID)),
                ]
        elif typ in {"thematic", "thematic-mid"}:
            act = typ == "thematic"                   # ἦλθον, ἑάλων: active in form
            mid = True if typ == "thematic-mid" else (not v.deponent and not v.ov.get("no_aorist_middle", False))
            imper2 = "έ" if strip_accent(stem_p) in T.OXYTONE_IMPERATIVES else "ε"
            if act:
                tables += [
                    table(label, "active", "indicative", _alt_indicative(finite(aug, E.IMPF_ACT, floor=_prefix_syllables(v, aug)), aug, rec["alt_aug"], E.IMPF_ACT)),
                    table(label, "active", "subjunctive", finite(stem_p, E.SUBJ_ACT)),
                    table(label, "active", "optative", finite(stem_p, E.OPT_ACT, optative=True)),
                    table(label, "active", "imperative", finite(stem_p, [None, imper2, "ετω", None, "ετε", "οντων"])),
                    table(label, "active", "infinitive", _cells(["inf"], [join(stem_p, "εῖν")])),
                    table(label, "active", "participle", participle(stem_p, ("ών", "οῦσα", "όν", "όντος"))),
                ]
            if mid:
                tables += [
                    table(label, "middle", "indicative", _alt_indicative(finite(aug, E.IMPF_MP, floor=_prefix_syllables(v, aug)), aug, rec["alt_aug"], E.IMPF_MP)),
                    table(label, "middle", "subjunctive", finite(stem_p, E.SUBJ_MP)),
                    table(label, "middle", "optative", finite(stem_p, E.OPT_MP, optative=True)),
                    table(label, "middle", "imperative", finite(stem_p, [None, "οῦ", "εσθω", None, "εσθε", "εσθων"])),
                    table(label, "middle", "infinitive", _cells(["inf"], [join(stem_p, "έσθαι")])),
                    table(label, "middle", "participle", participle(stem_p, E.PART_MP)),
                ]
        elif typ == "root":
            ends = _root_endings(stem)
            if ends is None:
                continue
            key_v, ends_t = ends
            short = _root_short(stem, key_v)
            short_p = with_prefix(v, short)
            long_aug = aug  # e.g. ἐβη / ἐστη / ἐγνω
            tables += [
                table(label, "active", "indicative", finite(long_aug[:-1], ends_t["ind"], floor=_prefix_syllables(v, long_aug[:-1]))),
                table(label, "active", "subjunctive", finite(short_p[:-1], ends_t["subj"])),
                table(label, "active", "optative", finite(short_p[:-1], ends_t["opt"], optative=True)),
                table(label, "active", "imperative", finite(short_p[:-1], ends_t["imper"])),
                table(label, "active", "infinitive", _cells(["inf"], [join(short_p[:-1], ends_t["inf"])])),
                table(label, "active", "participle", participle(short_p[:-1], ends_t["part"])),
            ]
        elif typ == "kappa":
            key_v = "ω/ο" if strip_accent(stem).endswith("ω") else "η/ε"
            ends = E.MI_AOR[key_v]
            short = stem[:-1]           # δω → δ ; the endings supply ο/ω
            short_p = with_prefix(v, short)
            aug_short = aug[:-1]
            tables += [
                table(label, "active", "indicative", finite(aug_short, ends["act_ind"], floor=_prefix_syllables(v, aug_short))),
                table(label, "active", "subjunctive", finite(short_p, ends["subj_act"])),
                table(label, "active", "optative", finite(short_p, ends["opt_act"], optative=True)),
                table(label, "active", "imperative", finite(short_p, ends["imper_act"])),
                table(label, "active", "infinitive", _cells(["inf"], [join(short_p, ends["inf_act"])])),
                table(label, "active", "participle", participle(short_p, ends["part_act"])),
                table(label, "middle", "indicative", finite(aug_short, ends["mid_ind"], floor=_prefix_syllables(v, aug_short))),
                table(label, "middle", "subjunctive", finite(short_p, ends["subj_mid"])),
                table(label, "middle", "optative", finite(short_p, ends["opt_mid"], optative=True)),
                table(label, "middle", "imperative", finite(short_p, ends["imper_mid"])),
                table(label, "middle", "infinitive", _cells(["inf"], [join(short_p, ends["inf_mid"])])),
                table(label, "middle", "participle", participle(short_p, ends["part_mid"])),
            ]
    # aorist passive
    for ap in v.parts.get("aorist-passive", []):
        stem = _aorist_passive_stem(v, ap)
        if not stem:
            continue
        aug = _aorist_passive_aug(v, ap)
        imper = list(E.AORP_IMPER)
        imper[1] = "ητι" if strip_accent(stem).endswith("θ") else "ηθι"
        label = "aorist" if strip_accent(stem).endswith("θ") else "second aorist"
        tables += [
            table(label, "passive", "indicative", finite(aug, E.AORP_IND, floor=_prefix_syllables(v, aug))),
            table(label, "passive", "subjunctive", finite(stem, E.AORP_SUBJ)),
            table(label, "passive", "optative", finite(stem, E.AORP_OPT, optative=True)),
            table(label, "passive", "imperative", finite(stem, imper)),
            table(label, "passive", "infinitive", _cells(["inf"], [join(stem, E.AORP_INF)])),
            table(label, "passive", "participle", participle(stem, E.AORP_PART)),
        ]
    return tables


def _root_endings(stem: str):
    bare = strip_accent(stem)
    if bare.endswith("η"):
        return "η/α", E.ROOT_AOR["η/α"]
    if bare.endswith("ω"):
        return "ω/ο", E.ROOT_AOR["ω/ο"]
    if bare.endswith("υ"):
        return "υ/υ", E.ROOT_AOR["υ/υ"]
    return None


def _root_short(stem: str, key: str) -> str:
    short = {"η/α": "α", "ω/ο": "ο", "υ/υ": "υ"}[key]
    return stem[:-1] + short


def _aorist_passive_stem(v: VerbInfo, ap: str) -> str | None:
    ap = ap.lstrip("-")
    bare = strip_accent(ap)
    if not bare.endswith("ην"):
        return None
    body = ap
    prefix_v = ""
    if v.prefix:
        for prev in sorted(set(PREFIX_SHAPES[v.prefix]), key=len, reverse=True):
            if bare.startswith(prev):
                prefix_v, body = prev, ap[len(prev):]
                break
    stem_aug = strip_accent(body)[:-2]
    plain = v.ov.get("aorist_passive_stem") or unaugment(stem_aug, v.base)
    return with_prefix(v, plain)


def _aorist_passive_aug(v: VerbInfo, ap: str) -> str:
    aug = strip_accent(ap.lstrip("-"))[:-2]
    return aug if v.prefix else _ensure_breathing(aug)


def perfect_system(v: VerbInfo) -> list[dict]:
    tables = []
    for pf in v.parts.get("perfect", [])[:2]:
        pf = pf.lstrip("-")
        bare = strip_accent(pf)
        if not bare.endswith("α"):
            continue
        stem = strip_accent(pf)[:-1]
        if not v.prefix:
            stem = _ensure_breathing(stem)
        plup = _pluperfect_stem(v, stem)
        given = [x for x in v.extra.get("pluperfect", []) if strip_accent(x).endswith(("η", "ειν", "ει"))]
        if given:
            g = strip_accent(given[0])
            plup = g[:-3] if g.endswith("ειν") else (g[:-2] if g.endswith("ει") else g[:-1])
        tables += [
            table("perfect", "active", "indicative", finite(stem, E.PERF_ACT_IND, floor=_prefix_syllables(v, stem))),
            table("perfect", "active", "subjunctive", _periphrastic(stem, E.PERF_PART_ACT, T.EIMI_SUBJ), "Usually periphrastic: perfect participle + subjunctive of εἰμί."),
            table("perfect", "active", "optative", _periphrastic(stem, E.PERF_PART_ACT, T.EIMI_OPT), "Usually periphrastic: perfect participle + optative of εἰμί."),
            table("perfect", "active", "infinitive", _cells(["inf"], [join(stem, E.PERF_INF_ACT)])),
            table("perfect", "active", "participle", participle(stem, E.PERF_PART_ACT)),
            table("pluperfect", "active", "indicative", finite(plup, E.PLUP_ACT_IND, floor=_prefix_syllables(v, plup))),
        ]
    for pm in v.parts.get("perfect-mp", [])[:1]:
        pm = pm.lstrip("-")
        tables += _perfect_mp(v, pm)
    return tables


def _pluperfect_stem(v: VerbInfo, stem: str) -> str:
    """Pluperfect adds an augment before consonantal reduplication (ἐ-λελυκ-);
    a vowel-initial perfect stem lengthens α/ο (ἀκήκοα → ἠκηκόη, ὄλωλα → ὠλώλη)
    but Attic keeps ε (ἐλήλυθα → ἐληλύθη); ἑόρακα → ἑωράκη."""
    if v.ov.get("pluperfect_stem"):
        return v.ov["pluperfect_stem"]
    body = stem
    prefix = ""
    if v.prefix:
        base_vowel = bool(v.base) and nfd(strip_accent(v.base))[0] in VOWELS
        matches = [sh for sh in sorted(set(PREFIX_SHAPES[v.prefix]) | {"συμ", "συγ", "συλ", "ἐμ", "ἐγ"}, key=len, reverse=True)
                   if strip_accent(stem).startswith(sh)]
        preferred = [sh for sh in matches if (nfd(strip_accent(stem[len(sh):]))[:1] in tuple(VOWELS)) == base_vowel]
        if matches:
            sh = (preferred or matches)[0]
            prefix, body = v.prefix, stem[len(sh):]
            if sh in PREFIX_SURFACE:
                body = _restore_breathing(sh, body)  # ἀφ-ῑγ- keeps its rough breathing: ἀφίγμην
    units = _units(body)
    if units and units[0][0] in VOWELS:
        first = units[0][0]
        if strip_accent(body).startswith("ἑο"):
            units[1] = ["ω"] + units[1][1:]
        elif first == "α":
            units[0] = ["η"] + units[0][1:]
        elif first == "ο":
            units[0] = ["ω"] + units[0][1:]
        body = nfc("".join("".join(u) for u in units))
        return attach_prefix(prefix, body) if prefix else body
    aug = "ἐ" + body
    return attach_prefix(prefix, aug) if prefix else aug


def _periphrastic(stem: str, part: tuple, aux: list[str]) -> list[dict]:
    m = join(stem, part[0])
    forms = [f"{m} {a}" for a in aux]
    return _cells(E.PERSONS, forms)


def _perfect_mp(v: VerbInfo, pm: str) -> list[dict]:
    bare = strip_accent(pm)
    if not bare.endswith("μαι"):
        return []
    base = _keep_length(pm)[:-3]
    if not v.prefix:
        base = _ensure_breathing(base)
    liquid = "liquid" in v.entry.get("pos", "")
    if bare.endswith("μμαι"):
        kind, base = "labial", base[:-1]
        ind = ["μμαι", "ψαι", "πται", "μμεθα", "φθε", None]
        plup = ["μμην", "ψο", "πτο", "μμεθα", "φθε", None]
        imper = [None, "ψο", "φθω", None, "φθε", None]
        inf, part = "φθαι", ("μμένος", "μμένη", "μμένον", "μμένου")
    elif bare.endswith("γμαι"):
        kind, base = "velar", base[:-1]
        ind = ["γμαι", "ξαι", "κται", "γμεθα", "χθε", None]
        plup = ["γμην", "ξο", "κτο", "γμεθα", "χθε", None]
        imper = [None, "ξο", "χθω", None, "χθε", None]
        inf, part = "χθαι", ("γμένος", "γμένη", "γμένον", "γμένου")
    elif bare.endswith("σμαι") and liquid:
        kind, base = "nasal", base[:-1]
        ind = ["σμαι", "νσαι", "νται", "σμεθα", "νθε", None]
        plup = ["σμην", "νσο", "ντο", "σμεθα", "νθε", None]
        imper = [None, "νσο", "νθω", None, "νθε", None]
        inf, part = "νθαι", ("σμένος", "σμένη", "σμένον", "σμένου")
    elif bare.endswith("σμαι"):
        kind, base = "dental", base[:-1]
        ind = ["σμαι", "σαι", "σται", "σμεθα", "σθε", None]
        plup = ["σμην", "σο", "στο", "σμεθα", "σθε", None]
        imper = [None, "σο", "σθω", None, "σθε", None]
        inf, part = "σθαι", ("σμένος", "σμένη", "σμένον", "σμένου")
    elif bare.endswith(("λμαι", "ρμαι")):
        kind = "liquid"
        ind = ["μαι", "σαι", "ται", "μεθα", "θε", None]
        plup = ["μην", "σο", "το", "μεθα", "θε", None]
        imper = [None, "σο", "θω", None, "θε", None]
        inf, part = "θαι", ("μένος", "μένη", "μένον", "μένου")
    else:
        kind = "vowel"
        ind, plup, imper = E.PERF_MP_IND, E.PLUP_MP_IND, E.PERF_MP_IMPER
        inf, part = E.PERF_MP_INF, E.PERF_MP_PART
    plup_stem = _pluperfect_stem(v, base)
    ind_cells = finite(base, ind, floor=_prefix_syllables(v, base))
    plup_cells = finite(plup_stem, plup, floor=_prefix_syllables(v, plup_stem))
    part_cells = participle(base, part)
    note = None
    if kind != "vowel":
        third = part_cells[0]["forms"][0].replace("ος", "οι") + " εἰσί(ν)"
        ind_cells.append({"tag": "3pl", "forms": [third]})
        plup_cells.append({"tag": "3pl", "forms": [part_cells[0]["forms"][0].replace("ος", "οι") + " ἦσαν"]})
        note = "Consonant stem: the 3rd plural is periphrastic (participle + εἰσί/ἦσαν)."
    tables = [
        table("perfect", "middle/passive", "indicative", ind_cells, note),
        table("perfect", "middle/passive", "subjunctive", _periphrastic(base, part, T.EIMI_SUBJ), "Periphrastic: perfect participle + subjunctive of εἰμί."),
        table("perfect", "middle/passive", "optative", _periphrastic(base, part, T.EIMI_OPT), "Periphrastic: perfect participle + optative of εἰμί."),
        table("perfect", "middle/passive", "imperative", finite(base, imper)),
        table("perfect", "middle/passive", "infinitive", _cells(["inf"], [join(base, inf, "penult")])),
        table("perfect", "middle/passive", "participle", part_cells),
        table("pluperfect", "middle/passive", "indicative", plup_cells),
    ]
    if kind == "vowel":
        fp = base + E.FUT_PERF
        tables.append(table("future perfect", "middle/passive", "indicative", finite(fp, E.PRES_MP_IND), "Rare; ‘will have been …’."))
    return tables


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

SYSTEM_ORDER = [
    ("present", "Present & imperfect", {"present", "imperfect"}),
    ("future", "Future", {"future"}),
    ("aorist", "Aorist", {"aorist", "second aorist", "root aorist"}),
    ("perfect", "Perfect & pluperfect", {"perfect", "pluperfect", "future perfect"}),
]


def _group(tables: list[dict]) -> list[dict]:
    systems = []
    for sid, label, tenses in SYSTEM_ORDER:
        ts = [t for t in tables if t["tense"] in tenses]
        if ts:
            systems.append({"id": sid, "label": label, "tables": ts})
    return systems


def conjugate_entry(entry: dict) -> dict | None:
    lemma = entry["lemma"]
    v = VerbInfo(entry)
    if lemma in T.IRREGULAR:
        spec = T.IRREGULAR[lemma]
        return {
            "kind": "verb", "lemma": lemma, "class": "irregular", "principal_parts": _pp(v),
            "notes": [spec.get("note", "")], "systems": _group(spec["tables"]),
        }
    alias = entry.get("morph", {}).get("alias_of") or v.ov.get("alias_of")
    tables: list[dict] = []
    try:
        if alias:
            tables += aorist_system(v)      # εἶπον, εἶδον: an aorist listed on its own
        else:
            tables += present_system(v)
            tables += future_system(v)
            tables += aorist_system(v)
            tables += perfect_system(v)
    except Exception as exc:  # pragma: no cover - surfaced in tests
        raise RuntimeError(f"{lemma}: {exc}") from exc
    if v.impersonal:
        tables = [_only_3sg(t) for t in tables]
    for hand in v.ov.get("tables", []):
        key = (hand["tense"], hand["voice"], hand["mood"])
        tables = [t for t in tables if (t["tense"], t["voice"], t["mood"]) != key]
        tables.append(T.from_spec(hand))
    return {
        "kind": "verb", "lemma": lemma, "class": v.subclass, "principal_parts": _pp(v),
        "notes": v.notes + ([f"Aorist of {alias}; see that entry for the other tenses."] if alias else []),
        "systems": _group(tables),
    }


def _only_3sg(t: dict) -> dict:
    keep = [c for c in t["cells"] if c["tag"] in {"3sg", "inf", "m", "f", "n", "mg"}]
    return {**t, "cells": keep}


def _pp(v: VerbInfo) -> list[dict]:
    order = [("present", "present"), ("future", "future"), ("aorist", "aorist"), ("perfect", "perfect active"),
             ("perfect-mp", "perfect middle/passive"), ("aorist-passive", "aorist passive")]
    out = []
    for key, label in order:
        forms = v.parts.get(key)
        if forms:
            out.append({"slot": label, "forms": forms})
    for key, forms in v.extra.items():
        out.append({"slot": key, "forms": forms})
    return out


def conjugate(lemma: str, subclass: str, morph: dict) -> dict | None:
    return conjugate_entry({"lemma": lemma, "subclass": subclass, "morph": morph, "kind": "verb"})
