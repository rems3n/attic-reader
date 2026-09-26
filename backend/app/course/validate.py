"""Authoring rules for course content (docs/COURSE_PLAN.md §8).

`validate()` returns a list of human-readable problems; the test suite
asserts it is empty, and scripts/build_course.py prints it.
"""

from __future__ import annotations

from ..greek import attic_ipa
from ..tts.kokoro import prepare_kokoro_phonemes, unknown_kokoro_symbols
from . import data
from .forms import cell_forms, entry_forms
from .grade import ALL_TYPES, CHOICE_TYPES, SELF_TYPES, TYPED_TYPES
from .normalize import answers_match, expand_movable, normalize_answer, tokens

MAX_NEW_WORDS = 12
MIN_QUIZ, MAX_QUIZ = 5, 10



# elision marks as they occur in authored and Perseus text: ’ ' ʼ ᾽
ELISION_MARKS = ("\u2019", "'", "\u02bc", "\u1fbd")
# an elided consonant before a rough breathing is aspirated: ἐφ’ ← ἐπί, καθ’ ← κατά, ἀνθ’ ← ἀντί
DEASPIRATE = {"φ": "π", "θ": "τ", "χ": "κ"}

def validate() -> list[str]:
    problems: list[str] = []
    problems += _validate_manifest()
    problems += _validate_images()
    problems += _validate_extras()
    for lid in data.lesson_ids():
        if data.lesson_available(lid):
            try:
                problems += _validate_lesson(lid)
            except (ValueError, KeyError, TypeError) as exc:  # malformed JSON or shape
                problems.append(f"lesson {lid}: cannot load ({exc})")
    for unit in [u for s in data.load_course()["stages"] for u in s["units"]]:
        if unit.get("test") and (data.DATA_DIR / "tests" / f"{unit['test']}.json").exists():
            try:
                problems += _validate_test(unit["test"])
            except (ValueError, KeyError, TypeError) as exc:
                problems.append(f"test {unit['test']}: cannot load ({exc})")
    return problems


def _validate_manifest() -> list[str]:
    out = []
    ids = data.lesson_ids()
    if len(ids) != len(set(ids)):
        out.append("course.json: duplicate lesson ids")
    for path in (data.DATA_DIR / "lessons").glob("*.json"):
        if path.stem not in ids:
            out.append(f"{path.name}: lesson file not listed in course.json")
    return out


def _validate_images() -> list[str]:
    out = []
    seen: dict[str, str] = {}
    for path in sorted((data.DATA_DIR / "images").glob("manifest*.json")):
        try:
            ids = [img["id"] for img in data._read(path)["images"]]
        except (ValueError, KeyError, TypeError) as exc:
            out.append(f"{path.name}: cannot load ({exc})")
            continue
        for img_id in ids:
            if img_id in seen:
                out.append(f"image {img_id}: defined in both {seen[img_id]} and {path.name}")
            seen[img_id] = path.name
    for img_id, img in data.load_images().items():
        for key in ("alt_grc", "alt_en", "credit", "license"):
            if not img.get(key):
                out.append(f"image {img_id}: missing {key}")
        placeholder = img.get("license") == "placeholder"
        if not placeholder:
            if img.get("svg"):
                # our own diagram, drawn as a theme-aware SVG component in the frontend
                if img.get("kind") != "diagram":
                    out.append(f"image {img_id}: only diagrams can be inline SVG")
                continue
            if not img.get("file"):
                out.append(f"image {img_id}: missing file")
            if not img.get("source_url") and not img["credit"].startswith("Attic Reader"):
                out.append(f"image {img_id}: missing source_url")
            if not any(img["license"].startswith(p) for p in ("CC0", "CC BY")):
                out.append(f"image {img_id}: licence {img['license']!r} is not Creative Commons")
    return out


def _validate_extras() -> list[str]:
    out = []
    from .. import vocab

    core = {e["lemma"] for e in vocab.load_entries()}
    seen: dict[str, str] = {}
    for path in sorted(data.DATA_DIR.glob("vocab_extra*.json")):
        try:
            lemmas = [raw["lemma"] for raw in data._read(path)]
        except (ValueError, KeyError, TypeError) as exc:
            out.append(f"{path.name}: cannot load ({exc})")
            continue
        for lemma in lemmas:
            key = normalize_answer(lemma, True)
            if key in seen:
                out.append(f"vocab_extra: {lemma} is defined in both {seen[key]} and {path.name} (keep the unit that teaches it first)")
            seen[key] = path.name
    for e in data.extra_entries():
        if e["lemma"] in core:
            out.append(f"vocab_extra: {e['lemma']} duplicates a DCC entry")
        if e["kind"] in {"noun", "verb", "adjective"} and not entry_forms(e) - {normalize_answer(e["lemma"])}:
            out.append(f"vocab_extra: {e['lemma']} produces no forms (check subclass/morph)")
    return out


def _validate_lesson(lid: str) -> list[str]:
    out: list[str] = []
    raw = data.load_lesson(lid)
    stage = data.stage_of(lid)["id"]
    prefix = f"lesson {lid}"
    for key in ("title_grc", "title_en", "story", "vocab", "exercises", "quiz", "skills"):
        if key not in raw:
            out.append(f"{prefix}: missing {key}")
    if out:
        return out

    skills = data.load_skills()["by_id"]
    for s in raw["skills"]:
        if s not in skills:
            out.append(f"{prefix}: unknown skill {s}")

    # vocabulary
    scope_before = set(data.vocab_scope(lid, inclusive=False))
    new_ids = []
    for v in raw["vocab"]:
        try:
            data.entry_by_id(v["id"])
        except KeyError:
            out.append(f"{prefix}: unknown vocab id {v['id']}")
            continue
        if v["id"] not in scope_before:
            new_ids.append(v["id"])
        if v.get("pic") and v["pic"] not in data.load_images():
            out.append(f"{prefix}: vocab {v['id']} references unknown image {v['pic']}")
    if stage != "0" and len(new_ids) > MAX_NEW_WORDS:
        out.append(f"{prefix}: {len(new_ids)} new words (max {MAX_NEW_WORDS})")

    # controlled vocabulary in the story
    scope_ids = data.vocab_scope(lid)
    known: set[str] = set()
    for entry_id in scope_ids:
        try:
            known |= entry_forms(data.entry_by_id(entry_id))
        except KeyError:
            pass
    names = data.names_for(lid)
    for name, forms in names.items():
        known.add(normalize_answer(name))
        known |= {normalize_answer(f) for f in forms}
    allow = {normalize_answer(k): v for k, v in raw.get("allow", {}).items()}
    glossed: set[str] = set()  # a gloss holds for the rest of the lesson (LOGOS glosses once)
    for pi, para in enumerate(raw["story"]):
        if para.get("image") and para["image"] not in data.load_images():
            out.append(f"{prefix}: story paragraph {pi} references unknown image {para['image']}")
        for si, sent in enumerate(para.get("sentences", [])):
            glossed |= {normalize_answer(g["word"]) for g in sent.get("glosses", [])}
            for g in sent.get("glosses", []):
                if g.get("kind") == "pic" and g["value"] not in data.load_images():
                    out.append(f"{prefix}: gloss image {g['value']} unknown ({sent['text'][:30]})")
            for tok in tokens(sent["text"]):
                key = normalize_answer(tok)
                if key in known or key in glossed or key in allow:
                    continue
                if tok.endswith(ELISION_MARKS):  # elided: ἀλλ’, δʼ, ἐφ’ (ἐπί before a rough breathing)
                    stem = normalize_answer(tok[:-1])
                    stems = {stem}
                    if stem[-1:] in DEASPIRATE:
                        stems.add(stem[:-1] + DEASPIRATE[stem[-1]])
                    pool = known | glossed
                    if len(stem) <= 1:
                        # δ’, τ’, γ’, μ’, σ’: only the one-syllable word the mark stands for (δέ, τε, γε, με, σε)
                        if any(s + v in pool for s in stems for v in "εαοι"):
                            continue
                    elif any(k.startswith(s) for s in stems for k in pool):
                        continue
                out.append(f"{prefix}: story {pi}.{si} uses {tok!r} before it is taught (gloss it or add it to vocab/allow)")
            unknown = unknown_kokoro_symbols(prepare_kokoro_phonemes(attic_ipa(sent["text"])))
            if unknown:
                out.append(f"{prefix}: story {pi}.{si} has symbols the voice cannot say: {unknown}")

    # exercises and quiz
    exercise_skills: set[str] = set()
    for block in ("exercises", "questions", "quiz"):
        for item in raw.get(block, []):
            out += [f"{prefix} {block} {item.get('id')}: {p}" for p in _validate_item(item, scope_ids)]
            exercise_skills |= set(item.get("skills", []))
    for s in raw["skills"]:
        if s in skills and s not in exercise_skills:
            out.append(f"{prefix}: skill {s} has no exercise")
    nq = len(raw["quiz"])
    if not MIN_QUIZ <= nq <= MAX_QUIZ:
        out.append(f"{prefix}: quiz has {nq} items (want {MIN_QUIZ}–{MAX_QUIZ})")
    if raw.get("cover") and raw["cover"] not in data.load_images():
        out.append(f"{prefix}: unknown cover image {raw['cover']}")
    culture = raw.get("culture")
    if culture and culture.get("image") and culture["image"] not in data.load_images():
        out.append(f"{prefix}: unknown culture image {culture['image']}")
    for p in raw.get("grammar", {}).get("paradigms", []):
        from ..greek.morph import paradigms

        try:
            paradigms.get(p)
        except KeyError:
            out.append(f"{prefix}: unknown paradigm {p}")
    out += _validate_original(prefix, raw)
    return out


def _validate_passage(section: dict, scope_lesson: str, scope_ids: list[str]) -> list[str]:
    """An authored unseen passage in a unit test uses only what the unit has
    taught (names and the section's own `allow` excepted): a learner who
    passed the lessons can read it without help."""
    known: set[str] = set()
    for i in scope_ids:
        known |= entry_forms(data.entry_by_id(i))
    for n, fs in data.names_for(scope_lesson).items():
        known.add(normalize_answer(n))
        known |= {normalize_answer(f) for f in fs}
    allow = {normalize_answer(k) for k in list(section.get("allow", {})) + list(section.get("glosses", {}))}
    unknown = []
    for tok in tokens(section["passage"]):
        key = normalize_answer(tok)
        if key in known or key in allow:
            continue
        if tok.endswith(ELISION_MARKS) and any(k.startswith(normalize_answer(tok[:-1])) for k in known):
            continue
        unknown.append(tok)
    return [f"unseen passage uses untaught {', '.join(sorted(set(unknown)))} (teach it, or gloss it in the section's `glosses`)"] if unknown else []


def _validate_original(prefix: str, raw: dict) -> list[str]:
    """A lesson paired with an original text: the text must exist and each
    story sentence's `orig` indices must point into it."""
    out: list[str] = []
    original = raw.get("original")
    orig_refs = [(pi, si, s["orig"]) for pi, p in enumerate(raw.get("story", [])) for si, s in enumerate(p.get("sentences", [])) if "orig" in s]
    if not original:
        if orig_refs:
            out.append(f"{prefix}: story sentences carry `orig` but the lesson names no original text")
        return out
    try:
        n = len(data.load_text(original.get("text", ""))["sentences"])
    except data.CourseError as exc:
        return [f"{prefix}: {exc}"]
    for pi, si, refs in orig_refs:
        if not isinstance(refs, list) or not all(isinstance(i, int) and 0 <= i < n for i in refs):
            out.append(f"{prefix}: story {pi}.{si} orig {refs!r} out of range (original has {n} sentences)")
    return out


def _validate_item(item: dict, scope_ids: list[str]) -> list[str]:
    out = []
    t = item.get("type")
    if t not in ALL_TYPES:
        return [f"unknown type {t!r}"]
    if not item.get("skills"):
        out.append("no skills")
    else:
        skills = data.load_skills()["by_id"]
        out += [f"unknown skill {s}" for s in item["skills"] if s not in skills]
    if not item.get("prompt") and t not in {"listen-pick", "dictation"}:
        out.append("no prompt")
    if t in CHOICE_TYPES or (t == "answer-grc" and item.get("options")):
        options = item.get("options") or ([{"id": "true"}, {"id": "false"}] if t == "true-false-grc" else [])
        ids = [o["id"] for o in options]
        if len(ids) < 2 or len(ids) != len(set(ids)):
            out.append("options must be ≥ 2 and unique")
        if item.get("answer") not in ids:
            out.append("answer is not an option id")
        for o in options:
            if o.get("image") and o["image"] not in data.load_images():
                out.append(f"option image {o['image']} unknown")
    elif t in TYPED_TYPES:
        gaps = item.get("gaps") or ([{"answers": item["answers"]}] if item.get("answers") else [])
        if item.get("lemma") and item.get("cell"):
            entry = _entry_by_lemma(item["lemma"], scope_ids)
            if not entry:
                out.append(f"lemma {item['lemma']} not in scope")
            else:
                forms = cell_forms(entry, item["cell"])
                if not forms:
                    out.append(f"{item['lemma']} has no cell {item['cell']}")
                elif not gaps:
                    item["gaps"] = gaps = [{"answers": forms}]
                elif not all(any(answers_match(v, forms, True) for v in expand_movable(a)) for a in gaps[0]["answers"]):
                    out.append(f"answers {gaps[0]['answers']} disagree with the engine {forms}")
        if not gaps:
            out.append("typed item needs gaps or answers")
        for g in gaps:
            if not g.get("answers"):
                out.append("gap with no answers")
            for a in g.get("answers", []):
                for v in expand_movable(a):
                    if not normalize_answer(v):
                        out.append(f"answer {a!r} normalizes to nothing")
        template = item.get("template")
        if template is not None and template.count("___") != len(gaps):
            out.append("template gap count differs from gaps")
    elif t == "parse":
        if not item.get("form") or not item.get("groups") or not item.get("answer"):
            out.append("parse needs form, groups, answer")
        else:
            for g in item["groups"]:
                if item["answer"].get(g["id"]) not in [o["id"] for o in g["options"]]:
                    out.append(f"parse answer for {g['id']} not among options")
    elif t == "locate":
        toks = item.get("tokens") or tokens(item.get("sentence", ""))
        if not toks:
            out.append("locate needs tokens or sentence")
        elif any(not 0 <= i < len(toks) for i in item.get("answer", [])):
            out.append("locate answer index out of range")
    elif t == "reorder":
        if not item.get("tokens") or not item.get("answers"):
            out.append("reorder needs tokens and answers")
        else:
            for a in item["answers"]:
                if sorted(normalize_answer(x) for x in tokens(a)) != sorted(normalize_answer(x) for x in item["tokens"]):
                    out.append(f"reorder answer {a!r} does not use exactly the tokens")
    elif t in {"match", "word-family"}:
        pairs = item.get("pairs") or []
        if len(pairs) < 2:
            out.append("match needs ≥ 2 pairs")
        lefts = [p["left"] for p in pairs]
        rights = [p["right"] for p in pairs]
        if len(set(lefts)) != len(lefts) or len(set(rights)) != len(rights):
            out.append("match sides must be unique")
    elif t in SELF_TYPES:
        if not item.get("model"):
            out.append("self-graded item needs a model answer")
    if item.get("image") and item["image"] not in data.load_images():
        out.append(f"unknown image {item['image']}")
    return out


def _entry_by_lemma(lemma: str, scope_ids: list[str]) -> dict | None:
    for entry_id in scope_ids:
        try:
            e = data.entry_by_id(entry_id)
        except KeyError:
            continue
        if e["lemma"] == lemma:
            return e
    for e in data.all_entries():
        if e["lemma"] == lemma:
            return e
    return None


def _validate_test(test_id: str) -> list[str]:
    out = []
    raw = data.load_test(test_id)
    prefix = f"test {test_id}"
    if raw.get("scope") not in data.lesson_ids():
        out.append(f"{prefix}: scope must be a lesson id")
        return out
    scope_ids = data.vocab_scope(raw["scope"])
    if not raw.get("sections"):
        out.append(f"{prefix}: no sections")
    for section in raw.get("sections", []):
        for key in ("id", "title"):
            if not section.get(key):
                out.append(f"{prefix}: section missing {key}")
        if section.get("passage_from"):
            try:
                data.load_text(section["passage_from"])
            except data.CourseError as exc:
                out.append(f"{prefix}: {exc}")
        elif section.get("passage"):
            out += [f"{prefix} {section.get('id')}: {p}" for p in _validate_passage(section, raw["scope"], scope_ids)]
        for item in section.get("items", []):
            out += [f"{prefix} {section.get('id')} {item.get('id')}: {p}" for p in _validate_item(item, scope_ids)]
        gen = section.get("generate")
        if gen:
            from .drill import supported

            for s in gen.get("skills", []):
                if not supported(s):
                    out.append(f"{prefix}: cannot generate items for skill {s}")
    if raw.get("pass_score") is None:
        out.append(f"{prefix}: missing pass_score")
    return out
