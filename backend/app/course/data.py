"""Course content loading and resolution."""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from ..greek import attic_ipa

DATA_DIR = Path(__file__).parent.parent / "course_data"
LIBRARY_DIR = Path(__file__).parent.parent / "library_data"
EXTRA_RANK_BASE = 1000  # course-only words sort after the 524 DCC words


class CourseError(KeyError):
    pass


def _read(path: Path) -> dict | list:
    return json.loads(path.read_text("utf-8"))


def _slug(text: str) -> str:
    base = "".join(ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^Ͱ-Ͽ]+", "", base)


# ----------------------------------------------------------------- manifests

@lru_cache(maxsize=1)
def load_course() -> dict:
    return _read(DATA_DIR / "course.json")  # type: ignore[return-value]


@lru_cache(maxsize=1)
def load_skills() -> dict:
    raw = _read(DATA_DIR / "skills.json")
    by_id = {s["id"]: s for s in raw["skills"]}
    return {**raw, "by_id": by_id}


@lru_cache(maxsize=1)
def load_images() -> dict[str, dict]:
    """All image records: images/manifest.json plus any images/manifest-*.json
    (one per unit, so authors never edit the same file)."""
    out: dict[str, dict] = {}
    for path in sorted((DATA_DIR / "images").glob("manifest*.json")):
        for img in _read(path)["images"]:
            out[img["id"]] = img
    return out


@lru_cache(maxsize=1)
def extra_entries() -> list[dict]:
    """Course-only vocabulary (words the DCC list lacks), in lexicon shape."""
    from .. import vocab

    known = {e["id"] for e in vocab.load_entries()}
    out: list[dict] = []
    raws: list[dict] = []
    # vocab_extra.json plus vocab_extra-*.json (one per unit)
    for path in sorted(DATA_DIR.glob("vocab_extra*.json")):
        raws.extend(_read(path))
    seen_ids: set[str] = set()
    for n, raw in enumerate(raws):
        entry_id = raw.get("id") or _slug(raw["lemma"])
        if entry_id in known or entry_id in seen_ids:
            entry_id += "-x"
        seen_ids.add(entry_id)
        entry = {
            "id": entry_id,
            "rank": EXTRA_RANK_BASE + n + 1,
            "lemma": raw["lemma"],
            "headword": raw.get("headword", raw["lemma"]),
            "dcc_headword": None,
            "definition": raw["definition"],
            "short": raw.get("short", raw["definition"].split(",")[0].split(";")[0].strip()),
            "kind": raw["kind"],
            "subclass": raw["subclass"],
            "pos": raw.get("pos", raw["kind"]),
            "group": "Course",
            "tier": raw.get("tier", 1),
            "level": raw.get("level", "beginner"),
            "topics": raw.get("topics", ["city-life"]),
            "notes": raw.get("notes"),
            "cognates": raw.get("cognates"),
            "tags": ["course"] + (["cognates"] if raw.get("cognates") else []),
            "morph": raw.get("morph", {}),
            "readings": [],
            "source": "course",
        }
        out.append(entry)
    return out


@lru_cache(maxsize=1)
def all_entries() -> list[dict]:
    from .. import vocab

    return sorted(vocab.load_entries() + extra_entries(), key=lambda e: e["rank"])


@lru_cache(maxsize=1)
def _entry_index() -> dict[str, dict]:
    return {e["id"]: e for e in all_entries()}


def entry_by_id(entry_id: str) -> dict:
    try:
        return _entry_index()[entry_id]
    except KeyError as exc:
        raise CourseError(f"unknown vocabulary id {entry_id!r}") from exc


# ------------------------------------------------------------------- lessons

def _units() -> list[dict]:
    return [u for stage in load_course()["stages"] for u in stage["units"]]


@lru_cache(maxsize=1)
def lesson_ids() -> list[str]:
    """Every lesson id in course order (authored or planned)."""
    return [lid for unit in _units() for lid in unit["lessons"]]


def lesson_path(lesson_id: str) -> Path:
    return DATA_DIR / "lessons" / f"{lesson_id}.json"


def lesson_available(lesson_id: str) -> bool:
    return lesson_path(lesson_id).exists()


@lru_cache(maxsize=None)
def load_lesson(lesson_id: str) -> dict:
    path = lesson_path(lesson_id)
    if not path.exists():
        raise CourseError(f"no lesson {lesson_id!r}")
    raw = _read(path)
    raw.setdefault("id", lesson_id)
    # give every exercise, question and quiz item a stable id and fill engine answers
    for block in ("exercises", "questions", "quiz"):
        for n, item in enumerate(raw.get(block, [])):
            item.setdefault("id", f"{lesson_id}:{block[0]}{n + 1}")
            _fill_engine_answers(item)
    return raw


def _fill_engine_answers(item: dict) -> None:
    """A typed item may name `lemma` + `cell` instead of spelling out its
    answers; the morphology engine supplies them (and the validator checks
    any answers that are spelled out against the same table)."""
    if item.get("gaps") or not (item.get("lemma") and item.get("cell")):
        return
    from .forms import cell_forms

    entry = next((e for e in all_entries() if e["lemma"] == item["lemma"]), None)
    if entry:
        forms = cell_forms(entry, item["cell"])
        if forms:
            item["gaps"] = [{"answers": forms}]


# ------------------------------------------------------------------ originals

@lru_cache(maxsize=None)
def load_text(text_id: str) -> dict:
    """An original Greek passage a lesson or test pairs with: a course text
    (course_data/texts/<id>.json, built by scripts/build_course_texts.py) or a
    reading-library passage (library_data/<id>.json). Always has `sentences`."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9.\-]*", text_id or ""):
        raise CourseError(f"bad text id {text_id!r}")
    for folder in (DATA_DIR / "texts", LIBRARY_DIR):
        path = folder / f"{text_id}.json"
        if path.exists():
            raw = dict(_read(path))  # type: ignore[arg-type]
            if "sentences" not in raw:
                from ..greek import segment_sentences

                raw["sentences"] = [s.text for s in segment_sentences(raw.get("text", ""))]
            raw["id"] = text_id
            return raw
    raise CourseError(f"no original text {text_id!r}")


def original_record(text_id: str, note: str | None = None) -> dict:
    t = load_text(text_id)
    return {
        "id": text_id,
        "title": t.get("title"),
        "author": t.get("author"),
        "work": t.get("work"),
        "ref": t.get("ref"),
        "blurb": t.get("blurb"),
        "source": t.get("source"),
        "sentences": t["sentences"],
        "note": note,
    }


def unit_of(lesson_id: str) -> dict:
    for unit in _units():
        if lesson_id in unit["lessons"]:
            return unit
    raise CourseError(f"lesson {lesson_id!r} is not in the course manifest")


def stage_of(lesson_id: str) -> dict:
    for stage in load_course()["stages"]:
        for unit in stage["units"]:
            if lesson_id in unit["lessons"]:
                return stage
    raise CourseError(lesson_id)


def lessons_before(lesson_id: str, inclusive: bool = True) -> list[str]:
    ids = lesson_ids()
    if lesson_id not in ids:
        raise CourseError(lesson_id)
    stop = ids.index(lesson_id) + (1 if inclusive else 0)
    return [lid for lid in ids[:stop] if lesson_available(lid)]


def vocab_scope(lesson_id: str, inclusive: bool = True) -> list[str]:
    """Vocabulary entry ids introduced up to (and including) a lesson, in order."""
    seen: list[str] = []
    for lid in lessons_before(lesson_id, inclusive):
        for item in load_lesson(lid).get("vocab", []):
            if item["id"] not in seen:
                seen.append(item["id"])
    return seen


@lru_cache(maxsize=1)
def entry_lessons() -> dict[str, list[str]]:
    """entry id → lessons that introduce it (first) or use it in their list."""
    out: dict[str, list[str]] = {}
    for lid in lesson_ids():
        if not lesson_available(lid):
            continue
        for item in load_lesson(lid).get("vocab", []):
            out.setdefault(item["id"], []).append(lid)
    return out


def names_for(lesson_id: str) -> dict[str, list[str]]:
    """Proper names allowed in a lesson: course-wide plus lesson-local."""
    names = {k: list(v) for k, v in load_course().get("names", {}).items()}
    for name, forms in load_lesson(lesson_id).get("names", {}).items():
        # a lesson may add forms to a course-wide name (Ἕλλησιν) without repeating the list
        names[name] = list(dict.fromkeys(names.get(name, []) + list(forms)))
    return names


# ----------------------------------------------------------------- resolving

def vocab_summary(entry: dict, pic: str | None = None, gloss_grc: str | None = None) -> dict:
    from .. import vocab

    out = vocab.summary(entry)
    out["definition"] = entry["definition"]
    out["ipa"] = attic_ipa(entry["lemma"])
    out["pic"] = pic
    out["gloss_grc"] = gloss_grc
    out["source"] = entry.get("source", "dcc")
    return out


def image_record(image_id: str | None) -> dict | None:
    if not image_id:
        return None
    img = load_images().get(image_id)
    if not img:
        raise CourseError(f"unknown image {image_id!r}")
    return img


def resolve_lesson(lesson_id: str) -> dict:
    """Lesson JSON with vocabulary entries, images and position filled in."""
    raw = load_lesson(lesson_id)
    unit = unit_of(lesson_id)
    stage = stage_of(lesson_id)
    ids = lesson_ids()
    idx = ids.index(lesson_id)
    prev_id = next((lid for lid in reversed(ids[:idx]) if lesson_available(lid)), None)
    next_id = next((lid for lid in ids[idx + 1:] if lesson_available(lid)), None)
    out = dict(raw)
    out["unit"] = {"id": unit["id"], "n": unit["n"], "title_grc": unit["title_grc"], "title_en": unit["title_en"], "test": unit.get("test")}
    out["stage"] = {"id": stage["id"], "title_grc": stage["title_grc"], "title_en": stage["title_en"]}
    out["position"] = {"index": idx, "prev": prev_id, "next": next_id, "in_unit": unit["lessons"].index(lesson_id) + 1, "unit_size": len(unit["lessons"])}
    out["vocab"] = [vocab_summary(entry_by_id(v["id"]), v.get("pic"), v.get("gloss_grc")) for v in raw.get("vocab", [])]
    out["cover_image"] = image_record(raw.get("cover"))
    out["story"] = [
        {**para, "image_record": image_record(para.get("image"))}
        for para in raw.get("story", [])
    ]
    culture = raw.get("culture")
    out["culture"] = {**culture, "image_record": image_record(culture.get("image"))} if culture else None
    out["skills"] = [_skill_record(s) for s in raw.get("skills", [])]
    out["story_text"] = "\n".join(s["text"] for para in raw.get("story", []) for s in para.get("sentences", []))
    original = raw.get("original")
    out["original_text"] = original_record(original["text"], original.get("note")) if original else None
    return out


def _skill_record(skill_id: str) -> dict:
    skill = load_skills()["by_id"].get(skill_id)
    return {"id": skill_id, "label": skill["label"] if skill else skill_id, "paradigm": (skill or {}).get("paradigm")}


def load_test(test_id: str) -> dict:
    path = DATA_DIR / "tests" / f"{test_id}.json"
    if not path.exists():
        raise CourseError(f"no test {test_id!r}")
    raw = _read(path)
    raw.setdefault("id", test_id)
    for section in raw.get("sections", []):
        for n, item in enumerate(section.get("items", [])):
            item.setdefault("id", f"{test_id}:{section['id']}{n + 1}")
            _fill_engine_answers(item)
    return raw


def resolve_test(test_id: str, seed: int | None = None) -> dict:
    """A unit test with its generated sections filled from the drill generator."""
    from .drill import generate

    raw = load_test(test_id)
    out = dict(raw)
    scope = vocab_scope(raw["scope"])
    sections = []
    for section in raw.get("sections", []):
        items = list(section.get("items", []))
        if section.get("passage_from") and not section.get("passage"):
            # an unseen original: the passage is the text itself
            t = original_record(section["passage_from"])
            section = {**section, "passage": " ".join(t["sentences"]), "passage_source": {k: t[k] for k in ("author", "work", "ref", "source")}}
        gen = section.get("generate")
        if gen:
            items.extend(generate(gen["skills"], gen["n"], scope, seed=seed if seed is not None else gen.get("seed", 0), prefix=f"{test_id}:{section['id']}g"))
        sections.append({**section, "items": items})
    out["sections"] = sections
    out["item_count"] = sum(len(s["items"]) for s in sections)
    return out


PLACEMENT_PER_UNIT = 6
PLACEMENT_STOP_MISSES = 3
PLACEMENT_PASS = 0.6


def resolve_placement(seed: int = 0) -> dict:
    """An adaptive placement walk: for every unit with a test, a short block
    of that test's forms + sentence items (no vocabulary, no reading, no
    self-graded items). The client runs the blocks in order and stops after
    `stop_after_misses` consecutive misses or a block under `pass_score`;
    the learner is placed at the first unit not passed, and every lesson
    before it is marked skipped."""
    import random

    from .grade import SELF_TYPES

    blocks = []
    skipped: list[str] = []
    for unit in _units():
        skipped.extend(unit["lessons"])
        test_id = unit.get("test")
        if not test_id or not (DATA_DIR / "tests" / f"{test_id}.json").exists():
            continue
        test = resolve_test(test_id, seed=seed)
        rng = random.Random(f"{seed}:{test_id}")
        generated = [i for s in test["sections"] for i in s["items"] if i.get("generated")]
        authored = [i for s in test["sections"] if s["id"] not in ("vocab", "reading") and not s.get("passage") for i in s["items"] if not i.get("generated") and i["type"] not in SELF_TYPES]
        rng.shuffle(generated)
        rng.shuffle(authored)
        n_gen = min(len(generated), PLACEMENT_PER_UNIT // 2)
        items = generated[:n_gen] + authored[: PLACEMENT_PER_UNIT - n_gen]
        rng.shuffle(items)
        first_after = next((lid for lid in lesson_ids()[lesson_ids().index(unit["lessons"][-1]) + 1:] if lesson_available(lid)), None)
        blocks.append({
            "unit": unit["n"],
            "title_grc": unit["title_grc"],
            "title_en": unit["title_en"],
            "test": test_id,
            "scope": test["scope"],
            "lessons": list(skipped),
            "next_lesson": first_after,
            "items": items,
        })
    return {"blocks": blocks, "per_unit": PLACEMENT_PER_UNIT, "stop_after_misses": PLACEMENT_STOP_MISSES, "pass_score": PLACEMENT_PASS, "seed": seed}


def course_index() -> dict:
    course = load_course()
    stages = []
    for stage in course["stages"]:
        units = []
        for unit in stage["units"]:
            lessons = []
            for lid in unit["lessons"]:
                if lesson_available(lid):
                    raw = load_lesson(lid)
                    lessons.append({
                        "id": lid,
                        "title_grc": raw["title_grc"],
                        "title_en": raw["title_en"],
                        "available": True,
                        "skills": raw.get("skills", []),
                        "word_count": len(raw.get("vocab", [])),
                        "exercise_count": len(raw.get("exercises", [])) + len(raw.get("questions", [])),
                        "quiz_count": len(raw.get("quiz", [])),
                    })
                else:
                    lessons.append({"id": lid, "title_grc": "", "title_en": "", "available": False})
            units.append({**unit, "lessons": lessons, "test_available": bool(unit.get("test") and (DATA_DIR / "tests" / f"{unit['test']}.json").exists())})
        stages.append({**stage, "units": units})
    return {
        "stages": stages,
        "tracks": course.get("tracks", []),
        "skills": load_skills()["skills"],
        "families": load_skills()["families"],
        "lesson_order": lesson_ids(),
    }
