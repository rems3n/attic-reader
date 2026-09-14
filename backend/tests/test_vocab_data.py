"""The DCC core vocabulary lexicon shipped in app/vocab_data/core.json."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.greek import attic_ipa
from app.main import app
from app.tts.kokoro import prepare_kokoro_phonemes, unknown_kokoro_symbols
from app.vocab import TOPICS, facets, get_entry, load_entries, summary, VocabError

DATA = Path(__file__).resolve().parents[1] / "app" / "vocab_data"
KINDS = {"noun", "verb", "adjective", "pronoun", "numeral", "article", "preposition", "adverb", "conjunction", "interjection"}


def test_lexicon_shape():
    entries = load_entries()
    assert len(entries) == 524
    assert len({e["id"] for e in entries}) == 524
    # The DCC export has two words at rank 384 (θνῄσκω, λύω) and no 385.
    assert [e["rank"] for e in entries] == sorted(e["rank"] for e in entries)
    assert {e["rank"] for e in entries} >= set(range(1, 384))
    for e in entries:
        assert e["kind"] in KINDS, e
        assert e["definition"] and e["short"], e
        assert e["group"] and e["pos"], e
        assert 1 <= e["tier"] <= 4 and e["level"], e
        assert e["topics"] and set(e["topics"]) <= {t for t, _ in TOPICS}, e
        assert e["lemma"] and " " not in e["lemma"], e


def test_every_verb_has_parsed_principal_parts():
    for e in load_entries():
        if e["kind"] != "verb":
            continue
        parts = e["morph"]["parts"]
        assert e["lemma"] in parts.get("present", []) + parts.get("aorist", []), e["headword"]
        for slot, forms in parts.items():
            assert forms and all(f for f in forms), (e["headword"], slot)


def test_nouns_have_genitive_and_gender():
    for e in load_entries():
        if e["kind"] != "noun":
            continue
        assert e["morph"].get("genitive"), e["headword"]
        assert e["morph"].get("gender") in {"m", "f", "n", "m/f"}, e["headword"]


def test_attic_spelling_applied():
    by_rank = {e["rank"]: e for e in load_entries()}
    assert by_rank[214]["lemma"] == "θάλαττα" and by_rank[214]["dcc_headword"].startswith("θάλασσα")
    assert by_rank[134]["lemma"] == "πράττω"
    assert by_rank[305]["lemma"] == "τέτταρες"


def test_abbreviated_endings_expanded_with_accent():
    by_rank = {e["rank"]: e for e in load_entries()}
    assert by_rank[65]["morph"]["genitive"] == "ἀνθρώπου"
    assert by_rank[226]["morph"]["genitive"] == "ποταμοῦ"
    assert by_rank[218]["morph"]["genitive"] == "κεφαλῆς"
    assert by_rank[186]["morph"]["feminine"] == "δευτέρα"
    assert by_rank[73]["morph"]["forms"] == ["κακός", "κακή", "κακόν"]
    assert by_rank[325]["morph"]["terminations"] == 2


def test_lemmas_are_pronounceable_by_kokoro():
    for e in load_entries():
        ipa = attic_ipa(e["lemma"])
        assert ipa.strip(), e["lemma"]
        assert unknown_kokoro_symbols(prepare_kokoro_phonemes(ipa)) == [], (e["lemma"], ipa)


def test_facets_cover_all_topics():
    f = facets()
    assert [t["id"] for t in f["topics"]] == [t for t, _ in TOPICS]
    assert all(t["count"] > 0 for t in f["topics"])
    assert sum(t["count"] for t in f["tiers"]) == 524
    assert any(g["id"] == "Religion" for g in f["groups"])


def test_cognates_tag():
    entries = load_entries()
    tagged = [e for e in entries if "cognates" in e["tags"]]
    assert len(tagged) >= 250
    for e in entries:
        c = e["cognates"]
        assert (c is not None) == ("cognates" in e["tags"]), e["lemma"]
        if c:
            assert all(v for v in c.values()), e["lemma"]
    by = {e["lemma"]: e for e in entries}
    assert "logic" in by["λόγος"]["cognates"]["derivatives"]
    assert "father" in by["πατήρ"]["cognates"]["cognates"]
    f = facets()
    assert f["tags"][0] == {"id": "cognates", "label": "English cognates", "count": len(tagged)}
    client = TestClient(app)
    index = client.get("/api/vocab").json()
    assert index["facets"]["tags"][0]["count"] == len(tagged)
    assert index["items"][44]["cognates"]["derivatives"][0] == "logic"


def test_get_entry_and_summary():
    logos = get_entry("λογος")
    assert logos["rank"] == 45 and logos["kind"] == "noun"
    s = summary(logos)
    assert set(s) >= {"id", "lemma", "short", "topics", "tier"}
    with pytest.raises(VocabError):
        get_entry("nope")


def test_vocab_api():
    client = TestClient(app)
    index = client.get("/api/vocab").json()
    assert len(index["items"]) == 524
    assert "DCC" in index["attribution"]
    assert index["facets"]["topics"][0]["id"] == "mythology"
    entry = client.get("/api/vocab/λογος").json()
    assert entry["definition"].startswith("word")
    assert entry["ipa"]
    assert client.get("/api/vocab/missing").status_code == 404


def test_core_json_is_up_to_date_with_builder():
    """core.json must be regenerated (python scripts/build_vocab.py) after edits."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_vocab", DATA.parents[1] / "scripts" / "build_vocab.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    fresh = module.build(check=True)
    committed = json.loads((DATA / "core.json").read_text("utf-8"))
    assert fresh == committed


def test_forms_on_word_page_and_grammar_api():
    from app.greek.morph import decline_entry

    client = TestClient(app)
    logos = client.get("/api/vocab/λογος").json()
    assert logos["forms"]["kind"] == "noun"
    assert logos["forms"]["cells"][1]["forms"] == ["λόγου"]
    # every declinable entry produces a table without raising
    for e in load_entries():
        if e["kind"] == "verb":
            continue
        decline_entry(e)
    index = client.get("/api/grammar").json()
    assert [s["id"] for s in index["sections"]][:2] == ["article", "nouns-1"]
    item = client.get("/api/grammar/polis").json()
    assert item["table"]["cells"][1]["forms"] == ["πόλεως"]
    assert item["examples"][0]["greek"]
    assert client.get("/api/grammar/nope").status_code == 404
    from app.greek.morph import paradigms as pm
    for p in pm.PARADIGMS:
        if p["kind"] != "verb":
            assert pm.table_for(p) is not None, p["id"]
