"""Gold tests for the dual (Smyth §§ 195, 214, 230, 250 ff., 305, 325, 332,
383, 462) and for the verbal adjectives in -τός / -τέος (Smyth §§ 471–473).

The dual lives in a separate ``dual`` block of each table, so nothing that
reads ``cells`` changes; the course sees it as ``nom.du`` / ``gen.du.m`` /
``present.active.indicative.2du`` cells after all singular and plural cells.
"""

from __future__ import annotations

import pytest

from app.course import data
from app.course.drill import generate
from app.course.forms import all_cells, cell_forms, describe_cell, entry_forms
from app.course.grade import feedback_for_typed
from app.course.normalize import normalize_answer
from app.greek.morph import decline
from app.greek.morph.participle import decline_participle
from app.greek.morph.verb import conjugate_entry


@pytest.fixture(scope="module")
def lex():
    out: dict[str, dict] = {}
    for e in data.all_entries():
        out.setdefault(e["lemma"], e)
    return out


def noun_dual(lemma, genitive, gender, subclass):
    t = decline(lemma, "noun", subclass, {"genitive": genitive, "gender": gender})
    return " ".join("/".join(c["forms"]) for c in t["dual"])


# --------------------------------------------------------------------------- nouns

@pytest.mark.parametrize("spec,expected", [
    (("λόγος", "λόγου", "m", "noun-2"), "λόγω λόγοιν λόγοιν λόγω λόγω"),
    (("ὁδός", "ὁδοῦ", "f", "noun-2"), "ὁδώ ὁδοῖν ὁδοῖν ὁδώ ὁδώ"),
    (("ἄνθρωπος", "ἀνθρώπου", "m/f", "noun-2"), "ἀνθρώπω ἀνθρώποιν ἀνθρώποιν ἀνθρώπω ἀνθρώπω"),
    (("δῶρον", "δώρου", "n", "noun-2"), "δώρω δώροιν δώροιν δώρω δώρω"),
    (("χώρα", "χώρας", "f", "noun-1"), "χώρα χώραιν χώραιν χώρα χώρα"),
    (("τιμή", "τιμῆς", "f", "noun-1"), "τιμά τιμαῖν τιμαῖν τιμά τιμά"),
    (("θάλαττα", "θαλάττης", "f", "noun-1"), "θαλάττα θαλάτταιν θαλάτταιν θαλάττα θαλάττα"),
    (("νίκη", "νίκης", "f", "noun-1"), "νίκα νίκαιν νίκαιν νίκα νίκα"),
    (("πολίτης", "πολίτου", "m", "noun-1"), "πολίτα πολίταιν πολίταιν πολίτα πολίτα"),
    (("νεανίας", "νεανίου", "m", "noun-1"), "νεανία νεανίαιν νεανίαιν νεανία νεανία"),
    (("πρᾶγμα", "πράγματος", "n", "noun-3-cons"), "πράγματε πραγμάτοιν πραγμάτοιν πράγματε πράγματε"),
    (("φύλαξ", "φύλακος", "m", "noun-3-cons"), "φύλακε φυλάκοιν φυλάκοιν φύλακε φύλακε"),
    (("ἀγών", "ἀγῶνος", "m", "noun-3-cons"), "ἀγῶνε ἀγώνοιν ἀγώνοιν ἀγῶνε ἀγῶνε"),
    (("δαίμων", "δαίμονος", "m/f", "noun-3-cons"), "δαίμονε δαιμόνοιν δαιμόνοιν δαίμονε δαίμονε"),
    (("νύξ", "νυκτός", "f", "noun-3-cons"), "νύκτε νυκτοῖν νυκτοῖν νύκτε νύκτε"),
    (("γένος", "γένους", "n", "noun-3-sigma"), "γένει γενοῖν γενοῖν γένει γένει"),
    (("πόλις", "πόλεως", "f", "noun-3-iota"), "πόλει πολέοιν πολέοιν πόλει πόλει"),
    (("βασιλεύς", "βασιλέως", "m", "noun-3-eus"), "βασιλῆ βασιλέοιν βασιλέοιν βασιλῆ βασιλῆ"),
    (("πούς", "ποδός", "m", "noun-3-cons"), "πόδε ποδοῖν ποδοῖν πόδε πόδε"),
    (("ἀνήρ", "ἀνδρός", "m", "noun-3-irregular"), "ἄνδρε ἀνδροῖν ἀνδροῖν ἄνδρε ἄνδρε"),
    (("γυνή", "γυναικός", "f", "noun-3-irregular"), "γυναῖκε γυναικοῖν γυναικοῖν γυναῖκε γυναῖκε"),
    (("πλοῦς", "πλοῦ", "m", "noun-2"), "πλώ πλοῖν πλοῖν πλώ πλώ"),
])
def test_noun_dual(spec, expected):
    assert noun_dual(*spec) == expected


def test_dual_is_kept_out_of_the_regular_cells():
    t = decline("λόγος", "noun", "noun-2", {"genitive": "λόγου", "gender": "m"})
    assert {c["number"] for c in t["cells"]} == {"sg", "pl"}
    assert {c["number"] for c in t["dual"]} == {"du"}


# --------------------------------------------------------------------------- article, pronouns, adjectives

def adj_dual(t, gender):
    return " ".join("/".join(c["forms"][gender]) for c in t["dual"])


def test_article_dual():
    t = decline("ὁ", "article", "article", {})
    assert adj_dual(t, "m") == "τώ τοῖν τοῖν τώ"
    assert adj_dual(t, "n") == "τώ τοῖν τοῖν τώ"
    assert adj_dual(t, "f") == "τώ/τά τοῖν/ταῖν τοῖν/ταῖν τώ/τά"


@pytest.mark.parametrize("lemma,person,expected", [
    ("ἐγώ", "1st person", "νώ νῷν νῷν νώ"),
    ("σύ", "2nd person", "σφώ σφῷν σφῷν σφώ"),
])
def test_personal_pronoun_dual(lemma, person, expected):
    assert adj_dual(decline(lemma, "pronoun", "pronoun", {}), person) == expected


@pytest.mark.parametrize("lemma,sub,morph,gender,expected", [
    ("ἀγαθός", "adj-1-2", {"terminations": 3, "feminine": "ἀγαθή"}, "m", "ἀγαθώ ἀγαθοῖν ἀγαθοῖν ἀγαθώ ἀγαθώ"),
    ("ἀγαθός", "adj-1-2", {"terminations": 3, "feminine": "ἀγαθή"}, "f", "ἀγαθά ἀγαθαῖν ἀγαθαῖν ἀγαθά ἀγαθά"),
    ("δίκαιος", "adj-1-2", {"terminations": 3, "feminine": "δικαία"}, "f", "δικαία δικαίαιν δικαίαιν δικαία δικαία"),
    ("ἀδύνατος", "adj-1-2", {"terminations": 2}, "mf", "ἀδυνάτω ἀδυνάτοιν ἀδυνάτοιν ἀδυνάτω ἀδυνάτω"),
    ("ἀληθής", "adj-3-es", {"terminations": 2}, "mf", "ἀληθεῖ ἀληθοῖν ἀληθοῖν ἀληθεῖ ἀληθεῖ"),
    ("πλήρης", "adj-3-es", {"terminations": 2}, "n", "πλήρει πλήροιν πλήροιν πλήρει πλήρει"),
    ("βελτίων", "adj-3-on", {"terminations": 2}, "mf", "βελτίονε βελτιόνοιν βελτιόνοιν βελτίονε βελτίονε"),
    ("ταχύς", "adj-us", {"terminations": 3}, "m", "ταχέε ταχέοιν ταχέοιν ταχέε ταχέε"),
    ("ταχύς", "adj-us", {"terminations": 3}, "f", "ταχεία ταχείαιν ταχείαιν ταχεία ταχεία"),
])
def test_adjective_dual(lemma, sub, morph, gender, expected):
    assert adj_dual(decline(lemma, "adjective", sub, morph), gender) == expected


# --------------------------------------------------------------------------- verbs

def dual_of(t, tense, voice, mood):
    for system in t["systems"]:
        for tb in system["tables"]:
            if (tb["tense"], tb["voice"], tb["mood"]) == (tense, voice, mood):
                return " ".join("/".join(c["forms"]) for c in tb.get("dual", []))
    raise AssertionError(f"no table {tense} {voice} {mood}")


VERB_DUAL = [
    ("λύω", "present", "active", "indicative", "λύετον λύετον"),
    ("λύω", "present", "active", "subjunctive", "λύητον λύητον"),
    ("λύω", "present", "active", "optative", "λύοιτον λυοίτην"),
    ("λύω", "present", "active", "imperative", "λύετον λυέτων"),
    ("λύω", "imperfect", "active", "indicative", "ἐλύετον ἐλυέτην"),
    ("λύω", "future", "active", "indicative", "λύσετον λύσετον"),
    ("λύω", "aorist", "active", "indicative", "ἐλύσατον ἐλυσάτην"),
    ("λύω", "aorist", "active", "subjunctive", "λύσητον λύσητον"),
    ("λύω", "aorist", "active", "optative", "λύσαιτον λυσαίτην"),
    ("λύω", "aorist", "active", "imperative", "λύσατον λυσάτων"),
    ("λύω", "aorist", "passive", "indicative", "ἐλύθητον ἐλυθήτην"),
    ("λύω", "aorist", "passive", "optative", "λυθεῖτον/λυθείητον λυθείτην/λυθειήτην"),
    ("λύω", "perfect", "active", "indicative", "λελύκατον λελύκατον"),
    ("λύω", "pluperfect", "active", "indicative", "ἐλελύκετον ἐλελυκέτην"),
    # middle/passive (λύομαι)
    ("λύω", "present", "middle/passive", "indicative", "λύεσθον λύεσθον"),
    ("λύω", "present", "middle/passive", "optative", "λύοισθον λυοίσθην"),
    ("λύω", "present", "middle/passive", "imperative", "λύεσθον λυέσθων"),
    ("λύω", "imperfect", "middle/passive", "indicative", "ἐλύεσθον ἐλυέσθην"),
    ("λύω", "aorist", "middle", "indicative", "ἐλύσασθον ἐλυσάσθην"),
    ("λύω", "aorist", "middle", "imperative", "λύσασθον λυσάσθων"),
    ("λύω", "perfect", "middle/passive", "indicative", "λέλυσθον λέλυσθον"),
    ("λύω", "pluperfect", "middle/passive", "indicative", "ἐλέλυσθον ἐλελύσθην"),
    # contract and consonant stems keep the accent of the 2nd plural where they can
    ("τιμάω", "present", "active", "indicative", "τιμᾶτον τιμᾶτον"),
    ("τιμάω", "imperfect", "active", "indicative", "ἐτιμᾶτον ἐτιμάτην"),
    ("ποιέω", "imperfect", "active", "indicative", "ἐποιεῖτον ἐποιείτην"),
    ("γράφω", "perfect", "middle/passive", "indicative", "γέγραφθον γέγραφθον"),
    ("βαίνω", "aorist", "active", "indicative", "ἔβητον ἐβήτην"),
    ("δίδωμι", "present", "active", "indicative", "δίδοτον δίδοτον"),
    ("δίδωμι", "imperfect", "active", "indicative", "ἐδίδοτον ἐδιδότην"),
    # hand tables too
    ("εἰμί", "present", "active", "indicative", "ἐστόν ἐστόν"),
    ("εἰμί", "present", "active", "imperative", "ἔστον ἔστων"),
    ("οἶδα", "perfect", "active", "indicative", "ἴστον ἴστον"),
]


@pytest.mark.parametrize("lemma,tense,voice,mood,expected", VERB_DUAL, ids=[f"{g[0]}-{g[1]}-{g[2]}-{g[3]}" for g in VERB_DUAL])
def test_verb_dual(lex, lemma, tense, voice, mood, expected):
    assert dual_of(conjugate_entry(lex[lemma]), tense, voice, mood) == expected


def test_deponent_middle_dual(lex):
    t = conjugate_entry(lex["βούλομαι"])
    assert dual_of(t, "present", "middle", "indicative") == "βούλεσθον βούλεσθον"
    assert dual_of(t, "imperfect", "middle", "indicative") == "ἐβούλεσθον ἐβουλέσθην"


def test_hand_tables_are_not_mutated(lex):
    from app.greek.morph import verb_tables as T

    conjugate_entry(lex["εἰμί"])
    assert all("dual" not in tb for tb in T.IRREGULAR["εἰμί"]["tables"])


@pytest.mark.parametrize("principal,rows", [
    (("λύων", "λύουσα", "λῦον", "λύοντος"), {"m": "λύοντε λυόντοιν", "f": "λυούσα λυούσαιν", "n": "λύοντε λυόντοιν"}),
    (("λύσας", "λύσασα", "λῦσαν", "λύσαντος"), {"m": "λύσαντε λυσάντοιν", "f": "λυσάσα λυσάσαιν"}),
    (("λυθείς", "λυθεῖσα", "λυθέν", "λυθέντος"), {"m": "λυθέντε λυθέντοιν", "f": "λυθείσα λυθείσαιν"}),
    (("λελυκώς", "λελυκυῖα", "λελυκός", "λελυκότος"), {"m": "λελυκότε λελυκότοιν", "f": "λελυκυία λελυκυίαιν"}),
    (("στάς", "στᾶσα", "στάν", "στάντος"), {"m": "στάντε στάντοιν", "f": "στάσα στάσαιν"}),
    (("λυόμενος", "λυομένη", "λυόμενον", "λυομένου"), {"m": "λυομένω λυομένοιν", "f": "λυομένα λυομέναιν"}),
])
def test_participle_dual(principal, rows):
    got = decline_participle(*principal)
    for g, expected in rows.items():
        nav, gd = expected.split()
        assert got[(g, "du")] == [nav, gd, gd, nav, nav]


# --------------------------------------------------------------------------- course cells

@pytest.mark.parametrize("lemma,cell,form", [
    ("λόγος", "nom.du", "λόγω"),
    ("λόγος", "gen.du", "λόγοιν"),
    ("χώρα", "gen.du", "χώραιν"),
    ("πρᾶγμα", "nom.du", "πράγματε"),
    ("πούς", "gen.du", "ποδοῖν"),
    ("ὁ", "gen.du.f", "τοῖν"),
    ("ἀγαθός", "nom.du.m", "ἀγαθώ"),
    ("λύω", "present.active.indicative.2du", "λύετον"),
    ("λύω", "imperfect.active.indicative.3du", "ἐλυέτην"),
    ("λύω", "aorist.active.participle.gen.du.m", "λυσάντοιν"),
])
def test_course_dual_cells(lex, lemma, cell, form):
    e = lex[lemma]
    assert form in cell_forms(e, cell), cell_forms(e, cell)
    assert normalize_answer(form) in entry_forms(e)
    assert describe_cell(e, cell)


def test_dual_cells_come_last(lex):
    keys = [k for k, _ in all_cells(lex["λόγος"])]
    first_dual = min(i for i, k in enumerate(keys) if ".du" in k)
    assert all(".du" not in k for k in keys[:first_dual]) and all(".du" in k for k in keys[first_dual:])
    # λόγω (dual) and λόγῳ (dative) look alike without accents: feedback names the dative
    found = feedback_for_typed({}, "λογω", [lex["λόγος"]["id"]])
    assert found[0]["cell"] == "dat.sg"


def test_drills_leave_the_dual_out(lex):
    scope = [lex[w]["id"] for w in ("λόγος", "ἄνθρωπος", "λύω", "ἀγαθός", "χώρα")]
    items = generate(["noun.decl2.gen.sg", "verb.pres.act.ind.2pl", "adj.agree", "noun.decl1.nom.pl"], 24, scope, seed=3)
    for item in items:
        assert ".du" not in item["cell"] and not item["cell"].endswith("du")
        for option in item.get("options", []):
            assert option["text"] not in {"λόγω", "λόγοιν", "λύετον", "ἀγαθώ", "χώραιν"}


# --------------------------------------------------------------------------- verbal adjectives

VADJ = [
    ("λύω", "λυτός", "λυτέος"),
    ("ποιέω", "ποιητός", "ποιητέος"),
    ("πράττω", "πρακτός", "πρακτέος"),
    ("γράφω", "γραπτός", "γραπτέος"),
    ("λαμβάνω", "ληπτός", "ληπτέος"),
    ("ἀκούω", "ἀκουστός", "ἀκουστέος"),
    ("πείθω", "πειστός", "πειστέος"),
    ("τίθημι", "θετός", "θετέος"),
    ("δίδωμι", "δοτός", "δοτέος"),
    ("φέρω", "οἰστός", "οἰστέος"),
    ("σκοπέω", "σκεπτός", "σκεπτέος"),
    ("τρέπω", "τρεπτός", "τρεπτέος"),
]


@pytest.mark.parametrize("lemma,tos,teos", VADJ, ids=[v[0] for v in VADJ])
def test_verbal_adjectives(lex, lemma, tos, teos):
    e = lex[lemma]
    assert cell_forms(e, "vadj.tos") == [tos]
    assert cell_forms(e, "vadj.teos") == [teos]
    t = conjugate_entry(e)
    vt = [tb for s in t["systems"] if s["id"] == "verbal" for tb in s["tables"]]
    assert vt and vt[0]["cells"][0]["forms"][0] == tos and vt[0]["cells"][1]["forms"][0] == teos


@pytest.mark.parametrize("cell,form", [
    ("vadj.teos.nom.sg.n", "πρακτέον"),
    ("vadj.teos.nom.sg.f", "πρακτέα"),
    ("vadj.teos.gen.sg.f", "πρακτέας"),
    ("vadj.teos.gen.pl.m", "πρακτέων"),
    ("vadj.teos.nom.pl.n", "πρακτέα"),
    ("vadj.tos.gen.sg.f", "πρακτῆς"),
    ("vadj.tos.dat.pl.m", "πρακτοῖς"),
])
def test_verbal_adjectives_decline(lex, cell, form):
    e = lex["πράττω"]
    assert form in cell_forms(e, cell), cell_forms(e, cell)
    assert "verbal adjective" in describe_cell(e, cell)


def test_no_verbal_adjective_without_a_stem(lex):
    assert cell_forms(lex["δύναμαι"], "vadj.tos") == []
    assert cell_forms(lex["εἰμί"], "vadj.teos") == []
