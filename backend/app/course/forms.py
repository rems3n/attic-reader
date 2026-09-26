"""Lexicon-form helpers shared by the validator and the drill generator.

Cell keys:
  nouns                ``dat.sg``
  adjectives/articles  ``dat.sg.f``
  verbs                ``present.active.indicative.3sg`` (tag = 1sg…3pl,
                       ``inf`` for the infinitive, ``m``/``f``/``n`` for the
                       participle's nominative singular, ``mg`` for its
                       masculine genitive singular)
  participles, full    ``aorist.active.participle.gen.pl.f``
  comparison           ``comp.dat.sg.f`` / ``sup.acc.pl.m`` (adjectives)
  dual                 ``nom.du`` / ``gen.du.f`` (nouns, adjectives), ``present.active.indicative.2du``
                       / ``3du`` (verbs), ``aorist.active.participle.nom.du.m``
  verbal adjectives    ``vadj.tos`` / ``vadj.teos`` (nominative singular masculine) and
                       declined ``vadj.teos.gen.sg.f``

Dual cells come after all singular/plural cells (and verbal adjectives last),
so a form that is also a singular or plural (χώρα, λόγω ~ λόγῳ) is described
by its commoner reading.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache

from ..greek.morph import decline_entry
from ..greek.morph.accent import strip_accent
from ..greek.morph.nominal import decline_adjective
from ..greek.morph.participle import participle_cells
from ..greek.morph.verb import conjugate_entry
from .normalize import normalize_answer

CASES = ("nom", "gen", "dat", "acc", "voc")
NUMBERS = ("sg", "pl")
DUAL = "du"
GENDERS = ("m", "f", "n")
PERSONS = ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl")
DUAL_PERSONS = ("2du", "3du")

CASE_LABEL = {"nom": "nominative", "gen": "genitive", "dat": "dative", "acc": "accusative", "voc": "vocative"}
NUMBER_LABEL = {"sg": "singular", "pl": "plural", "du": "dual"}
GENDER_LABEL = {"m": "masculine", "f": "feminine", "n": "neuter", "mf": "masculine/feminine"}
PERSON_LABEL = {"1sg": "1st singular", "2sg": "2nd singular", "3sg": "3rd singular", "1pl": "1st plural", "2pl": "2nd plural", "3pl": "3rd plural",
                "2du": "2nd dual", "3du": "3rd dual", "inf": "infinitive"}
VADJ_LABEL = {"tos": "verbal adjective in -τός", "teos": "verbal adjective in -τέος"}
CASE_LABEL_GRC = {"nom": "ὀνομαστική", "gen": "γενική", "dat": "δοτική", "acc": "αἰτιατική", "voc": "κλητική"}
NUMBER_LABEL_GRC = {"sg": "ἑνικός", "pl": "πληθυντικός", "du": "δυϊκός"}
GENDER_LABEL_GRC = {"m": "ἀρσενικόν", "f": "θηλυκόν", "n": "οὐδέτερον", "mf": "ἀρσενικὸν καὶ θηλυκόν"}


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
    if "id" in entry:
        return list(_all_cells_cached(entry["id"]))
    return _all_cells(entry)


@lru_cache(maxsize=None)
def _all_cells_cached(entry_id: str) -> tuple[tuple[str, list[str]], ...]:
    from .data import entry_by_id

    return tuple(_all_cells(entry_by_id(entry_id)))


def _all_cells(entry: dict) -> list[tuple[str, list[str]]]:
    table = table_for(entry)
    if not table:
        return []
    out: list[tuple[str, list[str]]] = []
    dual: list[tuple[str, list[str]]] = []
    if "systems" in table:
        vadj: list[tuple[str, list[str]]] = []
        for system in table["systems"]:
            for tb in system["tables"]:
                if tb.get("note", "").startswith("Periphrastic"):
                    continue
                if tb["tense"] == "verbal adjective":
                    vadj.extend(_verbal_adjective_rows(tb))
                    continue
                key = f"{tb['tense']}.{tb['voice']}.{tb['mood']}"
                for target, cells in ((out, tb["cells"]), (dual, tb.get("dual", []))):
                    for cell in cells:
                        # a periphrastic cell (γεγραμμένοι εἰσί(ν), λελυκὼς ὦ) is not one form: skip it
                        forms = [_clean(f) for f in cell["forms"] if f and " " not in f.strip()]
                        if forms:
                            target.append((f"{key}.{cell['tag']}", forms))
                if tb["mood"] == "participle":
                    rows = _participle_rows(tb)
                    out.extend(r for r in rows if f".{DUAL}." not in r[0])
                    dual.extend(r for r in rows if f".{DUAL}." in r[0])
        return out + dual + vadj
    for target, cells in ((out, table["cells"]), (dual, table.get("dual", []))):
        for cell in cells:
            forms = cell["forms"]
            if isinstance(forms, dict):
                for gender, lst in forms.items():
                    if lst:
                        target.append((f"{cell['case']}.{cell['number']}.{gender}", list(lst)))
            elif forms:
                target.append((f"{cell['case']}.{cell['number']}", list(forms)))
    if entry["kind"] in {"adjective", "numeral"} and table.get("comparison"):
        out.extend(_comparison_rows(table["comparison"]))
    if entry["kind"] in {"adjective", "numeral"} and table.get("adverb"):
        out.append(("adv", [_clean(a) for a in table["adverb"] if a]))  # σοφῶς, ἀκριβῶς, εὖ
    return out + dual


def _verbal_adjective_rows(tb: dict) -> list[tuple[str, list[str]]]:
    """``vadj.tos`` / ``vadj.teos`` (masc. nom. sg.) plus every case, number
    and gender of each, declined as a first/second-declension adjective
    (λυτός -ή -όν, λυτέος -έα -έον)."""
    out: list[tuple[str, list[str]]] = []
    for cell in tb["cells"]:
        if not cell["forms"]:
            continue
        m, f = cell["forms"][0], cell["forms"][1] if len(cell["forms"]) > 1 else None
        out.append((f"vadj.{cell['tag']}", [m]))
        try:
            table = decline_adjective(m, {"terminations": 3, "feminine": f or m}, "adj-1-2")
        except Exception:  # noqa: BLE001 - an odd form must not break the course
            continue
        for c in table["cells"] + table.get("dual", []):
            for gender, forms in c["forms"].items():
                if forms:
                    out.append((f"vadj.{cell['tag']}.{c['case']}.{c['number']}.{gender}", list(forms)))
    return out


def _participle_rows(tb: dict) -> list[tuple[str, list[str]]]:
    """The whole declension of a participle table (its cells give only the
    nominative singular per gender and the masculine genitive)."""
    by_tag = {c["tag"]: [_clean(f) for f in c["forms"] if f] for c in tb["cells"] if c.get("forms") and c["forms"][0]}
    if not all(k in by_tag for k in ("m", "f", "n", "mg")):
        return []
    grouped: dict[str, list[str]] = {}
    # alternative participles (ἑστηκώς / ἑστώς) are declined set by set
    for i in range(max(len(by_tag[k]) for k in ("m", "f", "n", "mg"))):
        pick = [by_tag[k][min(i, len(by_tag[k]) - 1)] for k in ("m", "f", "n", "mg")]
        for case, number, gender, form in participle_cells(*pick):
            forms = grouped.setdefault(f"{tb['tense']}.{tb['voice']}.participle.{case}.{number}.{gender}", [])
            if form not in forms:
                forms.append(form)
    return list(grouped.items())


def _comparison_rows(comparison: dict) -> list[tuple[str, list[str]]]:
    """Comparative and superlative declined in full: -τερος/-τατος as
    first/second-declension adjectives (feminine -τέρα, -τάτη), -ων/-ον
    comparatives (βελτίων, μείζων) as third declension."""
    out: dict[str, list[str]] = {}
    for prefix, key in (("comp", "comparative"), ("sup", "superlative")):
        for lemma in comparison.get(key) or []:
            lemma = _clean(lemma)
            bare = strip_accent(lemma)
            try:
                if bare.endswith("ος"):
                    fem = lemma[:-2] + ("α" if bare.endswith("ρος") else "η")
                    table = decline_adjective(lemma, {"terminations": 3, "feminine": fem}, "adj-1-2")
                elif bare.endswith("ων"):
                    table = decline_adjective(lemma, {"terminations": 2}, "adj-3-on")
                else:
                    continue
            except Exception:  # noqa: BLE001 - an odd form must not break the course
                continue
            for cell in table["cells"]:
                for gender, forms in cell["forms"].items():
                    for g in (("m", "f") if gender == "mf" else (gender,)):
                        for form in forms:
                            if form:
                                out.setdefault(f"{prefix}.{cell['case']}.{cell['number']}.{g}", []).append(form)
    return [(k, list(dict.fromkeys(v))) for k, v in out.items()]


def cell_forms(entry: dict, cell: str) -> list[str]:
    for key, forms in all_cells(entry):
        if key == cell:
            return forms
    return []


def entry_forms(entry: dict) -> set[str]:
    """Accent-insensitive keys of every surface form of the entry, including
    the lemma, listed alternative forms and movable-ν variants."""
    keys: set[str] = {normalize_answer(entry["lemma"])}
    # correlative pairs stored as one entry (μέν...δέ, εἴτε...εἴτε, οὔτε...οὔτε): each half on its own
    for sep in ("...", "…"):
        if sep in entry["lemma"]:
            keys |= {normalize_answer(part) for part in entry["lemma"].split(sep) if part.strip()}
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
    if parts[0] == "vadj":
        label = VADJ_LABEL.get(parts[1], "verbal adjective")
        if len(parts) == 5:
            return f"{label}, {CASE_LABEL[parts[2]]} {NUMBER_LABEL[parts[3]]} {GENDER_LABEL.get(parts[4], parts[4])}"
        return f"{label}, nominative singular masculine"
    if entry["kind"] == "verb":
        if len(parts) == 6:  # full participle cell
            tense, voice, _, case, number, gender = parts
            return f"{tense} {voice} participle, {CASE_LABEL[case]} {NUMBER_LABEL[number]} {GENDER_LABEL[gender]}"
        tense, voice, mood, tag = parts
        person = PERSON_LABEL.get(tag, tag)
        if mood == "participle":
            if tag == "mg":
                return f"{tense} {voice} participle, genitive singular masculine"
            return f"{tense} {voice} participle, nominative singular {GENDER_LABEL.get(tag, tag)}"
        if mood == "infinitive":
            return f"{tense} {voice} infinitive"
        return f"{tense} {voice} {mood}, {person}"
    if parts == ["adv"]:
        return "adverb"
    if parts[0] in ("comp", "sup"):
        degree = "comparative" if parts[0] == "comp" else "superlative"
        return f"{degree}, {CASE_LABEL[parts[1]]} {NUMBER_LABEL[parts[2]]} {GENDER_LABEL[parts[3]]}"
    if greek:
        label = f"{CASE_LABEL_GRC[parts[0]]} {NUMBER_LABEL_GRC[parts[1]]}"
        if len(parts) == 3:
            label += f", {GENDER_LABEL_GRC.get(parts[2], parts[2])}"
        return label
    label = f"{CASE_LABEL[parts[0]]} {NUMBER_LABEL[parts[1]]}"
    if len(parts) == 3:
        label += f", {GENDER_LABEL.get(parts[2], parts[2])}"
    return label
