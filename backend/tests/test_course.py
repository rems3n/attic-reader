"""The beginner course: content rules, loader, drills, grading, API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.course import data
from app.course.drill import generate, supported
from app.course.grade import grade
from app.course.normalize import answers_match, expand_movable, normalize_answer, tokens
from app.course.validate import validate
from app.main import app

client = TestClient(app)
FIXTURES = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "normalize.fixtures.json"


# ------------------------------------------------------------------ content

def test_content_passes_the_authoring_rules():
    problems = validate()
    assert problems == [], "\n".join(problems)


def test_manifest_and_authored_lessons():
    ids = data.lesson_ids()
    assert ids[:8] == ["0.1", "0.2", "0.3", "0.4", "1.1", "1.2", "1.3", "1.4"]
    for lid in ids[:8]:
        assert data.lesson_available(lid), lid
    index = data.course_index()
    assert [s["id"] for s in index["stages"]] == ["0", "1", "2"]
    unit1 = index["stages"][1]["units"][0]
    assert unit1["test"] == "unit-1" and unit1["test_available"]
    assert all(l["available"] for l in unit1["lessons"])
    assert {t["id"] for t in index["tracks"]} == {"mythology", "philosophy", "history", "politics"}


def test_vocabulary_scope_grows_in_order():
    first = data.vocab_scope("0.4")
    later = data.vocab_scope("1.2")
    assert first and later[: len(first)] == first
    assert "κεραμευς" in data.vocab_scope("1.1") and "κεραμευς" not in data.vocab_scope("0.4")
    before = set(data.vocab_scope("1.2", inclusive=False))
    new = [v["id"] for v in data.load_lesson("1.2")["vocab"] if v["id"] not in before]
    assert 6 <= len(new) <= 12


def test_resolved_lesson_has_everything_the_player_needs():
    lesson = data.resolve_lesson("1.1")
    assert lesson["unit"]["n"] == 1 and lesson["stage"]["id"] == "1"
    assert lesson["position"]["prev"] == "0.4" and lesson["position"]["next"] == "1.2"
    assert lesson["cover_image"]["alt_grc"]
    assert all(v["ipa"] and v["short"] and v["headword"] for v in lesson["vocab"])
    assert any(v["source"] == "course" for v in lesson["vocab"])  # κεραμεύς etc.
    assert lesson["story_text"].startswith("ὁ Ἀρίστων")
    assert lesson["skills"][0]["label"]
    assert all("id" in item for item in lesson["exercises"] + lesson["quiz"] + lesson["questions"])


def test_course_words_decline_and_conjugate():
    from app.course.forms import all_cells, cell_forms

    ker = data.entry_by_id("κεραμευς")
    assert cell_forms(ker, "gen.sg") == ["κεραμέως"]
    assert cell_forms(ker, "acc.sg") == ["κεραμέα"]
    assert cell_forms(data.entry_by_id("κυων"), "dat.pl") == ["κυσί(ν)"]
    assert cell_forms(data.entry_by_id("αγορα"), "dat.sg") == ["ἀγορᾷ"]
    pon = data.entry_by_id("πονεω")
    assert cell_forms(pon, "present.active.indicative.3sg") == ["πονεῖ"]
    assert cell_forms(pon, "present.active.indicative.3pl") == ["πονοῦσι(ν)"]
    assert cell_forms(data.entry_by_id("τρεχω"), "present.active.indicative.3sg") == ["τρέχει"]
    assert len(all_cells(data.entry_by_id("υφαινω"))) > 20
    # ὑφαίνω is not ὑπο + αἵνω: liquid aorist stem ὑφην- outside the indicative
    assert cell_forms(data.entry_by_id("υφαινω"), "aorist.active.infinitive.inf") == ["ὑφῆναι"]
    assert cell_forms(data.entry_by_id("υφαινω"), "aorist.active.subjunctive.1sg") == ["ὑφήνω"]
    # a compound's aorist_stem override written with its prefix is not doubled
    by_lemma = {e["lemma"]: e for e in data.all_entries()}
    for lemma, inf, imp in [("ἐξέρχομαι", "ἐξελθεῖν", "ἔξελθε"), ("εἰσέρχομαι", "εἰσελθεῖν", "εἴσελθε"), ("προσέρχομαι", "προσελθεῖν", "πρόσελθε")]:
        if lemma in by_lemma:
            assert cell_forms(by_lemma[lemma], "aorist.active.infinitive.inf") == [inf], lemma
            assert cell_forms(by_lemma[lemma], "aorist.active.imperative.2sg") == [imp], lemma


# ---------------------------------------------------------------- normalize

# The rough breathing is always kept (ὁ ≠ ὀ); lenient mode drops accents,
# length marks, the iota subscript and the smooth breathing; strict keeps
# accents (grave → acute) and both breathings.
CASES = [
    ("ὁ Ἀρίστων κεραμεύς ἐστιν.", False, "ὁ αριστων κεραμευσ εστιν"),
    ("ὁ Ἀρίστων κεραμεύς ἐστιν.", True, "ὁ ἀρίστων κεραμεύσ ἐστιν"),
    ("καλὸς ἄνθρωπος", True, "καλόσ ἄνθρωποσ"),
    ("  ἡ   ΑΓΟΡΆ ", False, "ἡ αγορα"),
    ("τῷ οἴκῳ", False, "τω οικω"),
    ("τῷ οἴκῳ", True, "τῷ οἴκῳ"),
    ("ὁ vs ὀ", False, "ὁ vs ο"),
    ("ὁ vs ὀ", True, "ὁ vs ὀ"),
    ("ἐστίν", False, "εστιν"),
    ("λῦσαι", True, "λῦσαι"),
    ("ᾱ̓γορᾱ́", False, "αγορα"),
    ("ὁ Λύσις παῖς ἐστιν.", True, "ὁ λύσισ παῖσ ἐστιν"),
    ("ἵππος", False, "ἱπποσ"),
]


def test_normalize_cases():
    for text, accents, want in CASES:
        assert normalize_answer(text, accents) == want, (text, accents)


def test_answers_match_rules():
    assert answers_match("γυνη", ["γυνή"])
    assert not answers_match("γυνη", ["γυνή"], accents=True)
    assert answers_match("ἐστιν", ["ἐστί(ν)"]) and answers_match("ἐστι", ["ἐστί(ν)"])
    assert answers_match("ὁ Λύσις παῖς ἐστιν.", ["ὁ Λύσις παῖς ἐστιν"], accents=True)
    assert not answers_match("ὀ", ["ὁ"])  # the rough breathing always counts
    assert answers_match("ανθρωπος", ["ἄνθρωπος"]) and not answers_match("ανθρωπος", ["ἄνθρωπος"], accents=True)
    assert not answers_match("", ["ὁ"])
    assert tokens("ἡ Χρυσὶς γυνή ἐστιν· ὁ Λύσις.") == ["ἡ", "Χρυσὶς", "γυνή", "ἐστιν", "ὁ", "Λύσις"]


def test_frontend_fixtures_are_current():
    """frontend/lib/normalize.fixtures.json must match this module; regenerate
    with scripts/export_normalize_fixtures.py when the rules change."""
    fixtures = json.loads(FIXTURES.read_text("utf-8"))
    assert fixtures["normalize"] == [{"text": t, "accents": a, "want": w} for t, a, w in CASES]
    for case in fixtures["match"]:
        assert answers_match(case["given"], case["accepted"], case["accents"]) == case["want"], case


# ------------------------------------------------------------------- grading

def test_grade_every_type():
    assert grade({"type": "cloze-choice", "answer": "b"}, "b")["correct"]
    assert not grade({"type": "true-false-grc", "answer": "false"}, "true")["correct"]
    r = grade({"type": "cloze-type", "gaps": [{"answers": ["γυνή"]}, {"answers": ["ἐστί(ν)"]}]}, ["γυνη", "εστι"])
    assert r["correct"] and r["gaps"] == [True, True]
    assert not grade({"type": "cloze-type", "gaps": [{"answers": ["γυνή"]}], "strict_accents": True}, ["γυνη"])["correct"]
    assert grade({"type": "parse", "answer": {"case": "dat", "number": "sg"}}, {"case": "dat", "number": "sg"})["correct"]
    r = grade({"type": "locate", "answer": [0, 4]}, [4])
    assert not r["correct"] and r["missing"] == [0]
    assert grade({"type": "reorder", "answers": ["ὁ Ἀρίστων κεραμεύς ἐστιν"]}, ["ὁ", "Ἀρίστων", "κεραμεύς", "ἐστιν"])["correct"]
    assert grade({"type": "match", "pairs": [{"left": "ὁ", "right": "κεραμεύς"}, {"left": "ἡ", "right": "γυνή"}]}, {"ὁ": "κεραμεύς", "ἡ": "γυνή"})["correct"]
    assert grade({"type": "translate-en", "model": "x"}, True)["self"]
    with pytest.raises(ValueError):
        grade({"type": "nope"}, None)


def test_authored_items_grade_correct_with_their_own_answers():
    """Every hand-written item must accept its own key (catches typos)."""
    for lid in data.lesson_ids():
        if not data.lesson_available(lid):
            continue
        raw = data.load_lesson(lid)
        for block in ("exercises", "questions", "quiz"):
            for item in raw.get(block, []):
                t = item["type"]
                if t in {"cloze-type", "produce-form", "transform", "compose-grc", "dictation", "endings-cloze"} or (t == "answer-grc" and not item.get("options")):
                    assert item.get("gaps"), (lid, item["id"], "no answers (lemma/cell unresolved?)")
                    key = [expand_movable(g["answers"][0])[0] for g in item["gaps"]]
                    assert grade(item, key, accents=True)["correct"], (lid, item["id"])
                elif t == "reorder":
                    assert grade(item, tokens(item["answers"][0]))["correct"], (lid, item["id"])


# -------------------------------------------------------------------- drills

@pytest.mark.parametrize("skill", ["noun.decl2.dat.sg", "noun.decl1.acc.sg", "noun.decl3.gen.pl", "art.dat.sg", "verb.eimi.pres.ind.3pl", "verb.pres.act.ind.3sg", "verb.pres.act.inf", "adj.agree"])
def test_generated_drills_are_self_consistent(skill):
    scope = data.vocab_scope("1.4")
    assert supported(skill)
    items = generate([skill], 6, scope, seed=1)
    assert items, skill
    for item in items:
        assert item["skills"] == [skill] and item["generated"] and item["explain"]
        if item["type"] == "produce-form":
            assert grade(item, [expand_movable(item["gaps"][0]["answers"][0])[0]], accents=True)["correct"]
        elif item["type"] == "parse":
            assert grade(item, item["answer"])["correct"]
            assert item["form"]
        else:
            assert grade(item, item["answer"])["correct"]
            texts = [o["text"] for o in item["options"]]
            assert len(texts) == len(set(texts)) >= 3


def test_drills_are_deterministic_per_seed():
    scope = data.vocab_scope("1.4")
    a = generate(["noun.decl2.dat.sg", "verb.pres.act.ind.3pl"], 8, scope, seed=7)
    b = generate(["noun.decl2.dat.sg", "verb.pres.act.ind.3pl"], 8, scope, seed=7)
    c = generate(["noun.decl2.dat.sg", "verb.pres.act.ind.3pl"], 8, scope, seed=8)
    assert a == b and a != c
    assert generate(["nope.skill"], 4, scope) == []


# ----------------------------------------------------------------------- API

def test_course_api():
    r = client.get("/api/course")
    assert r.status_code == 200 and r.json()["stages"][1]["units"][0]["lessons"][0]["id"] == "1.1"
    r = client.get("/api/course/lesson/1.1")
    assert r.status_code == 200 and r.json()["title_en"] == "Ariston is a potter"
    assert client.get("/api/course/lesson/9.9").status_code == 404
    r = client.get("/api/course/test/unit-1", params={"seed": 3})
    body = r.json()
    assert r.status_code == 200 and body["item_count"] >= 25 and body["pass_score"] == 0.8
    assert any(i.get("generated") for s in body["sections"] for i in s["items"])
    assert client.get("/api/course/test/unit-9").status_code == 404
    r = client.get("/api/course/drill", params={"skills": "noun.decl2.dat.sg,art.nom.sg", "scope": "1.2", "n": 4})
    assert r.status_code == 200 and len(r.json()["items"]) == 4
    assert client.get("/api/course/drill", params={"skills": "x", "scope": "nope"}).status_code == 404
    assert client.get("/api/course/images").json()["images"]


def test_placement_blocks():
    from app.course.grade import SELF_TYPES, grade

    r = client.get("/api/course/placement", params={"seed": 3})
    body = r.json()
    assert r.status_code == 200 and body["stop_after_misses"] == 3
    blocks = body["blocks"]
    assert blocks and blocks[0]["unit"] == 1 and blocks[0]["test"] == "unit-1"
    assert blocks[0]["lessons"][:2] == ["0.1", "0.2"] and "1.4" in blocks[0]["lessons"]
    for b in blocks:
        assert 1 <= len(b["items"]) <= body["per_unit"]
        for item in b["items"]:
            assert item["type"] not in SELF_TYPES
            assert item.get("gaps") or item.get("answer") is not None or item.get("options") or item.get("pairs") or item.get("tokens") or item.get("cells")
            assert grade(item, None, False)["correct"] is False
    # deterministic per seed
    assert client.get("/api/course/placement", params={"seed": 3}).json() == body
    assert client.get("/api/course/placement", params={"seed": 4}).json() != body


def test_course_check_names_the_form_you_typed():
    item = {"type": "produce-form", "gaps": [{"answers": ["ἀνθρώπῳ"]}]}
    r = client.post("/api/course/check", json={"item": item, "response": ["ἀνθρώπου"], "scope": "1.2"})
    body = r.json()
    assert r.status_code == 200 and not body["correct"]
    assert body["feedback"][0]["cell"] == "gen.sg" and body["feedback"][0]["lemma"] == "ἄνθρωπος"
    r = client.post("/api/course/check", json={"item": item, "response": ["ανθρωπω"]})
    assert r.json()["correct"]


def test_vocab_api_includes_course_words_and_lessons():
    body = client.get("/api/vocab").json()
    items = {i["id"]: i for i in body["items"]}
    assert len(items) >= 524 + 20
    assert items["κεραμευς"]["source"] == "course" and "1.1" in items["κεραμευς"]["lessons"]
    assert "0.4" in items["ανθρωπος"]["lessons"]
    assert any(f["id"] == "1.1" for f in body["facets"]["lessons"])
    entry = client.get("/api/vocab/κεραμευς").json()
    assert entry["forms"]["cells"][1]["forms"] == ["κεραμέως"]


def test_course_prerender_plan(fake_kokoro):
    from app.tts import prerender
    from app.tts.kokoro import KokoroAtticTTS

    jobs = prerender.course_plan(KokoroAtticTTS())
    assert len(jobs) > 200
    speeds = {j[0] for j in jobs}
    assert speeds == {0.75, 0.6}


def test_drill_decl3_subgroups_and_deponent_middle():
    from app.course.drill import generate, supported

    scope = data.vocab_scope("1.4")
    assert supported("noun.decl3.cons.pl") and supported("noun.decl3.cons.gen.sg")
    items = generate(["noun.decl3.cons.gen.sg"], 4, scope, seed=1)
    assert items and all(data.entry_by_id(next(e["id"] for e in data.all_entries() if e["lemma"] == i["lemma"]))["subclass"] == "noun-3-cons" for i in items)
    plural = generate(["noun.decl3.cons.pl"], 6, scope, seed=1)
    assert plural and all(i["cell"].endswith(".pl") for i in plural)
    # middle skills: active verbs' middle/passive when no deponent is in scope …
    mp = generate(["verb.pres.mp.ind.3sg"], 3, scope, seed=1)
    assert mp and all("middle" in i["cell"] for i in mp)
    # … and deponents only once one has been taught
    scope2 = scope + [e["id"] for e in data.all_entries() if e["lemma"] == "βούλομαι"]
    mp2 = generate(["verb.pres.mp.ind.3sg", "verb.pres.mp.inf"], 4, scope2, seed=1)
    assert mp2 and all(i["lemma"] == "βούλομαι" for i in mp2)
