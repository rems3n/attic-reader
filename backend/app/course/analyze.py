"""Guided reading (Stage 4): which lexicon words a Greek text uses.

Maps every word token of any text to DCC core or course entries through the
morphology engine's forms (accent-insensitive), and reports how much of the
text the core list covers. Names (capitalised and unknown) are left out of
the coverage count, like a reader's commentary would.
"""

from __future__ import annotations

from functools import lru_cache

from . import data
from .forms import entry_forms
from .normalize import normalize_answer, tokens

ELISION = ("’", "'", "ʼ", "᾽")
DEASPIRATE = {"φ": "π", "θ": "τ", "χ": "κ"}


@lru_cache(maxsize=1)
def form_index() -> dict[str, tuple[str, ...]]:
    """Normalized form → entry ids, most frequent (lowest rank) first."""
    out: dict[str, list[str]] = {}
    for e in data.all_entries():  # sorted by rank
        for key in entry_forms(e):
            out.setdefault(key, []).append(e["id"])
    return {k: tuple(v) for k, v in out.items()}


def _lookup(tok: str) -> tuple[str, ...]:
    idx = form_index()
    hit = idx.get(normalize_answer(tok))
    if hit:
        return hit
    if tok.endswith(ELISION):  # ἀλλ’ → ἀλλά, ἐφ’ → ἐπί, δ’ → δέ
        stem = normalize_answer(tok[:-1])
        stems = [stem] + ([stem[:-1] + DEASPIRATE[stem[-1]]] if stem[-1:] in DEASPIRATE else [])
        for s in stems:
            for v in "αεοι":
                if s + v in idx:
                    return idx[s + v]
    return ()


def analyze(text: str) -> dict:
    toks = tokens(text)
    entries: dict[str, dict] = {}
    unknown: dict[str, int] = {}
    out_tokens = []
    names = matched = dcc = 0
    for tok in toks:
        ids = _lookup(tok)
        if not ids:
            if tok[:1].isupper():
                names += 1
                out_tokens.append({"text": tok, "ids": [], "name": True})
                continue
            unknown[tok] = unknown.get(tok, 0) + 1
            out_tokens.append({"text": tok, "ids": []})
            continue
        matched += 1
        primary = data.entry_by_id(ids[0])
        if primary.get("source", "dcc") != "course":
            dcc += 1
        rec = entries.get(primary["id"])
        if rec is None:
            rec = entries[primary["id"]] = {
                "id": primary["id"],
                "lemma": primary["lemma"],
                "short": primary["short"],
                "rank": primary["rank"],
                "source": primary.get("source", "dcc"),
                "count": 0,
            }
        rec["count"] += 1
        out_tokens.append({"text": tok, "ids": list(ids)})
    words = len(toks) - names
    return {
        "words": words,
        "names": names,
        "matched": matched,
        "coverage": round(matched / words, 3) if words else 0.0,
        "dcc_coverage": round(dcc / words, 3) if words else 0.0,
        "entries": list(entries.values()),
        "unknown": [{"text": t, "count": n} for t, n in unknown.items()],
        "tokens": out_tokens,
    }


@lru_cache(maxsize=1)
def library_coverage() -> dict[str, dict]:
    """Coverage of every reading-library passage (for 'suggested first books')."""
    from ..library import get_item, load_manifest

    out = {}
    for item in load_manifest():
        a = analyze(get_item(item["id"])["text"])
        out[item["id"]] = {"coverage": a["coverage"], "dcc_coverage": a["dcc_coverage"], "words": a["words"], "unknown": len(a["unknown"])}
    return out
