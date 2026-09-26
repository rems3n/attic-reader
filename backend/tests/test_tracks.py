"""Stage 3 tracks (scope, index, API) and Stage 4 guided reading (analyze)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.course import data
from app.course.analyze import analyze, library_coverage
from app.main import app

client = TestClient(app)


def test_tracks_are_listed_with_seven_lessons_and_a_gate():
    main = data.main_lesson_ids()
    tracks = data.tracks()
    assert {t["id"] for t in tracks} == {"mythology", "philosophy", "history", "politics"}
    for t in tracks:
        assert len(t["lessons"]) == 7
        assert t["gate"].startswith("gate-")
        assert t["side_after"] in main and t["full_after"] in main
        assert not set(t["lessons"]) & set(main)


def test_track_lessons_build_on_the_main_course_not_on_other_tracks():
    myth = data.track_by_id("mythology")["lessons"]
    phil = data.track_by_id("philosophy")["lessons"]
    assert data.track_requires(myth[0]) == "9.4"
    assert data.track_requires(myth[3]) == "12.4"
    assert data.is_side_reading(myth[2]) and not data.is_side_reading(myth[3])
    # lesson 1's scope before it is exactly the main course through 9.4
    assert data.vocab_scope(myth[0], inclusive=False) == data.vocab_scope("9.4")
    # lesson 4 builds on everything through 12.4 plus the track's own lessons 1–3
    scope4 = data.vocab_scope(myth[3], inclusive=False)
    assert set(data.vocab_scope("12.4")) <= set(scope4)
    own = {v["id"] for lid in myth[:3] if data.lesson_available(lid) for v in data.load_lesson(lid)["vocab"]}
    assert own <= set(scope4)
    # no other track's words leak in (unless the main course also teaches them)
    other = {v["id"] for lid in phil if data.lesson_available(lid) for v in data.load_lesson(lid)["vocab"]}
    assert not (other - set(data.vocab_scope("12.4")) - own) & set(scope4)


def test_course_index_keeps_tracks_out_of_the_main_order():
    idx = client.get("/api/course").json()
    assert not any("." in lid and not lid.split(".")[0].isdigit() for lid in idx["lesson_order"])
    t = idx["tracks"][0]
    assert len(t["lessons"]) == 7 and "gate_available" in t
    assert all(lesson["requires"] in ("9.4", "12.4") for lesson in t["lessons"])


def test_track_route():
    r = client.get("/api/course/track/history")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "history" and len(body["lessons"]) == 7 and isinstance(body["words"], list)
    assert client.get("/api/course/track/nope").status_code == 404


def test_track_lessons_resolve_with_their_track():
    for t in data.tracks():
        for lid in t["lessons"]:
            if data.lesson_available(lid):
                lesson = data.resolve_lesson(lid)
                assert lesson["track"]["id"] == t["id"]
                assert lesson["stage"]["id"] == "3"
                assert lesson["unit"]["test"] == t["gate"]


# ---------------------------------------------------------- guided reading

def test_analyze_maps_forms_elisions_and_names():
    a = analyze("ἐν δὲ τῷ πολέμῳ ὁ Κῦρος ἐβούλετο τοὺς Ἕλληνας ἀγαγεῖν, ἀλλ’ ἐφ’ ἑαυτοῦ ἔμενε.")
    lemmas = {e["lemma"] for e in a["entries"]}
    assert {"πόλεμος", "βούλομαι", "ἄγω", "ἀλλά", "ἐπί", "μένω"} <= lemmas
    assert a["names"] >= 1 and a["unknown"] == []
    assert a["coverage"] == 1.0


def test_analyze_reports_unknown_words():
    a = analyze("ὁ ἄνθρωπος ζυγομαχεῖ.")
    assert [u["text"] for u in a["unknown"]] == ["ζυγομαχεῖ"]
    assert 0 < a["coverage"] < 1


def test_analyze_route_and_library_coverage():
    r = client.post("/api/analyze", json={"text": "ὁ λόγος ἀγαθός ἐστιν."})
    assert r.status_code == 200 and r.json()["coverage"] == 1.0
    assert client.post("/api/analyze", json={"text": "α" * 20001}).status_code == 422
    cov = library_coverage()
    assert cov and all(0.5 < v["coverage"] <= 1 for v in cov.values())
