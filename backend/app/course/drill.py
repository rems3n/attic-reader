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
    DUAL_PERSONS,
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
VERB_RE = re.compile(r"^verb\.(pres|impf|aor|fut|perf|plpf)\.(act|mp|mid|pass)\.(ind|imp|subj|opt)\.([123](?:sg|pl))$")
EIMI_RE = re.compile(r"^verb\.eimi\.(pres|impf|fut)\.(ind|imp)\.([123](?:sg|pl))$")
INF_RE = re.compile(r"^verb\.(pres|aor|fut|perf)\.(act|mp|mid|pass)\.inf$")
# participles in any case: verb.ptc.aor.act (all cases), verb.ptc.pres.act.gen, verb.ptc.aor.pass.dat.pl
PTC_RE = re.compile(r"^verb\.ptc\.(pres|aor|fut|perf)\.(act|mp|mid|pass)(?:\.(nom|gen|dat|acc))?(?:\.(sg|pl))?$")
# comparison declined: adj.comp, adj.sup.gen, adj.comp.acc.pl
COMP_RE = re.compile(r"^adj\.(comp|sup)(?:\.(nom|gen|dat|acc))?(?:\.(sg|pl))?$")
GEN_ABS = "syntax.gen-abs"  # genitive of present/aorist active and aorist passive participles

# skills about one irregular verb: drill its finite indicative/imperative forms
LEMMA_SKILLS = {
    "verb.mi.didomi": "δίδωμι",
    "verb.mi.tithemi": "τίθημι",
    "verb.mi.deiknymi": "δείκνυμι",
    "verb.mi.histemi": "ἵστημι",
    "verb.phemi": "φημί",
    "verb.oida": "οἶδα",
    "verb.eimi-go": "εἶμι",
}

TENSE = {"pres": "present", "impf": "imperfect", "aor": "aorist", "fut": "future", "perf": "perfect", "plpf": "pluperfect"}
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
        # the dual and the verbal adjectives are not drilled: keep them out of the options
        if _is_dual(key) != _is_dual(cell) or key.startswith("vadj.") != cell.startswith("vadj."):
            continue
        k_parts, c_parts = key.split("."), cell.split(".")
        # participle / comparison cells: other cases and numbers of the same
        # participle (same tense and voice) or degree, same gender
        if len(c_parts) == 6 or c_parts[0] in ("comp", "sup"):
            if len(k_parts) != len(c_parts) or k_parts[: len(c_parts) - 3] != c_parts[: len(c_parts) - 3] or k_parts[-1] != c_parts[-1]:
                continue
        # keep nominal distractors in the same gender; verbal in the same tense/mood
        elif entry["kind"] != "verb" and len(k_parts) == 3 and k_parts[2] != c_parts[-1]:
            continue
        elif entry["kind"] == "verb":
            k, c = key.split("."), cell.split(".")
            if k[0] != c[0] or k[2] != c[2] or k[3] not in PERSONS:
                continue
        for f in forms:
            f = _clean(f)
            if f not in target and f not in pool:
                pool.append(f)
    rng.shuffle(pool)
    return pool[:n]


def _is_dual(cell: str) -> bool:
    parts = cell.split(".")
    return "du" in parts or parts[-1] in DUAL_PERSONS


def _produce(item_id: str, entry: dict, cell: str, skill: str) -> dict:
    forms = cell_forms(entry, cell)
    return {
        "id": item_id,
        "type": "produce-form",
        "generated": True,
        "prompt": f"{describe_cell(entry, cell)} of {entry['lemma']}",
        "prompt_grc": describe_cell(entry, cell, greek=True) if entry["kind"] != "verb" and cell.split(".")[0] not in ("comp", "sup") else None,
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
    if len(parts) == 6 or parts[0] in ("comp", "sup"):
        # a declined participle or comparative: parse case, number, gender
        case, number, gender = parts[-3:]
        groups = [
            {"id": "case", "label": "Case", "options": [{"id": c, "label": CASE_LABEL[c]} for c in ("nom", "gen", "dat", "acc", "voc")]},
            {"id": "number", "label": "Number", "options": [{"id": n, "label": NUMBER_LABEL[n]} for n in ("sg", "pl")]},
            {"id": "gender", "label": "Gender", "options": [{"id": g, "label": GENDER_LABEL[g]} for g in GENDERS]},
        ]
        answer = {"case": case, "number": number, "gender": gender}
        if gender not in GENDERS:  # two-ending forms: "mf"
            groups[2]["options"].insert(0, {"id": gender, "label": GENDER_LABEL.get(gender, gender)})
    elif entry["kind"] == "verb" and parts[-1] not in PERSONS:
        # an infinitive or participle cell has no person: parse tense and voice
        tense, voice = parts[0], parts[1]
        tenses = list(dict.fromkeys(["present", "imperfect", "future", "aorist", "perfect", tense]))
        voices = list(dict.fromkeys(["active", "middle", "passive", voice]))
        groups = [
            {"id": "tense", "label": "Tense", "options": [{"id": t, "label": t} for t in tenses]},
            {"id": "voice", "label": "Voice", "options": [{"id": v, "label": v} for v in voices]},
        ]
        answer = {"tense": tense, "voice": voice}
    elif entry["kind"] == "verb":
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
            done = False
            for t in _tense_names(TENSE[tense]):
                for v in _voice_names(voice):
                    cell = f"{t}.{v}.{MOOD[mood]}.{tag}"
                    if cell_forms(e, cell):
                        out.append((e, cell))
                        done = True
                        break
                if done:
                    break
        return out
    m = INF_RE.match(skill)
    if m:
        tense, voice = m.groups()
        out = []
        for e in _verbs_for_voice(scope_ids, voice):
            done = False
            for t in _tense_names(TENSE[tense]):
                for v in _voice_names(voice):
                    cell = f"{t}.{v}.infinitive.inf"
                    if cell_forms(e, cell):
                        out.append((e, cell))
                        done = True
                        break
                if done:
                    break
        return out
    if skill in LEMMA_SKILLS:
        lemma = LEMMA_SKILLS[skill]
        out = []
        for e in _entries(scope_ids, "verb"):
            if e["lemma"] != lemma:
                continue
            for cell, forms in all_cells(e):
                parts = cell.split(".")
                # active voice only: what Units 7–10 teach (ἵστημι's intransitive root aorist is active too)
                basic = parts[0] in ("present", "imperfect", "aorist", "root aorist", "future") or lemma == "οἶδα"
                if basic and len(parts) == 4 and parts[1] == "active" and parts[2] in ("indicative", "imperative") and parts[3] in PERSONS and forms:
                    out.append((e, cell))
        return out
    m = PTC_RE.match(skill)
    if m or skill == GEN_ABS:
        if m:
            tense, voice, case, number = m.groups()
            combos = [(TENSE[tense], voice)]
            cases = (case,) if case else ("nom", "gen", "dat", "acc")
        else:
            combos = [("present", "act"), ("aorist", "act"), ("aorist", "pass")]
            cases, number = ("gen",), None
        numbers = (number,) if number else ("sg", "pl")
        out = []
        for tense_name, voice in combos:
            for e in _verbs_for_voice(scope_ids, voice):
                found = False
                for t in _tense_names(tense_name):
                    for v in _voice_names(voice):
                        for c in cases:
                            for num in numbers:
                                for g in GENDERS:
                                    cell = f"{t}.{v}.participle.{c}.{num}.{g}"
                                    if cell_forms(e, cell):
                                        out.append((e, cell))
                                        found = True
                        if found:
                            break
                    if found:
                        break
        return out
    m = COMP_RE.match(skill)
    if m:
        degree, case, number = m.groups()
        cases = (case,) if case else ("nom", "gen", "dat", "acc")
        numbers = (number,) if number else ("sg", "pl")
        out = []
        for e in _entries(scope_ids, "adjective"):
            for c in cases:
                for num in numbers:
                    for g in GENDERS:
                        cell = f"{degree}.{c}.{num}.{g}"
                        if cell_forms(e, cell):
                            out.append((e, cell))
        return out
    if skill == "adj.agree":
        out = []
        for e in _entries(scope_ids, "adjective"):
            for cell, forms in all_cells(e):
                if forms and cell.count(".") == 2 and not _is_dual(cell):
                    out.append((e, cell))
        return out
    return []


def _voice_names(voice: str) -> tuple[str, ...]:
    """Table voice labels to try for a skill voice: a deponent's present is
    filed under "middle", an active verb's under "middle/passive"; the
    present-system passive is the middle/passive table."""
    if voice == "mp":
        return ("middle/passive", "middle")
    if voice == "mid":
        return ("middle", "middle/passive")
    if voice == "pass":
        return ("passive", "middle/passive")
    return (VOICE[voice],)


def _tense_names(tense: str) -> tuple[str, ...]:
    """Table tense labels for a skill tense: second aorist passives (ἐτάφην,
    διεφθάρην) and root aorists (ἔστην) have their own labels."""
    if tense == "aorist":
        return ("aorist", "second aorist", "root aorist")
    return (tense,)


def _verbs_for_voice(scope_ids: list[str], voice: str) -> list[dict]:
    """Verbs to drill in a voice: for middle/passive skills, the deponents in
    scope when there are any (a learner meets βούλομαι before ἐσθίομαι),
    otherwise every verb that has the form. εἰμί has its own skills."""
    verbs = [e for e in _entries(scope_ids, "verb") if e["lemma"] != "εἰμί"]
    if voice == "pass":
        # deponents have no passive meaning; drill real passives
        return [e for e in verbs if e["subclass"] != "verb-deponent"]
    if voice in ("mp", "mid"):
        deponents = [e for e in verbs if e["subclass"] == "verb-deponent"]
        if deponents:
            return deponents
    return verbs


def supported(skill: str) -> bool:
    return bool(NOUN_RE.match(skill) or NOUN_NUM_RE.match(skill) or ART_RE.match(skill) or EIMI_RE.match(skill) or VERB_RE.match(skill) or INF_RE.match(skill) or PTC_RE.match(skill) or COMP_RE.match(skill) or skill in LEMMA_SKILLS or skill in (GEN_ABS, "adj.agree"))


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
        elif kind == "parse" and not cell.endswith(".mf"):  # the parse groups offer m / f / n only
            item = _parse(item_id, entry, cell, skill, rng)
        else:
            item = _choice(item_id, entry, cell, skill, rng) or _produce(item_id, entry, cell, skill)
        items.append(item)
    return items
