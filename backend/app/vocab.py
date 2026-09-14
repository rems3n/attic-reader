"""DCC Greek Core Vocabulary: lexicon loading, facets and summaries.

The lexicon is built offline by scripts/build_vocab.py into
app/vocab_data/core.json (see LICENSE-DCC.txt for attribution).
"""

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "vocab_data"

ATTRIBUTION = (
    "Vocabulary: DCC Ancient Greek Core Vocabulary, Dickinson College "
    "Commentaries (Christopher Francese et al.), CC BY-SA."
)
ATTRIBUTION_URL = "https://dcc.dickinson.edu/greek-core-list"

TOPICS = [
    ("mythology", "Mythology"),
    ("history", "History & war"),
    ("philosophy", "Philosophy & mind"),
    ("city-life", "City life in Athens"),
    ("core", "Core (function words)"),
]
TIER_LABELS = {1: "beginner", 2: "elementary", 3: "intermediate", 4: "advanced"}
KIND_LABELS = {
    "noun": "Nouns",
    "verb": "Verbs",
    "adjective": "Adjectives",
    "pronoun": "Pronouns",
    "numeral": "Numerals",
    "article": "Article",
    "preposition": "Prepositions",
    "adverb": "Adverbs",
    "conjunction": "Conjunctions",
    "interjection": "Interjections",
}

SUMMARY_KEYS = (
    "id", "rank", "lemma", "headword", "short", "kind", "subclass", "pos",
    "group", "tier", "level", "topics",
)


class VocabError(KeyError):
    pass


@lru_cache(maxsize=1)
def load_entries() -> list[dict]:
    entries = json.loads((DATA_DIR / "core.json").read_text("utf-8"))
    return sorted(entries, key=lambda e: e["rank"])


@lru_cache(maxsize=1)
def _by_id() -> dict[str, dict]:
    return {e["id"]: e for e in load_entries()}


def get_entry(entry_id: str) -> dict:
    try:
        return _by_id()[entry_id]
    except KeyError as exc:
        raise VocabError(entry_id) from exc


def summary(entry: dict) -> dict:
    out = {k: entry[k] for k in SUMMARY_KEYS}
    out["readings"] = [r["id"] for r in entry.get("readings", [])]
    return out


def detail(entry: dict) -> dict:
    """Full entry for the word page: definition, notes, principal parts, IPA."""
    from .greek import attic_ipa

    out = dict(entry)
    out["ipa"] = attic_ipa(entry["lemma"])
    out["dcc_url"] = f"{ATTRIBUTION_URL.rsplit('/', 1)[0]}/greek-core/{entry['lemma'].split()[0]}"
    return out


def facets(entries: list[dict] | None = None) -> dict:
    """Counts per topic, DCC group, part of speech, tier and reading."""
    items = entries if entries is not None else load_entries()
    topic_counts = Counter(t for e in items for t in e["topics"])
    group_counts = Counter(e["group"] for e in items)
    kind_counts = Counter(e["kind"] for e in items)
    pos_counts = Counter(e["pos"] for e in items)
    tier_counts = Counter(e["tier"] for e in items)
    reading_counts = Counter(r["id"] for e in items for r in e.get("readings", []))
    return {
        "topics": [{"id": tid, "label": label, "count": topic_counts.get(tid, 0)} for tid, label in TOPICS],
        "groups": [{"id": g, "label": g, "count": n} for g, n in sorted(group_counts.items(), key=lambda kv: -kv[1])],
        "kinds": [{"id": k, "label": KIND_LABELS.get(k, k), "count": n} for k, n in kind_counts.most_common()],
        "pos": [{"id": p, "label": p, "count": n} for p, n in sorted(pos_counts.items())],
        "tiers": [
            {"id": t, "label": TIER_LABELS[t], "count": tier_counts.get(t, 0), "ranks": _tier_ranks(t)}
            for t in sorted(TIER_LABELS)
        ],
        "readings": [{"id": r, "count": n} for r, n in sorted(reading_counts.items())],
    }


def _tier_ranks(tier: int) -> str:
    bounds = {1: "1–125", 2: "126–250", 3: "251–375", 4: "376–524"}
    return bounds[tier]
