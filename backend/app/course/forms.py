"""Lexicon-form helpers shared by the validator and the drill generator.

Cell keys:
  nouns                ``dat.sg``
  adjectives/articles  ``dat.sg.f``
  verbs                ``present.active.indicative.3sg`` (tag = 1sg…3pl,
                       ``inf`` for the infinitive, ``m``/``f``/``n`` for the
                       participle's nominative singular)
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

from ..greek.morph import decline_entry
from ..greek.morph.verb import conjugate_entry
from .normalize import normalize_answer

CASES = ("nom", "gen", "dat", "acc", "voc")
NUMBERS = ("sg", "pl")
GENDERS = ("m", "f", "n")
PERSONS = ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl")

CASE_LABEL = {"nom": "nominative", "gen": "genitive", "dat": "dative", "acc": "accusative", "voc": "vocative"}
NUMBER_LABEL = {"sg": "singular", "pl": "plural"}
GENDER_LABEL = {"m": "masculine", "f": "feminine", "n": "neuter"}
PERSON_LABEL = {"1sg": "1st singular", "2sg": "2nd singular", "3sg": "3rd singular", "1pl": "1st plural", "2pl": "2nd plural", "3pl": "3rd plural", "inf": "infinitive"}
CASE_LABEL_GRC = {"nom": "ὀνομαστική", "gen": "γενική", "dat": "δοτική", "acc": "αἰτιατική", "voc": "κλητική"}
NUMBER_LABEL_GRC = {"sg": "ἑνικός", "pl": "πληθυντικός"}
GENDER_LABEL_GRC = {"m": "ἀρσενικόν", "f": "θηλυκόν", "n": "οὐδέτερον"}


def _table(entry: dict) -> dict | None:
    try:
        return conjugate_entry(entry) if entry["kind"] == "verb" else decline_entry(entry)
    except Exception:  # noqa: BLE001 - a broken table must not break the course
        return None


@lru_cache(maxsize=None)
def _table_cached(entry_id: str) -> dict | None:
    from .data import entry_by_id

    return _table(entry_by_id(entry_id))


def table_for(entry: dict) -> dict | None:
    return _table_cached(entry["id"]) if "id" in entry else _table(entry)


def _clean(form: str) -> str:
    return form.split(" ")[0]


def all_cells(entry: dict) -> list[tuple[str, list[str]]]:
    """Every (cell_key, forms) pair the engine produces for the entry."""
    table = table_for(entry)
    if not table:
        return []
    out: list[tuple[str, list[str]]] = []
    if "systems" in table:
        for system in table["systems"]:
            for tb in system["tables"]:
                if tb.get("note", "").startswith("Periphrastic"):
                    continue
                for cell in tb["cells"]:
                    forms = [_clean(f) for f in cell["forms"] if f]
                    if forms:
                        out.append((f"{tb['tense']}.{tb['voice']}.{tb['mood']}.{cell['tag']}", forms))
        return out
    for cell in table["cells"]:
        forms = cell["forms"]
        if isinstance(forms, dict):
            for gender, lst in forms.items():
                if lst:
                    out.append((f"{cell['case']}.{cell['number']}.{gender}", list(lst)))
        elif forms:
            out.append((f"{cell['case']}.{cell['number']}", list(forms)))
    return out


def cell_forms(entry: dict, cell: str) -> list[str]:
    for key, forms in all_cells(entry):
        if key == cell:
            return forms
    return []


def entry_forms(entry: dict) -> set[str]:
    """Accent-insensitive keys of every surface form of the entry, including
    the lemma, listed alternative forms and movable-ν variants."""
    keys: set[str] = {normalize_answer(entry["lemma"])}
    for f in entry.get("morph", {}).get("forms", []) or []:
        keys.add(normalize_answer(f))
    for _, forms in all_cells(entry):
        for f in forms:
            for variant in _movable_variants(f):
                keys.add(normalize_answer(variant))
    return {k for k in keys if k}


def _movable_variants(form: str) -> list[str]:
    if "(ν)" in form:
        return [form.replace("(ν)", "ν"), form.replace("(ν)", "")]
    return [unicodedata.normalize("NFC", form)]


def describe_cell(entry: dict, cell: str, greek: bool = False) -> str:
    """Human label for a cell key: 'dative singular' / 'δοτικὴ ἑνικοῦ'."""
    parts = cell.split(".")
    if entry["kind"] == "verb":
        tense, voice, mood, tag = parts
        person = PERSON_LABEL.get(tag, tag)
        if mood == "participle":
            return f"{tense} {voice} participle, {GENDER_LABEL.get(tag, tag)} nominative singular"
        if mood == "infinitive":
            return f"{tense} {voice} infinitive"
        return f"{tense} {voice} {mood}, {person}"
    if greek:
        label = f"{CASE_LABEL_GRC[parts[0]]} {NUMBER_LABEL_GRC[parts[1]]}"
        if len(parts) == 3:
            label += f", {GENDER_LABEL_GRC[parts[2]]}"
        return label
    label = f"{CASE_LABEL[parts[0]]} {NUMBER_LABEL[parts[1]]}"
    if len(parts) == 3:
        label += f", {GENDER_LABEL[parts[2]]}"
    return label
