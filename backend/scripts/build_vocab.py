"""Build app/vocab_data/core.json from the DCC Greek Core Vocabulary CSV.

Usage (from backend/):  python scripts/build_vocab.py [--check]

Input:  app/vocab_data/greek-core-list.csv  (official DCC export, CC BY-SA)
        app/vocab_data/overrides.json       (per-word corrections and tags)
Output: app/vocab_data/core.json

The script is deterministic and its output is committed, so the API never
parses the CSV at runtime. It prints anything it could not parse; the build
is considered clean only when that list is empty.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.greek.normalize import normalize_polytonic  # noqa: E402

DATA = ROOT / "app" / "vocab_data"
CSV_PATH = DATA / "greek-core-list.csv"
OVERRIDES_PATH = DATA / "overrides.json"
OUT_PATH = DATA / "core.json"

# --------------------------------------------------------------------------
# Classification tables
# --------------------------------------------------------------------------

# DCC "Part of Speech" → (kind, subclass). `kind` drives the morphology engine.
POS_CLASSES: dict[str, tuple[str, str]] = {
    "definite article": ("article", "article"),
    "adjective: 1st and 2nd declension": ("adjective", "adj-1-2"),
    "adjective: 3rd declension -ης, -ες": ("adjective", "adj-3-es"),
    "adjective: 3rd declension -ων, -ον": ("adjective", "adj-3-on"),
    "adjective: -ύς, -εῖα, -ύ": ("adjective", "adj-us"),
    "adjective: numeral": ("numeral", "numeral"),
    "pronoun": ("pronoun", "pronoun"),
    "noun: 1st declension": ("noun", "noun-1"),
    "noun: 2nd declension": ("noun", "noun-2"),
    "noun: 3rd declension consonant stem": ("noun", "noun-3-cons"),
    "noun: 3rd declension σ-stem": ("noun", "noun-3-sigma"),
    "noun: 3rd declension ι-stem": ("noun", "noun-3-iota"),
    "noun: 3rd declension -εύς, -έως": ("noun", "noun-3-eus"),
    "noun: 3rd declension irregular": ("noun", "noun-3-irregular"),
    "verb: -ω vowel stem": ("verb", "verb-omega"),
    "verb: -ω labial stem": ("verb", "verb-omega"),
    "verb: -ω palatal stem": ("verb", "verb-omega"),
    "verb: -ω dental stem": ("verb", "verb-omega"),
    "verb: -ω liquid stem": ("verb", "verb-omega"),
    "verb: contracted": ("verb", "verb-contract"),
    "verb: -μι": ("verb", "verb-mi"),
    "verb: deponent": ("verb", "verb-deponent"),
    "verb: irregular": ("verb", "verb-irregular"),
    "verb: impersonal": ("verb", "verb-impersonal"),
    "preposition": ("preposition", "preposition"),
    "adverb": ("adverb", "adverb"),
    "conjunction: coordinating": ("conjunction", "conj-coord"),
    "conjunction: subordinating": ("conjunction", "conj-subord"),
    "interjection": ("interjection", "interjection"),
}

# The user's "focus" axis. Each DCC semantic group maps to one or more topics;
# words also pick up topics from the library passages they occur in
# (added in a later build step) and from overrides.json.
TOPIC_LABELS = {
    "core": "Core (function words)",
    "mythology": "Mythology",
    "history": "History & war",
    "philosophy": "Philosophy & mind",
    "city-life": "City life in Athens",
}
GROUP_TOPICS: dict[str, list[str]] = {
    "Pronouns/Interrogatives": ["core"],
    "Conjunctions/Adverbs": ["core"],
    "Particles": ["core"],
    "Prepositions without Direction": ["core"],
    "Direction": ["core"],
    "Humanity and Being": ["philosophy", "mythology"],
    "Writing and Talking": ["philosophy", "city-life"],
    "Measurements and Numerals": ["history", "city-life"],
    "Taking and Giving": ["city-life"],
    "Work and Leisure": ["city-life"],
    "Time": ["history"],
    "Religion": ["mythology"],
    "Ethics and Morals": ["philosophy"],
    "Government and Society": ["history", "city-life"],
    "The Senses and Feelings": ["philosophy"],
    "The Mind, Perceiving and Learning": ["philosophy"],
    "Characteristics": ["philosophy"],
    "Body Parts": ["city-life", "mythology"],
    "World Order": ["mythology", "philosophy"],
    "Earth": ["mythology", "history"],
    "War and Peace": ["history"],
    "Showing and Finding": ["philosophy"],
    "Law and Judgment": ["city-life", "history"],
    "Family and Friendship and the Home": ["city-life", "mythology"],
    "Movement": ["history", "mythology"],
    "Animals and Plants": ["mythology", "city-life"],
    "Life and Death": ["mythology", "history"],
    "Help and Safety": ["history"],
}

TIERS = [
    (125, 1, "beginner"),
    (250, 2, "elementary"),
    (375, 3, "intermediate"),
    (10_000, 4, "advanced"),
]

# DCC prints a few Koine/common spellings; the app targets Classical Attic.
ATTIC_SPELLING = {"σσ": "ττ"}
ATTIC_SPELLING_RANKS = {214, 484, 134, 230, 317, 475, 220, 302, 331, 305}

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

DASH = "–"  # en dash used by DCC for abbreviated endings
GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")


def strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch)
    )


def slug(text: str) -> str:
    """Accent-free lowercase Greek id, e.g. 'λογος'."""
    base = strip_accents(text).lower()
    return re.sub(r"[^Ͱ-Ͽ]+", "", base)


def tier_for(rank: int) -> tuple[int, str]:
    for upper, tier, label in TIERS:
        if rank <= upper:
            return tier, label
    raise AssertionError(rank)


def attic_spelling(text: str, rank: int) -> str:
    if rank not in ATTIC_SPELLING_RANKS:
        return text
    for koine, attic in ATTIC_SPELLING.items():
        text = text.replace(koine, attic)
    return text


def short_gloss(definition: str) -> str:
    """First sense, trimmed for the front of a flashcard."""
    first = re.split(r"[;]", definition, maxsplit=1)[0]
    first = re.sub(r"\([^)]*\)", "", first).strip(" ,")
    if len(first) > 48:
        first = first[:45].rsplit(" ", 1)[0].rstrip(",") + "…"
    return first


LONG_ALPHA_ENDINGS = {"α", "ας"}  # fem. -ᾱ of -ος adjectives, gen. -ᾱς of 1st decl.


def expand_abbreviated(lemma: str, ending: str, lemma_ending: str) -> str:
    """'ἄνθρωπος' + '–ου' → 'ἀνθρώπου', keeping the lemma's accent rules."""
    from greek_accentuation.accentuation import persistent
    from greek_accentuation.characters import strip_accents as ga_strip

    assert lemma.endswith(lemma_ending) or strip_accents(lemma).endswith(strip_accents(lemma_ending)), (lemma, lemma_ending)
    stem = lemma[: len(lemma) - len(lemma_ending)]
    ending = ending.lstrip(DASH + "-")
    if ending != strip_accents(ending):
        # Ending carries its own accent (–οῦ, –ῆς): drop the lemma accent.
        return unicodedata.normalize("NFC", ga_strip(stem) + ending)
    long_alpha = ending in LONG_ALPHA_ENDINGS
    if long_alpha:  # mark the α long so the accent cannot stay on the antepenult
        ending = ending.replace("α", "ᾱ")
    form = unicodedata.normalize("NFC", ga_strip(stem) + ending)
    try:
        moved = persistent(form, lemma)
    except Exception:  # pragma: no cover - library edge cases
        moved = None
    out = unicodedata.normalize("NFC", moved or form)
    return out.replace("ᾱ", "α") if long_alpha else out


# --------------------------------------------------------------------------
# Headword parsers
# --------------------------------------------------------------------------

def _nfc(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(unicodedata.normalize("NFC", i) for i in items)


NOUN_ENDINGS = {
    "noun-1": _nfc(("ης", "ής", "ας", "ᾶς", "ῆς", "η", "α", "ά", "ή", "ᾱ")),
    "noun-2": _nfc(("ος", "ον", "ός", "όν", "οῦς", "ους")),
}


def parse_noun(headword: str, subclass: str) -> dict:
    """'λόγος λόγου, ὁ' / 'ἄνθρωπος –ου, ὁ/ἡ' / 'νοῦς, νοῦ, ὁ (other dialects…)'."""
    head = re.sub(r"\([^)]*\)", "", headword).strip()
    head = head.replace(",", " ")
    tokens = head.split()
    article = [t for t in tokens if strip_accents(t) in {"ο", "η", "το", "ο/η"}]
    forms = [t for t in tokens if t not in article]
    if not forms:
        raise ValueError(headword)
    lemma = forms[0]
    genitive = forms[1] if len(forms) > 1 else None
    if genitive and genitive.startswith(DASH):
        lemma_ending = next(
            (e for e in sorted(NOUN_ENDINGS.get(subclass, ()), key=len, reverse=True) if lemma.endswith(e)),
            None,
        )
        if lemma_ending is None:
            raise ValueError(f"cannot expand {headword}")
        genitive = expand_abbreviated(lemma, genitive, lemma_ending)
    gender = {"ο": "m", "η": "f", "το": "n", "ο/η": "m/f"}.get(strip_accents(article[0]) if article else "", None)
    return {"lemma": lemma, "genitive": genitive, "gender": gender, "article": article[0] if article else None}




def parse_adjective(headword: str) -> dict:
    """'ἀγαθός ἀγαθή ἀγαθόν' / 'κακός –ή –όν' / 'ἀδύνατος –ον' / 'ἀληθής –ές'."""
    head = re.sub(r"\(ν\)", "", headword).strip()
    tokens = head.split()
    lemma = tokens[0]
    rest = tokens[1:]
    # Determine the masculine ending so abbreviated forms can be expanded.
    endings = sorted(_nfc(("ος", "ός", "οῦς", "ης", "ής", "ων", "ύς", "υς", "ας")), key=len, reverse=True)
    lemma_ending = next((e for e in endings if lemma.endswith(e)), None)
    expanded = []
    for tok in rest:
        if tok.startswith(DASH):
            if lemma_ending is None:
                raise ValueError(headword)
            expanded.append(expand_abbreviated(lemma, tok, lemma_ending))
        else:
            expanded.append(tok)
    terminations = 1 + len(expanded)
    out = {"lemma": lemma, "terminations": terminations, "forms": [lemma, *expanded]}
    if terminations == 3:
        out["feminine"], out["neuter"] = expanded
    elif terminations == 2:
        out["neuter"] = expanded[0]
    return out


VERB_LABELS = {
    "impf.": "imperfect",
    "infin.": "infinitive",
    "act. infin.": "infinitive-active",
    "mid.infin.": "infinitive-middle",
    "imper.": "imperative",
    "ptc.": "participle",
    "plupf.": "pluperfect",
    "plup.": "pluperfect",
    "pf.": "perfect",
    "fut.": "future",
    "aor.": "aorist",
    "1 aor.": "aorist-1",
    "2 aor.": "aorist-2",
    "2 aor. mid.": "aorist-2-middle",
}
SLOTS = ("present", "future", "aorist", "perfect", "perfect-mp", "aorist-passive")


def _split_alternatives(text: str) -> list[str]:
    parts = re.split(r"\s+(?:or|and)\s+", text)
    return [p.strip(" ,") for p in parts if p.strip(" ,")]


def _reduplicated(bare: str) -> bool:
    """λέλυκα / πέφηνα / κεχάρηκα style reduplication (aspirates → plain)."""
    if len(bare) < 3 or bare[1] != "ε":
        return False
    first, third = bare[0], bare[2]
    return first == third or (first, third) in {("π", "φ"), ("τ", "θ"), ("κ", "χ")}


def _classify(form: str, filled: set[str]) -> str | None:
    """Best-effort principal-part slot for an unlabeled form (order matters)."""
    bare = strip_accents(form).lstrip("-")
    if "present" not in filled:
        return "present"
    if "future" not in filled and re.search(r"(σω|ξω|ψω|ω|σομαι|ξομαι|ψομαι|ομαι|ουμαι|ιω|σει)$", bare):
        return "future"
    if bare.endswith("θην"):
        return "aorist-passive"
    if bare.endswith("ην") and ("perfect" in filled or "perfect-mp" in filled):
        return "aorist-passive"
    if bare.endswith("μαι"):
        return "perfect-mp" if "aorist" in filled or "future" in filled else "present"
    if bare.endswith("μην"):
        return "aorist" if "aorist" not in filled else "aorist-2"
    if "aorist" not in filled and not (bare.endswith("κα") and _reduplicated(bare)):
        return "aorist"
    if "perfect" not in filled and _reduplicated(bare) and not re.search(r"(ον|ην|ων|υν)$", bare):
        return "perfect"
    if "perfect" not in filled and re.search(r"(ον|ην|ων|υν)$", bare) and "aorist" in filled:
        return "aorist-2"
    if "perfect" not in filled:
        return "perfect"
    return None


def _assign(form: str, label: str, parts: dict, extra: dict, filled: set[str]) -> None:
    slot = VERB_LABELS.get(label) or (label.rstrip(".") if label else None) or _classify(form, filled) or "other"
    if slot in SLOTS:
        parts.setdefault(slot, []).append(form)
        filled.add(slot)
    else:
        extra.setdefault(slot, []).append(form)


def parse_verb(headword: str) -> dict:
    """Split a DCC verb headword into labelled principal parts.

    Returns {"lemma", "parts": {slot: [forms]}, "extra": {label: [forms]}, "raw": [...]}.
    """
    text = headword
    # Remove glosses in quotes/parentheses ("I am undone", "(but usu. κεῖμαι instead)").
    text = re.sub(r"\((?:[^()]*)\)", "", text)
    text = re.sub(r"[“\"][^”\"]*[”\"]", "", text)
    # Drop stray English glosses after a form (ἵστημι entry): keep Greek-bearing chunks.
    chunks = [c.strip() for c in re.split(r"[,;]", text) if c.strip()]
    parts: dict[str, list[str]] = {}
    extra: dict[str, list[str]] = {}
    filled: set[str] = set()
    raw: list[str] = []
    for chunk in chunks:
        # Strip any trailing English words (e.g. "στήσω will set").
        words = chunk.split()
        label_words: list[str] = []
        greek: list[str] = []
        for w in words:
            if GREEK_RE.search(w) and not w.startswith("-"):
                greek.append(w)
            elif GREEK_RE.search(w):
                greek.append(w)  # forms attested only in compounds, keep "-"
            elif not greek:
                label_words.append(w)
            elif w in {"or", "and"}:
                greek.append(w)
            else:
                break  # English gloss after the form
        if not greek:
            continue
        label = " ".join(label_words).strip()
        forms = _split_alternatives(" ".join(greek))
        if not label and len(forms) == 1 and " " in forms[0]:
            # "ἵστημι στήσω" (missing comma in the source): separate forms.
            forms = forms[0].split()
            for f in forms:
                _assign(f, "", parts, extra, filled)
                raw.append(f)
            continue
        raw.extend(forms)
        if label in VERB_LABELS:
            slot = VERB_LABELS[label]
        elif label:
            slot = label.rstrip(".")
        else:
            slot = _classify(forms[0], filled) or "other"
        base_slot = slot
        if slot in {"aorist-1", "aorist-2", "aorist-2-middle", "aorist"}:
            if "aorist" in filled and slot != "aorist":
                parts.setdefault(slot, []).extend(forms)
                continue
            base_slot = "aorist"
        if base_slot in SLOTS:
            parts.setdefault(base_slot, []).extend(forms)
            filled.add(base_slot)
            if slot != base_slot:
                parts.setdefault(slot, []).extend(forms)
        else:
            extra.setdefault(slot, []).extend(forms)
    lemma = parts.get("present", raw[:1])[0]
    return {"lemma": lemma, "parts": parts, "extra": extra, "raw": raw}


def parse_generic(headword: str) -> dict:
    head = re.sub(r"\([^)]*\)", "", headword).strip()
    forms = [f.strip() for f in re.split(r"[,\s]+", head) if f.strip()]
    return {"lemma": forms[0] if forms else headword, "forms": forms}


# --------------------------------------------------------------------------
# Occurrences in the reading library → examples and topic tags
# --------------------------------------------------------------------------

READING_TOPICS = {"history": "history", "philosophy": "philosophy", "mythology": "mythology"}
ELISION_MARKS = "\u2019\u02bc\u1fbd'"


def _norm(text: str) -> str:
    """Accent- and case-insensitive key (breathing kept: ὁ ≠ ὀ)."""
    d = unicodedata.normalize("NFD", text.lower())
    d = "".join(ch for ch in d if ch not in "\u0301\u0300\u0342")
    return unicodedata.normalize("NFC", d)


def all_forms(entry: dict) -> set[str]:
    """Every surface form the engine produces for the entry (accent-free keys)."""
    from app.greek.morph import decline_entry
    from app.greek.morph.verb import conjugate_entry

    forms: set[str] = {_norm(entry["lemma"])}
    for f in entry["morph"].get("forms", []) or []:
        forms.add(_norm(f))
    try:
        table = conjugate_entry(entry) if entry["kind"] == "verb" else decline_entry(entry)
    except Exception:
        table = None
    if not table:
        return forms

    def add(form: str) -> None:
        form = form.split(" ")[0]  # periphrastic: keep the participle
        form = form.replace("(ν)", "")
        if form.endswith("ν)"):
            return
        base = _norm(form)
        forms.add(base)
        if form.endswith("σι") or form.endswith("ε") and entry["kind"] == "verb":
            forms.add(base + "ν")  # movable ν
        if base.endswith("ν") and form.endswith("(ν)"):
            forms.add(base[:-1])

    if "systems" in table:
        for system in table["systems"]:
            for tb in system["tables"]:
                for c in tb["cells"]:
                    for f in c["forms"]:
                        add(f)
    else:
        for c in table["cells"]:
            fs = c["forms"]
            if isinstance(fs, dict):
                for lst in fs.values():
                    for f in lst:
                        add(f)
            else:
                for f in fs:
                    add(f)
    return {f for f in forms if f}


def index_readings(entries: list[dict]) -> None:
    """Attach `readings` (library id, sentence index, matched form) to entries
    whose forms occur in the built-in passages; add the passage's topic."""
    from app.library import load_manifest

    form_index: dict[str, list[dict]] = {}
    for e in entries:
        for f in all_forms(e):
            form_index.setdefault(f, []).append(e)
        e["readings"] = []
    token_re = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]+[" + ELISION_MARKS + "]?")
    for item in load_manifest():
        topic = READING_TOPICS.get(item["category"])
        for si, sentence in enumerate(item["sentences"]):
            seen: set[str] = set()
            for m in token_re.finditer(sentence):
                tok = m.group(0)
                elided = tok[-1] in ELISION_MARKS
                key = _norm(tok.rstrip(ELISION_MARKS))
                candidates = form_index.get(key, [])
                if not candidates and elided:
                    for v in "αεηιουω":
                        candidates = form_index.get(key + v, [])
                        if candidates:
                            break
                for e in candidates:
                    if e["id"] in seen:
                        continue
                    seen.add(e["id"])
                    e["readings"].append({"id": item["id"], "sentence": si, "form": tok})
                    if topic and topic not in e["topics"]:
                        e["topics"].append(topic)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def build(check: bool = False) -> list[dict]:
    overrides = json.loads(OVERRIDES_PATH.read_text("utf-8")) if OVERRIDES_PATH.exists() else {}
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))
    entries: list[dict] = []
    problems: list[str] = []
    seen_ids: set[str] = set()

    for row in rows:
        rank = int(row["FREQUENCY RANK"])
        dcc_headword = normalize_polytonic(row["Headword"]).strip()
        headword = attic_spelling(dcc_headword, rank)
        pos = row["Part of Speech"].strip()
        group = row["SEMANTIC GROUP"].strip()
        definition = normalize_polytonic(row["DEFINITION"]).strip()
        kind, subclass = POS_CLASSES[pos]
        ov = overrides.get(str(rank), {})
        subclass = ov.get("subclass", subclass)

        entry_subclass_override = None
        try:
            if subclass.startswith("adj") or (kind == "numeral" and DASH in headword):
                parsed = parse_adjective(headword)
                if kind == "numeral":
                    entry_subclass_override = "adj-1-2"
                elif kind == "noun":
                    kind = "adjective"
            elif kind == "noun":
                parsed = parse_noun(headword, subclass)
            elif kind == "verb":
                parsed = parse_verb(headword)
            else:
                parsed = parse_generic(headword)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{rank} {headword!r}: {exc}")
            parsed = {"lemma": headword.split()[0]}

        tier, level = tier_for(rank)
        topics = list(GROUP_TOPICS[group])
        for t in ov.get("topics", []):
            if t not in topics:
                topics.append(t)

        lemma = ov.get("lemma", parsed["lemma"])
        entry_id = slug(lemma) or f"w{rank}"
        if entry_id in seen_ids:
            entry_id = f"{entry_id}-{rank}"
        seen_ids.add(entry_id)

        entry = {
            "id": entry_id,
            "rank": rank,
            "lemma": lemma,
            "headword": headword,
            "dcc_headword": dcc_headword if dcc_headword != headword else None,
            "definition": definition,
            "short": ov.get("short", short_gloss(definition)),
            "kind": kind,
            "subclass": entry_subclass_override or subclass,
            "pos": pos,
            "group": group,
            "tier": tier,
            "level": level,
            "topics": topics,
            "notes": ov.get("notes"),
            "morph": {k: v for k, v in parsed.items() if k != "lemma"},
        }
        if "morph" in ov:
            entry["morph"].update(ov["morph"])
        entries.append(entry)

    entries.sort(key=lambda e: e["rank"])
    index_readings(entries)
    if problems:
        print("UNPARSED:")
        for p in problems:
            print("  ", p)
    if check:
        return entries
    OUT_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", "utf-8")
    covered = sum(1 for e in entries if e["readings"])
    print(f"wrote {OUT_PATH} ({len(entries)} entries, {len(problems)} problems, {covered} occur in the library)")
    return entries


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="parse only, do not write")
    ap.add_argument("--show", nargs="*", help="print parsed entries for these ranks or kinds")
    args = ap.parse_args()
    result = build(check=args.check)
    if args.show:
        for e in result:
            if str(e["rank"]) in args.show or e["kind"] in args.show:
                print(json.dumps({k: e[k] for k in ("rank", "headword", "morph")}, ensure_ascii=False))
