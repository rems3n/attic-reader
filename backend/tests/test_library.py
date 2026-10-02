import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.greek import attic_ipa, segment_sentences
from app.library import CATEGORIES, DATA_DIR, LEVELS, load_manifest
from app.main import app
from app.tts.kokoro import prepare_kokoro_phonemes, unknown_kokoro_symbols

client = TestClient(app)


def test_manifest_lists_unique_attributed_passages():
    items = load_manifest()
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)) >= 300
    categories = {c for c, _ in CATEGORIES}
    for item in items:
        assert item["category"] in categories
        assert item["level"] in LEVELS
        assert item["dialect"] in {"attic", "ionic", "koine"}
        assert item["source"]["license"] == "CC BY-SA 4.0"
        assert item["source"]["urn"].startswith("urn:cts:greekLit:")
        assert item["title"] and item["blurb"] and item["author"] and item["work"]
    assert all(any(i["category"] == c for i in items) for c, _ in CATEGORIES)


def test_every_passage_segments_into_a_learnable_number_of_sentences():
    for item in load_manifest():
        n = len(segment_sentences(item["text"]))
        assert 1 <= n <= 100, f"{item['id']}: {n} sentences"
        assert item["sentence_count"] == n
        assert item["estimated_seconds"] > 10


def test_every_passage_is_representable_by_the_voice():
    for item in load_manifest():
        for sentence in item["sentences"]:
            unknown = unknown_kokoro_symbols(prepare_kokoro_phonemes(attic_ipa(sentence)))
            assert unknown == [], f"{item['id']}: {unknown} in {sentence[:40]}"


def test_passage_files_match_sources_spec():
    sources = json.loads((DATA_DIR / "sources.json").read_text("utf-8"))
    spec_ids = [p["id"] for p in sources["passages"]]
    assert spec_ids == [i["id"] for i in load_manifest()]
    assert all((DATA_DIR / f"{i}.json").exists() for i in spec_ids)


def test_library_index_and_item_endpoints():
    body = client.get("/api/library").json()
    assert [c["id"] for c in body["categories"]] == [c for c, _ in CATEGORIES]
    assert len(body["items"]) == len(load_manifest())
    first = body["items"][0]
    assert "text" not in first
    assert set(first) >= {"id", "title", "author", "work", "ref", "level", "blurb", "sentence_count", "estimated_seconds", "ready_speeds", "source"}
    item = client.get(f"/api/library/{first['id']}").json()
    assert item["text"].startswith("Δαρείου")
    assert len(item["sentences"]) == item["sentence_count"]
    assert client.get("/api/library/nope").status_code == 404


def test_tei_ref_resolver_on_inline_fragment(tmp_path):
    import sys
    import xml.etree.ElementTree as ET

    sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
    from build_library import element_text, resolve_ref

    xml = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>
      <div type="edition" n="urn:x">
        <div type="textpart" subtype="book" n="1">
          <div type="textpart" subtype="chapter" n="1">
            <div type="textpart" subtype="section" n="2"><p>ἀρχὴ<note>editorial</note> τοῦ
              λόγου.</p></div>
          </div>
        </div>
        <div type="textpart" subtype="section" n="43">
          <sp><speaker>Σωκράτης</speaker><p>τί λέγεις;</p></sp><sp><speaker>Κρίτων</speaker><p>οὐδέν.</p></sp>
        </div>
      </div></body></text></TEI>"""
    root = ET.fromstring(xml)
    assert element_text(resolve_ref(root, "1.1.2")) == "ἀρχὴ τοῦ λόγου."
    assert element_text(resolve_ref(root, "43")) == "Σωκράτης: τί λέγεις;\nΚρίτων: οὐδέν."


def test_expanded_sequences_keep_sources_and_do_not_prerender():
    from collections import defaultdict
    groups = defaultdict(list)
    for item in load_manifest():
        if not item.get('sequence'):
            continue
        assert item['prerender'] is False
        assert 'reading_url' in item['source']
        assert '/master/' not in item['source']['url']
        groups[(item['author'], item['work'])].append(item['sequence'])
    assert len(groups) == 26
    assert all(sorted(v) == list(range(1, len(v)+1)) for v in groups.values())


def test_editorial_marks_remain_in_text_but_are_supported_for_audio():
    assert prepare_kokoro_phonemes('[a] † >') == '(a)'
    assert any('[' in i['text'] for i in load_manifest())
