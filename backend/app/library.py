"""Built-in reading library: Perseus passages shipped as JSON under app/library_data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .greek import normalize_polytonic, segment_sentences

DATA_DIR = Path(__file__).parent / "library_data"
CATEGORIES = [
    ("history", "History"),
    ("philosophy", "Philosophy"),
    ("mythology", "Mythology"),
]
LEVELS = ("beginner", "intermediate", "advanced")

# Rough narration rate of the default voice at 1x: ~0.075 s per character of
# polytonic Greek. Used only for the "~2 min" hint before real clips exist.
SECONDS_PER_CHAR = 0.075


class LibraryError(KeyError):
    pass


@lru_cache(maxsize=1)
def load_manifest() -> list[dict]:
    ids = json.loads((DATA_DIR / "manifest.json").read_text("utf-8"))
    items = []
    for item_id in ids:
        item = json.loads((DATA_DIR / f"{item_id}.json").read_text("utf-8"))
        # Normalize line by line: speech turns are separated by newlines and
        # normalize_polytonic would collapse them.
        item["text"] = "\n".join(normalize_polytonic(line) for line in item["text"].splitlines() if line.strip())
        sentences = segment_sentences(item["text"])
        item["sentence_count"] = len(sentences)
        item["sentences"] = [s.text for s in sentences]
        item["estimated_seconds"] = round(len(item["text"]) * SECONDS_PER_CHAR)
        items.append(item)
    return items


def get_item(item_id: str) -> dict:
    for item in load_manifest():
        if item["id"] == item_id:
            return item
    raise LibraryError(item_id)


def summary(item: dict, ready_speeds: list[float] | None = None) -> dict:
    keys = ("id", "category", "level", "title", "author", "work", "ref", "blurb", "dialect", "sentence_count", "estimated_seconds")
    out = {k: item[k] for k in keys}
    out["source"] = item["source"]
    out["ready_speeds"] = ready_speeds or []
    return out
