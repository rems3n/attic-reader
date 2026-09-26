"""Remove image records and extra-vocabulary entries that a lower-numbered
unit file already defines (the unit that teaches a word first owns its
picture and its lexicon entry).

    python scripts/dedupe_course_data.py            # all unit files
    python scripts/dedupe_course_data.py --skip u6  # leave a unit being edited alone
"""

from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "app" / "course_data"


def _key(lemma: str) -> str:
    base = unicodedata.normalize("NFD", lemma)
    return "".join(ch for ch in base if not unicodedata.combining(ch)).lower()


def _write(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", "utf-8")


def main() -> None:
    skip = {a for a in sys.argv[2:]} if len(sys.argv) > 2 and sys.argv[1] == "--skip" else set()
    seen: dict[str, str] = {}
    for path in sorted((DATA / "images").glob("manifest*.json")):
        unit = path.stem.replace("manifest-", "")
        doc = json.loads(path.read_text("utf-8"))
        keep, dropped = [], []
        for img in doc["images"]:
            if img["id"] in seen:
                dropped.append(img["id"])
            else:
                seen[img["id"]] = path.name
                keep.append(img)
        if dropped and unit not in skip:
            doc["images"] = keep
            _write(path, doc)
            print(f"{path.name}: dropped {len(dropped)} duplicate image(s): {', '.join(dropped)}")
        elif dropped:
            print(f"{path.name}: skipped ({len(dropped)} duplicate(s) left in place)")
    seen_lemmas: dict[str, str] = {}
    for path in sorted(DATA.glob("vocab_extra*.json")):
        unit = path.stem.replace("vocab_extra-", "")
        entries = json.loads(path.read_text("utf-8"))
        keep, dropped = [], []
        for e in entries:
            k = _key(e["lemma"])
            if k in seen_lemmas:
                dropped.append(e["lemma"])
            else:
                seen_lemmas[k] = path.name
                keep.append(e)
        if dropped and unit not in skip:
            _write(path, keep)
            print(f"{path.name}: dropped {len(dropped)} duplicate word(s): {', '.join(dropped)}")
        elif dropped:
            print(f"{path.name}: skipped ({len(dropped)} duplicate(s) left in place)")


if __name__ == "__main__":
    main()
