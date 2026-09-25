"""Validate the course content and print a short report.

    python scripts/build_course.py          # problems, exit 1 if any
    python scripts/build_course.py --stats  # per-lesson word counts too
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.course import data  # noqa: E402
from app.course.validate import validate  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()
    if args.stats:
        for lid in data.lesson_ids():
            if not data.lesson_available(lid):
                print(f"{lid:6} (planned)")
                continue
            raw = data.load_lesson(lid)
            before = set(data.vocab_scope(lid, inclusive=False))
            new = [v["id"] for v in raw["vocab"] if v["id"] not in before]
            words = sum(len(s["text"].split()) for p in raw["story"] for s in p.get("sentences", []))
            print(f"{lid:6} {raw['title_grc'][:32]:34} new words {len(new):2}  story words {words:3}  exercises {len(raw['exercises']):2}  quiz {len(raw['quiz'])}")
    problems = validate()
    for p in problems:
        print("✗", p)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
