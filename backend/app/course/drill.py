"""Generated morphology drills.

Given skill ids and a vocabulary scope (entry ids the learner has met), build
fresh ``produce-form``, ``parse`` and ``cloze-choice`` items from the
morphology engine. Deterministic for a given seed, so a unit test's generated
section is the same on every load of the same attempt.
"""

from __future__ import annotations

import random
import re

from .data import entry_by_id
from .forms import (
    CASE_LABEL,
    GENDER_LABEL,
    GENDERS,
    NUMBER_LABEL,
    PERSON_LABEL,
    PERSONS,
    all_cells,
    cell_forms,
    describe_cell,
)

NOUN_RE = re.compile(r"^noun\.decl([123])(?:\.(cons|sigma|iota|eus))?\.(nom|gen|dat|acc|voc)\.(sg|pl)$")
NOUN_NUM_RE = re.compile(r"^noun\.decl([123])(?:\.(cons|sigma|iota|eus))?\.(sg|pl)$")  # e.g. noun.decl3.cons.pl: any case of that number
ART_RE = re.compile(r"^art\.(nom|gen|dat|acc)\.(sg|pl)$")
VERB_RE = re.compile(r"^verb\.(pres|impf|aor|fut)\.(act|mp|mid|pass)\.(ind|imp|subj|opt)\.([123](?:sg|pl))$")
EIMI_RE = re.compile(r"^verb\.eimi\.(pres|impf|fut)\.(ind|imp)\.([123](?:sg|pl))$")
INF_RE = re.compile(r"^verb\.(pres|aor)\.(act|mp|mid)\.inf$")

TENSE = {"pres": "present", "impf": "imperfect", "aor": "aorist", "fut": "future"}
VOICE = {"act": "active", "mp": "middle/passive", "mid": "middle", "pass": "passive"}
MOOD = {"ind": "indicative", "imp": "imperative", "subj": "subjunctive", "opt": "optative"}
DECL_SUBCLASS = {"1": ("noun-1",), "2": ("noun-2",), "3": ("noun-3-cons", "noun-3-sigma", "noun-3-iota", "noun-3-eus", "noun-3-irregular")}


def _clean(form: str) -> str:
    return form.replace("(ν)", "ν")


def _entries(scope_ids: list[str], kind: str, subclasses: tuple[str, ...] | None = None) -> list[dict]:
    out = []
    for entry_id in scope_ids:
        try:
            e = entry_by_id(entry_id)
        except KeyError:
            continue
        if e["kind"] != kind:
            continue
        if subclasses and e["subclass"] not in subclasses:
            continue
        out.append(e)
    return out


def _distractors(entry: dict, cell: str, rng: random.Random, n: int = 3) -> list[str]:
    """Other surface forms of the same word, distinct from the target."""
    target = {_clean(f) for f in cell_forms(entry, cell)}
    pool: list[str] = []
    for key, forms in all_cells(entry):
        if key == cell:
            continue
        # keep nominal distractors in the same gender; verbal in the same tense/mood
        if entry["kind"] != "verb" and len(key.split(".")) == 3 and key.split(".")[2] != cell.split(".")[-1]:
            continue
        if entry["kind"] == "verb":
            k, c = key.split("."), cell.split(".")
            if k[0] != c[0] or k[2] != c[2] or k[3] not in PERSONS:
                continue
        for f in forms:
            f = _clean(f)
            if f not in target and f not in pool:
                pool.append(f)
    rng.shuffle(pool)
    return pool[:n]


def _produce(item_id: str, entry: dict, cell: str, skill: str) -> dict:
    forms = cell_forms(entry, cell)
    return {
        "id": item_id,
        "type": "produce-form",
        "generated": True,
        "prompt": f"{describe_cell(entry, cell)} of {entry['lemma']}",
        "prompt_grc": describe_cell(entry, cell, greek=True) if entry["kind"] != "verb" else None,
        "lemma": entry["lemma"],
        "cell": cell,
        "gaps": [{"answers": forms}],
        "skills": [skill],
        "explain": f"{entry['headword']} — {entry['short']}. {describe_cell(entry, cell)}: {', '.join(forms)}.",
        "audio": _clean(forms[0]),
    }


def _parse(item_id: str, entry: dict, cell: str, skill: str, rng: random.Random) -> dict:
    form = _clean(rng.choice(cell_forms(entry, cell)))
    parts = cell.split(".")
    if entry["kind"] == "verb":
        tense, voice, mood, tag = parts
        groups = [
            {"id": "person", "label": "Person and number", "options": [{"id": p, "label": PERSON_LABEL[p]} for p in PERSONS]},
        ]
        answer = {"person": tag}
        # add tense as a second axis when more than one tense is in play
        if entry["subclass"] != "verb-irregular" or entry["lemma"] == "εἰμί":
            pass
    else:
        groups = [
            {"id": "case", "label": "Case", "options": [{"id": c, "label": CASE_LABEL[c]} for c in ("nom", "gen", "dat", "acc", "voc")]},
            {"id": "number", "label": "Number", "options": [{"id": n, "label": NUMBER_LABEL[n]} for n in ("sg", "pl")]},
        ]
        answer = {"case": parts[0], "number": parts[1]}
        if len(parts) == 3:
            groups.append({"id": "gender", "label": "Gender", "options": [{"id": g, "label": GENDER_LABEL[g]} for g in GENDERS]})
            answer["gender"] = parts[2]
    return {
        "id": item_id,
        "type": "parse",
        "generated": True,
        "prompt": f"Parse {form} (from {entry['lemma']}).",
        "form": form,
        "lemma": entry["lemma"],
        "cell": cell,
        "groups": groups,
        "answer": answer,
        "skills": [skill],
        "explain": f"{form} is the {describe_cell(entry, cell)} of {entry['lemma']} ({entry['short']}).",
        "audio": form,
    }


def _choice(item_id: str, entry: dict, cell: str, skill: str, rng: random.Random) -> dict | None:
    forms = [_clean(f) for f in cell_forms(entry, cell)]
    wrong = _distractors(entry, cell, rng)
    if len(wrong) < 2:
        return None
    options = [{"id": f"o{i}", "text": t} for i, t in enumerate([forms[0]] + wrong)]
    rng.shuffle(options)
    answer = next(o["id"] for o in options if o["text"] == forms[0])
    return {
        "id": item_id,
        "type": "cloze-choice",
        "generated": True,
        "prompt": f"Which is the {describe_cell(entry, cell)} of {entry['lemma']}?",
        "lemma": entry["lemma"],
        "cell": cell,
        "options": options,
        "answer": answer,
        "skills": [skill],
        "explain": f"{describe_cell(entry, cell)} of {entry['lemma']}: {', '.join(forms)}.",
        "audio": forms[0],
    }


def _plan_for_skill(skill: str, scope_ids: list[str]) -> list[tuple[dict, str]]:
    """(entry, cell) candidates for a skill id, or [] when unsupported."""
    m = NOUN_RE.match(skill) or NOUN_NUM_RE.match(skill)
    if m:
        groups = m.groups()
        decl, sub = groups[0], groups[1]
        cases = (groups[2],) if len(groups) == 4 else ("nom", "gen", "dat", "acc")
        num = groups[-1]
        subclasses = (f"noun-3-{sub}",) if sub else DECL_SUBCLASS[decl]
        out = []
        for e in _entries(scope_ids, "noun", subclasses):
            for case in cases:
                cell = f"{case}.{num}"
                if cell_forms(e, cell):
                    out.append((e, cell))
        return out
    m = ART_RE.match(skill)
    if m:
        case, num = m.groups()
        try:
            art = entry_by_id("ο")
        except KeyError:
            return []
        return [(art, f"{case}.{num}.{g}") for g in GENDERS if cell_forms(art, f"{case}.{num}.{g}")]
    m = EIMI_RE.match(skill)
    if m:
        tense, mood, tag = m.groups()
        try:
            eimi = entry_by_id("ειμι")
        except KeyError:
            return []
        cell = f"{TENSE[tense]}.active.{MOOD[mood]}.{tag}"
        return [(eimi, cell)] if cell_forms(eimi, cell) else []
    m = VERB_RE.match(skill)
    if m:
        tense, voice, mood, tag = m.groups()
        out = []
        for e in _verbs_for_voice(scope_ids, voice):
            for v in _voice_names(voice):
                cell = f"{TENSE[tense]}.{v}.{MOOD[mood]}.{tag}"
                if cell_forms(e, cell):
                    out.append((e, cell))
                    break
        return out
    m = INF_RE.match(skill)
    if m:
        tense, voice = m.groups()
        out = []
        for e in _verbs_for_voice(scope_ids, voice):
            for v in _voice_names(voice):
                cell = f"{TENSE[tense]}.{v}.infinitive.inf"
                if cell_forms(e, cell):
                    out.append((e, cell))
                    break
        return out
    if skill == "adj.agree":
        out = []
        for e in _entries(scope_ids, "adjective"):
            for cell, forms in all_cells(e):
                if forms and cell.count(".") == 2:
                    out.append((e, cell))
        return out
    return []


def _voice_names(voice: str) -> tuple[str, ...]:
    """Table voice labels to try for a skill voice: a deponent's present is
    filed under "middle", an active verb's under "middle/passive"."""
    if voice == "mp":
        return ("middle/passive", "middle")
    if voice == "mid":
        return ("middle", "middle/passive")
    return (VOICE[voice],)


def _verbs_for_voice(scope_ids: list[str], voice: str) -> list[dict]:
    """Verbs to drill in a voice: for middle/passive skills, the deponents in
    scope when there are any (a learner meets βούλομαι before ἐσθίομαι),
    otherwise every verb that has the form. εἰμί has its own skills."""
    verbs = [e for e in _entries(scope_ids, "verb") if e["lemma"] != "εἰμί"]
    if voice in ("mp", "mid"):
        deponents = [e for e in verbs if e["subclass"] == "verb-deponent"]
        if deponents:
            return deponents
    return verbs


def supported(skill: str) -> bool:
    return bool(NOUN_RE.match(skill) or NOUN_NUM_RE.match(skill) or ART_RE.match(skill) or EIMI_RE.match(skill) or VERB_RE.match(skill) or INF_RE.match(skill) or skill == "adj.agree")


def generate(skills: list[str], n: int, scope_ids: list[str], seed: int = 0, prefix: str = "drill") -> list[dict]:
    """Up to `n` items spread over the requested skills (round-robin)."""
    rng = random.Random(seed)
    plans = {s: _plan_for_skill(s, scope_ids) for s in skills}
    plans = {s: p for s, p in plans.items() if p}
    if not plans:
        return []
    items: list[dict] = []
    order = list(plans)
    used: set[tuple[str, str]] = set()
    kinds = ["produce-form", "cloze-choice", "parse"]
    i = 0
    attempts = 0
    while len(items) < n and attempts < n * 6:
        attempts += 1
        skill = order[i % len(order)]
        i += 1
        candidates = [c for c in plans[skill] if (c[0]["id"], c[1]) not in used] or plans[skill]
        entry, cell = rng.choice(candidates)
        used.add((entry["id"], cell))
        kind = kinds[len(items) % len(kinds)]
        item_id = f"{prefix}{len(items) + 1}"
        if kind == "produce-form":
            item = _produce(item_id, entry, cell, skill)
        elif kind == "parse":
            item = _parse(item_id, entry, cell, skill, rng)
        else:
            item = _choice(item_id, entry, cell, skill, rng) or _produce(item_id, entry, cell, skill)
        items.append(item)
    return items
