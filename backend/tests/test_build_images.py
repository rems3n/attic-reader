"""The image pass itself needs network access; these cover its offline parts:
licence acceptance, crop parsing, the source list against the manifests, and
the crop/pad/WebP processing on a synthetic picture."""

import importlib.util
import io
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_images.py"
spec = importlib.util.spec_from_file_location("build_images", SCRIPT)
bi = importlib.util.module_from_spec(spec)
sys.modules["build_images"] = bi
spec.loader.exec_module(bi)  # type: ignore[union-attr]


@pytest.mark.parametrize("text", ["CC0", "CC0 1.0", "Public domain", "CC BY 4.0", "CC BY-SA 3.0", "cc-by-sa-4.0", "Creative Commons Attribution-ShareAlike 4.0", "PD-old-100"])
def test_license_accepted(text):
    assert bi.license_ok(text)


@pytest.mark.parametrize("text", [None, "", "CC BY-NC 4.0", "CC BY-NC-SA 4.0", "CC BY-ND 4.0", "All rights reserved", "unknown", "Fair use"])
def test_license_refused(text):
    assert not bi.license_ok(text)


def test_parse_crop():
    assert bi.parse_crop("") is None
    assert bi.parse_crop(None) is None
    assert bi.parse_crop("0.1,0.2,0.5,0.5") == (0.1, 0.2, 0.5, 0.5)
    assert bi.parse_crop("0.8,0.8,0.5,0.5") == (0.8, 0.8, pytest.approx(0.2), pytest.approx(0.2))
    with pytest.raises(ValueError):
        bi.parse_crop("0.1,0.2")
    with pytest.raises(ValueError):
        bi.parse_crop("1.5,0,0.2,0.2")


def test_sources_match_manifests():
    rows = bi.read_sources()
    records = bi.manifest_records()
    assert rows, "sources.csv is empty"
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate ids in sources.csv"
    for row in rows:
        assert row["id"] in records, f"{row['id']} is in sources.csv but in no manifest"
        assert row["source"] in set(bi.VERIFIERS) | {"manual"}, row
        assert row["ref"], row["id"]
        if row["ref"].startswith("search:"):
            assert row["source"] in bi.SEARCHERS, f"{row['id']}: {row['source']} has no search"
        if row["source"] == "manual":
            assert bi.license_ok(row["license"]) and row["credit"], f"{row['id']}: manual rows need licence + credit"
        bi.parse_crop(row.get("crop"))
        assert (row.get("aspect") or "3:2") in bi.WIDTHS
    # every non-diagram placeholder for Stage 0 / Unit 1 has a row (diagrams are our own SVGs)
    base = bi.load_json(bi.DATA / "manifest.json", {"images": []})["images"]
    for img in base:
        if img.get("kind") != "diagram" and img.get("license") == "placeholder":
            assert img["id"] in set(ids), f"no source row for {img['id']}"


def test_process_image_pads_and_fits():
    from PIL import Image

    src = Image.new("RGB", (1200, 500), (200, 40, 40))
    buf = io.BytesIO()
    src.save(buf, "PNG")
    out = bi.process_image(buf.getvalue(), None, "3:2")
    assert len(out) <= bi.MAX_BYTES
    im = Image.open(io.BytesIO(out))
    assert im.size == bi.WIDTHS["3:2"]
    # cream field at the corners, picture in the middle
    corner = im.getpixel((3, 3))
    assert all(abs(c - t) < 12 for c, t in zip(corner, bi.CREAM))
    mid = im.getpixel((450, 300))
    assert mid[0] > 150 and mid[1] < 90

    square = bi.process_image(buf.getvalue(), (0.25, 0.0, 0.5, 1.0), "1:1")
    assert Image.open(io.BytesIO(square)).size == bi.WIDTHS["1:1"]


def test_relaxed_queries_drop_words_from_the_end():
    assert bi.relaxed_queries("red-figure kylix symposium youth") == ["red-figure kylix symposium youth", "red-figure kylix symposium", "red-figure kylix"]
    assert bi.relaxed_queries("kylix") == ["kylix"]


def test_find_hit_relaxes_then_falls_back(monkeypatch):
    calls = []

    def met_search(q):
        calls.append(("met", q))
        return ["1"] if q == "terracotta lekythos" else []

    def commons_search(q):
        calls.append(("commons", q))
        return ["File:Owl.jpg"]

    verifiers = {
        "met": lambda ref: {"ok": True, "license": "CC0", "title": "Terracotta lekythos (oil flask)", "match_text": "Vase"},
        "commons": lambda ref: {"ok": True, "license": "CC BY-SA 4.0", "title": ref, "match_text": "Athenian tetradrachm owl"},
    }
    monkeypatch.setattr(bi, "SEARCHERS", {"met": met_search, "commons": commons_search})
    monkeypatch.setattr(bi, "VERIFIERS", verifiers)
    # a shorter query finds it at the row's own source
    assert bi.find_hit("met", "terracotta lekythos white ground", "lekythos") == ("met", "1", "Terracotta lekythos (oil flask)")
    # nothing at the Met: the fallback source, matched on its description text
    assert bi.find_hit("met", "silver tetradrachm", "tetradrachm") == ("commons", "File:Owl.jpg", "File:Owl.jpg")
    assert bi.find_hit("met", "silver tetradrachm", "tetradrachm", fallback=False) is None
    # licence still checked on fallback hits
    verifiers["commons"] = lambda ref: {"ok": True, "license": "CC BY-NC 4.0", "title": ref, "match_text": "tetradrachm"}
    assert bi.find_hit("met", "silver tetradrachm", "tetradrachm") is None


def test_resolved_hit_keeps_its_source():
    row = {"id": "x", "source": "met", "ref": "search:owl|owl"}
    resolved = {"x": {"ref": "search:owl|owl", "source": "commons", "object": "File:Owl.jpg"}}
    assert bi.concrete_source_ref(row, resolved) == ("commons", "File:Owl.jpg")
    assert bi.concrete_source_ref(row, {}) == ("met", None)
    assert bi.concrete_source_ref({"id": "y", "source": "met", "ref": "123"}, {}) == ("met", "123")


def test_failures_file_keeps_only_what_still_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(bi, "FAILURES", tmp_path / "failures.json")
    monkeypatch.setattr(bi, "ROOT", tmp_path / "backend")
    monkeypatch.setattr(bi, "_failed", {})
    bi.save_json(bi.FAILURES, {"old-fixed": {"step": "resolve", "reason": "x"}, "not-in-run": {"step": "fetch", "reason": "y"}})
    rows = [{"id": "old-fixed", "source": "met", "ref": "1"}, {"id": "bad", "source": "commons", "ref": "search:q|p"}]
    bi.fail("bad", "resolve", "no hit")
    bi.fail("bad", "verify", "later step")  # the first failing step wins
    bi.write_failures(rows)
    out = bi.load_json(bi.FAILURES, {})
    assert set(out) == {"bad", "not-in-run"}
    assert out["bad"] == {"step": "resolve", "reason": "no hit", "source": "commons", "ref": "search:q|p"}


def test_unreachable_host_is_skipped_after_repeated_failures(monkeypatch):
    calls = []

    def boom(req, timeout):
        calls.append(req.full_url)
        raise OSError("tunnel refused")

    monkeypatch.setattr(bi.urllib.request, "urlopen", boom)
    monkeypatch.setattr(bi.time, "sleep", lambda s: None)
    monkeypatch.setattr(bi, "_host_errors", {})
    for _ in range(bi.HOST_DOWN_AFTER):
        with pytest.raises(OSError):
            bi.http_json("https://example.org/api")
    n = len(calls)
    with pytest.raises(RuntimeError, match="unreachable"):
        bi.http_json("https://example.org/api")
    assert len(calls) == n  # no further network calls


def test_commons_verify_handles_numeric_metadata(monkeypatch):
    page = {"imageinfo": [{"url": "https://upload.wikimedia.org/a.jpg", "thumburl": "https://upload.wikimedia.org/t.jpg", "descriptionurl": "https://commons.wikimedia.org/wiki/File:A.jpg",
                           "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}, "Artist": {"value": "<a href='x'>Someone</a>"}, "DateTime": {"value": 2019.5}, "Assessments": {"value": ""}, "Odd": 3}}]}
    monkeypatch.setattr(bi, "http_json", lambda url, retries=4: {"query": {"pages": {"1": page}}})
    info = bi.commons_verify("File:A.jpg")
    assert info["ok"] and info["license"] == "CC BY-SA 4.0" and "Someone" in info["credit"]
