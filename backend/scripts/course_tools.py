"""Helpers for authoring course lessons.

    python scripts/course_tools.py scope 2.1          # words in scope before/at a lesson
    python scripts/course_tools.py find λόγος ἀγορά   # lexicon ids / MISSING
    python scripts/course_tools.py forms λόγος        # every cell the engine produces
    python scripts/course_tools.py check 2.1          # validate one lesson (+ stats)
    python scripts/course_tools.py tokens 2.1         # story tokens not yet in scope
    python scripts/course_tools.py skills noun        # skill ids matching a prefix
"""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.course import data  # noqa: E402
from app.course.forms import all_cells, entry_forms  # noqa: E402
from app.course.normalize import normalize_answer, tokens  # noqa: E402


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def cmd_scope(lesson_id: str) -> None:
    before = data.vocab_scope(lesson_id, inclusive=False) if lesson_id in data.lesson_ids() else []
    print(f"# {len(before)} words in scope before {lesson_id}")
    for i in before:
        e = data.entry_by_id(i)
        print(f"{i:16} {e['lemma']:18} {e['kind']:12} {e['short']}")


def cmd_find(lemmas: list[str]) -> None:
    by = {}
    for e in data.all_entries():
        by.setdefault(normalize_answer(e["lemma"], True), []).append(e)
    for lemma in lemmas:
        hits = by.get(normalize_answer(_nfc(lemma), True), [])
        if not hits:
            print(f"{lemma}: MISSING (add to vocab_extra-<unit>.json)")
        for e in hits:
            print(f"{lemma}: id={e['id']} kind={e['kind']} subclass={e['subclass']} source={e.get('source','dcc')} · {e['short']}")


def cmd_forms(lemma: str) -> None:
    for e in data.all_entries():
        if normalize_answer(e["lemma"], True) == normalize_answer(_nfc(lemma), True):
            for cell, forms in all_cells(e):
                print(f"{cell:44} {' / '.join(forms)}")
            return
    print("not found")


def cmd_check(lesson_id: str) -> None:
    from app.course.validate import _validate_lesson  # type: ignore[attr-defined]

    data.load_lesson.cache_clear()
    raw = data.load_lesson(lesson_id)
    before = set(data.vocab_scope(lesson_id, inclusive=False))
    new = [v["id"] for v in raw["vocab"] if v["id"] not in before]
    words = sum(len(s["text"].split()) for p in raw["story"] for s in p.get("sentences", []))
    print(f"{lesson_id}: new words {len(new)}  story words {words}  exercises {len(raw['exercises'])}  questions {len(raw.get('questions', []))}  quiz {len(raw['quiz'])}")
    print("new:", ", ".join(new))
    problems = _validate_lesson(lesson_id)
    for p in problems:
        print("✗", p)
    print(f"{len(problems)} problem(s)")


def cmd_tokens(lesson_id: str) -> None:
    data.load_lesson.cache_clear()
    raw = data.load_lesson(lesson_id)
    known: set[str] = set()
    for i in data.vocab_scope(lesson_id):
        known |= entry_forms(data.entry_by_id(i))
    names = data.names_for(lesson_id)
    for n, fs in names.items():
        known.add(normalize_answer(n))
        known |= {normalize_answer(f) for f in fs}
    glossed = {normalize_answer(g["word"]) for p in raw["story"] for s in p["sentences"] for g in s.get("glosses", [])}
    allow = {normalize_answer(k) for k in raw.get("allow", {})}
    unknown: dict[str, int] = {}
    for p in raw["story"]:
        for s in p["sentences"]:
            for t in tokens(s["text"]):
                k = normalize_answer(t)
                if k in known or k in glossed or k in allow:
                    continue
                unknown[t] = unknown.get(t, 0) + 1
    for t, n in sorted(unknown.items(), key=lambda kv: -kv[1]):
        print(f"{n:3}  {t}")
    print(f"{len(unknown)} untaught token(s)")


def cmd_skills(prefix: str) -> None:
    for s in data.load_skills()["skills"]:
        if s["id"].startswith(prefix):
            print(f"{s['id']:34} {s['label']}")


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    {"scope": lambda: cmd_scope(args[0]), "find": lambda: cmd_find(args), "forms": lambda: cmd_forms(args[0]), "check": lambda: cmd_check(args[0]), "tokens": lambda: cmd_tokens(args[0]), "skills": lambda: cmd_skills(args[0])}[cmd]()


if __name__ == "__main__":
    main()
