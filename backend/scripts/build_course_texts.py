"""Build the original Greek texts that Stage 2 lessons pair with their
adapted stories (docs/COURSE_PLAN.md §2.5, "Text tie-in").

Reads app/course_data/texts/sources.json (same shape as the reading
library's sources.json), fetches each Perseus TEI edition, resolves the
section refs, and writes app/course_data/texts/<id>.json with the passage
text and its sentences. Passages already in the reading library
(app/library_data/<id>.json) are used by id without being copied.

    python scripts/build_course_texts.py [--cache DIR] [--only ID ...]

A lesson names its original with ``"original": {"text": "<id>"}``; each
story sentence may carry ``"orig": [n, ...]``, the indices of the original's
sentences it adapts (see docs/AUTHORING.md, Stage 2).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_library import build_passage, load_tei  # noqa: E402

from app.greek import segment_sentences  # noqa: E402
from app.greek.g2p import attic_ipa  # noqa: E402
from app.tts.kokoro import prepare_kokoro_phonemes, unknown_kokoro_symbols  # noqa: E402

TEXT_DIR = BACKEND_ROOT / "app" / "course_data" / "texts"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()
    sources = json.loads((TEXT_DIR / "sources.json").read_text("utf-8"))
    problems = 0
    for spec in sources["passages"]:
        if args.only and spec["id"] not in args.only:
            continue
        try:
            item = build_passage(spec, load_tei(spec, args.cache, sources["raw_base"]))
        except Exception as exc:  # noqa: BLE001
            problems += 1
            print(f"FAIL {spec['id']}: {exc}")
            continue
        sentences = [s.text for s in segment_sentences(item["text"])]
        item["sentences"] = sentences
        unknown = sorted({ch for s in sentences for ch in unknown_kokoro_symbols(prepare_kokoro_phonemes(attic_ipa(s)))})
        (TEXT_DIR / f"{spec['id']}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", "utf-8")
        flag = f"  UNKNOWN SYMBOLS {unknown}" if unknown else ""
        print(f"{spec['id']:14s} {len(sentences):2d} sent  {item['text'][:70]!r}{flag}")
        problems += bool(unknown)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
