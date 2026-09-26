"""Deterministic grading of a learner's response to an exercise item.

The frontend grades locally with the same rules (lib/course.ts); this module
is the reference implementation used by the tests and by POST
/api/course/check, which adds morphology-aware feedback for typed forms.
"""

from __future__ import annotations

from .normalize import answers_match, normalize_answer, tokens

CHOICE_TYPES = {"pick-picture", "listen-pick", "cloze-choice", "true-false-grc", "bank-cloze", "label"}
TYPED_TYPES = {"cloze-type", "produce-form", "transform", "compose-grc", "dictation", "endings-cloze", "answer-grc"}
SELF_TYPES = {"translate-en", "describe-picture", "retell", "read-aloud", "continue-story"}
ALL_TYPES = CHOICE_TYPES | TYPED_TYPES | SELF_TYPES | {"parse", "locate", "reorder", "match", "word-family"}


def grade(item: dict, response: object, accents: bool = False) -> dict:
    """→ {"correct": bool, "detail": ...}. `response` shape by type:
    choice → option id; typed → list[str] (one per gap) or str; parse →
    {group: option}; locate → list[int]; reorder → list[str] (tokens in
    order); match → {left: right}; self-graded → bool (learner's own mark)."""
    t = item["type"]
    if t in CHOICE_TYPES or (t == "answer-grc" and item.get("options")):
        return {"correct": response == item["answer"]}
    if t in TYPED_TYPES:
        given = [response] if isinstance(response, str) else list(response or [])
        gaps = item.get("gaps") or [{"answers": item.get("answers", [])}]
        strict = item.get("strict_accents", accents)
        results = [answers_match(given[i] if i < len(given) else "", gap["answers"], strict) for i, gap in enumerate(gaps)]
        return {"correct": all(results), "gaps": results}
    if t == "parse":
        answer = item["answer"]
        given = response if isinstance(response, dict) else {}
        results = {g: given.get(g) == v for g, v in answer.items()}
        return {"correct": all(results.values()), "groups": results}
    if t == "locate":
        want = set(item["answer"])
        got = set(int(i) for i in (response or []))
        return {"correct": want == got, "missing": sorted(want - got), "extra": sorted(got - want)}
    if t == "reorder":
        given = " ".join(response or []) if isinstance(response, list) else str(response or "")
        return {"correct": answers_match(given, item["answers"], accents)}
    if t in {"match", "word-family"}:
        pairs = {p["left"]: p["right"] for p in item["pairs"]}
        given = response if isinstance(response, dict) else {}
        results = {k: given.get(k) == v for k, v in pairs.items()}
        return {"correct": all(results.values()), "pairs": results}
    if t in SELF_TYPES:
        return {"correct": bool(response), "self": True}
    raise ValueError(f"unknown exercise type {t!r}")


def feedback_for_typed(item: dict, response: list[str] | str, scope_ids: list[str], accents: bool = False) -> list[dict]:
    """Name the form the learner actually typed, when it is some form of a
    word in scope ('you gave the genitive singular')."""
    from .data import entry_by_id
    from .forms import all_cells, describe_cell

    given = [response] if isinstance(response, str) else list(response or [])
    out: list[dict] = []
    for text in given:
        key = normalize_answer(text, accents)
        found = None
        for entry_id in scope_ids:
            entry = entry_by_id(entry_id)
            for cell, forms in all_cells(entry):
                if any(normalize_answer(f.replace("(ν)", "ν"), accents) == key or normalize_answer(f.replace("(ν)", ""), accents) == key for f in forms):
                    found = {"lemma": entry["lemma"], "cell": cell, "label": describe_cell(entry, cell)}
                    break
            if found:
                break
        out.append(found or {})
    return out


def sentence_tokens(text: str) -> list[str]:
    return tokens(text)
