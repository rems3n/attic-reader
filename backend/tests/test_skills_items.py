"""Skill detail (/course/skills) and error-item rebuilding (mistakes deck)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.course import data
from app.course.drill import supported
from app.main import app

client = TestClient(app)


def test_skill_detail_lists_teaching_lessons_paradigm_and_drillability():
    r = client.get("/api/course/skill/noun.decl2.dat.sg")
    assert r.status_code == 200
    body = r.json()
    assert body["skill"]["id"] == "noun.decl2.dat.sg" and body["skill"]["family"] == "noun"
    assert body["paradigm"] == body["skill"]["paradigm"] and body["paradigm"]
    assert body["drillable"] is True
    ids = [l["id"] for l in body["lessons"]]
    assert "1.2" in ids
    for lesson in body["lessons"]:
        assert "noun.decl2.dat.sg" in data.load_lesson(lesson["id"])["skills"]
        assert lesson["title_grc"] and lesson["title_en"]
    # the paradigm link resolves on the grammar route
    assert client.get(f"/api/grammar/{body['paradigm']}").status_code == 200


def test_skill_detail_includes_track_lessons_and_non_drillable_skills():
    track_lessons = [lid for t in data.tracks() for lid in t["lessons"] if data.lesson_available(lid)]
    skill = next(s for lid in track_lessons for s in data.load_lesson(lid)["skills"])
    body = client.get(f"/api/course/skill/{skill}").json()
    assert any(l["track"] for l in body["lessons"])
    reading = client.get("/api/course/skill/read.comprehension").json()
    assert reading["drillable"] is False and reading["paradigm"] is None and reading["lessons"]


def test_unknown_skill_is_404():
    assert client.get("/api/course/skill/nope.nothing").status_code == 404


def test_authored_lesson_and_test_items_come_back_by_id():
    lesson = data.load_lesson("1.1")
    test = data.load_test("unit-1")
    forms = next(s for s in test["sections"] if s["id"] == "forms")
    reading = next(s for s in test["sections"] if s["id"] == "reading")
    ids = [lesson["exercises"][0]["id"], forms["items"][0]["id"], reading["items"][0]["id"]]
    r = client.post("/api/course/items", json={"ids": ids})
    assert r.status_code == 200
    body = r.json()
    assert body["missing"] == []
    got = {i["source"]: i for i in body["items"]}
    assert set(got) == set(ids)
    ex = got[ids[0]]
    assert ex["type"] == lesson["exercises"][0]["type"] and ex["origin"] == {"kind": "lesson", "id": "1.1", "block": "exercises", "scope": "1.1", "generated": False}
    assert got[ids[1]]["origin"]["kind"] == "test" and got[ids[1]]["origin"]["scope"] == test["scope"]
    # a reading-section item carries its passage
    assert got[ids[2]]["context"]["kind"] == "passage" and got[ids[2]]["context"]["text"] == reading["passage"]


def test_ambiguous_question_and_quiz_ids_return_both_candidates():
    lesson = data.load_lesson("1.1")
    assert lesson["questions"][0]["id"] == lesson["quiz"][0]["id"]  # both "1.1:q1"
    body = client.post("/api/course/items", json={"ids": ["1.1:q1"]}).json()
    blocks = sorted(i["origin"]["block"] for i in body["items"])
    assert blocks == ["questions", "quiz"]
    question = next(i for i in body["items"] if i["origin"]["block"] == "questions")
    assert question["context"]["kind"] == "story" and question["context"]["text"]


def test_generated_items_are_replaced_by_fresh_drill_items_on_the_same_skills():
    test = data.load_test("unit-1")
    forms = next(s for s in test["sections"] if s["id"] == "forms")
    refs = [
        {"id": "unit-1:formsg3", "key": "1.4|unit-1:formsg3", "lesson": "1.4"},
        {"id": "drill2", "key": "3.2|drill2", "lesson": "3.2"},
        {"id": "review-7:g1", "key": "k", "lesson": "2.1", "skills": ["noun.decl1.gen.sg"]},
    ]
    body = client.post("/api/course/items", json={"refs": refs, "seed": 3}).json()
    assert body["missing"] == []
    by = {i["source"]: i for i in body["items"]}
    gen = by["1.4|unit-1:formsg3"]
    assert gen["generated"] and gen["origin"]["generated"] and gen["origin"]["scope"] == test["scope"]
    assert set(gen["skills"]) <= set(forms["generate"]["skills"])
    lesson_skills = {s for lid in data.lessons_before("3.2") for s in data.load_lesson(lid)["skills"] if supported(s)}
    assert set(by["3.2|drill2"]["skills"]) <= lesson_skills
    assert by["k"]["skills"] == ["noun.decl1.gen.sg"] and by["k"]["origin"]["scope"] == "2.1"
    # every fresh item has its own id
    assert len({i["id"] for i in body["items"]}) == len(body["items"])


def test_unrebuildable_refs_are_missing():
    refs = [
        {"id": "1.1:e999", "key": "gone"},           # authored lesson id that no longer exists
        {"id": "unit-1:forms99", "key": "gone-test"},  # authored test id that no longer exists
        {"id": "drill1", "key": "old-review", "lesson": "review"},  # no scope, no skills
    ]
    body = client.post("/api/course/items", json={"refs": refs}).json()
    assert body["items"] == []
    assert body["missing"] == ["gone", "gone-test", "old-review"]
    # a fallback scope lets the old review drill be replaced
    body = client.post("/api/course/items", json={"refs": refs[2:], "scope": "2.1"}).json()
    assert body["missing"] == [] and body["items"][0]["origin"]["scope"] == "2.1"


def test_items_request_is_capped():
    assert client.post("/api/course/items", json={"ids": [f"1.1:e{n}" for n in range(61)]}).status_code == 422
