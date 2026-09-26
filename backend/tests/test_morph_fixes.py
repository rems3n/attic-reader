"""Gold tests for engine bugs reported by the course authors (2026-09-26).

Forms checked against Smyth (§§ 235, 292–293, 409, 417, 426, 431, 489,
529) and LSJ. Words that are not (yet) lexicon entries are conjugated or
declined from a synthetic morph dict, the way a course author would enter them.
"""

from __future__ import annotations

import pytest

from app.course import data
from app.course.forms import all_cells, cell_forms, entry_forms
from app.course.normalize import normalize_answer
from app.greek.morph import decline
from app.greek.morph.verb import conjugate, conjugate_entry


@pytest.fixture(scope="module")
def lex():
    out: dict[str, dict] = {}
    for e in data.all_entries():  # DCC core list + course words
        out.setdefault(e["lemma"], e)
    return out


def table(t: dict, tense: str, voice: str, mood: str) -> str:
    for system in t["systems"]:
        for tb in system["tables"]:
            if (tb["tense"], tb["voice"], tb["mood"]) == (tense, voice, mood):
                return " ".join("/".join(c["forms"]) for c in tb["cells"])
    raise AssertionError(f"{t['lemma']}: no table {tense} {voice} {mood}")


# --------------------------------------------------------------------------- verbs in the lexicon

LEXICON_GOLD = [
    # 1a: the 2nd singular aorist imperative in -σον is recessive
    ("ποιέω", "aorist", "active", "imperative", "ποίησον ποιησάτω ποιήσατε ποιησάντων"),
    ("ἀγνοέω", "aorist", "active", "imperative", "ἀγνόησον ἀγνοησάτω ἀγνοήσατε ἀγνοησάντων"),
    ("ἐλέγχω", "aorist", "active", "imperative", "ἔλεγξον ἐλεγξάτω ἐλέγξατε ἐλεγξάντων"),
    ("κερδαίνω", "aorist", "active", "imperative", "κέρδανον κερδανάτω κερδάνατε κερδανάντων"),
    ("λύω", "aorist", "active", "imperative", "λῦσον λυσάτω λύσατε λυσάντων"),
    ("παύω", "aorist", "active", "imperative", "παῦσον παυσάτω παύσατε παυσάντων"),
    ("λύω", "aorist", "middle", "imperative", "λῦσαι λυσάσθω λύσασθε λυσάσθων"),
    ("λύω", "aorist", "active", "infinitive", "λῦσαι"),
    ("ποιέω", "aorist", "active", "infinitive", "ποιῆσαι"),
    ("κατηγορέω", "aorist", "active", "imperative", "κατηγόρησον κατηγορησάτω κατηγορήσατε κατηγορησάντων"),
    # compound imperatives recede, but not past the last syllable of the prefix (Smyth § 426)
    ("ἀποδίδωμι", "aorist", "active", "imperative", "ἀπόδος ἀποδότω ἀποδότε ἀποδόντων"),
    ("παραδίδωμι", "aorist", "active", "imperative", "παράδος παραδότω παραδότε παραδόντων"),
    ("προστίθημι", "aorist", "active", "imperative", "πρόσθες προσθέτω προσθέτε προσθέντων"),
    ("ἀποδίδωμι", "aorist", "middle", "imperative", "ἀποδοῦ ἀποδόσθω ἀποδόσθε ἀποδόσθων"),
    ("καθίστημι", "root aorist", "active", "imperative", "κατάστηθι καταστήτω καταστῆτε καταστάντων"),
    ("ἀναβαίνω", "aorist", "active", "imperative", "ἀνάβηθι ἀναβήτω ἀναβῆτε ἀναβάντων"),
    ("ἀπόλλυμι", "aorist", "active", "imperative", "ἀπόλεσον ἀπολεσάτω ἀπολέσατε ἀπολεσάντων"),
    ("ἀποκτείνω", "aorist", "active", "imperative", "ἀπόκτεινον ἀποκτεινάτω ἀποκτείνατε ἀποκτεινάντων"),
    # 1e: σκοπέω takes its other tenses from σκεπ-
    ("σκοπέω", "future", "middle", "indicative", "σκέψομαι σκέψῃ/σκέψει σκέψεται σκεψόμεθα σκέψεσθε σκέψονται"),
    ("σκοπέω", "aorist", "middle", "indicative", "ἐσκεψάμην ἐσκέψω ἐσκέψατο ἐσκεψάμεθα ἐσκέψασθε ἐσκέψαντο"),
    ("σκοπέω", "aorist", "middle", "infinitive", "σκέψασθαι"),
    ("σκοπέω", "aorist", "middle", "imperative", "σκέψαι σκεψάσθω σκέψασθε σκεψάσθων"),
    ("σκοπέω", "perfect", "middle/passive", "indicative", "ἔσκεμμαι ἔσκεψαι ἔσκεπται ἐσκέμμεθα ἔσκεφθε ἐσκεμμένοι_εἰσί(ν)"),
    ("σκοπέω", "present", "active", "indicative", "σκοπῶ σκοπεῖς σκοπεῖ σκοποῦμεν σκοπεῖτε σκοποῦσι(ν)"),
    # 1f: a perfect given only as an extra part is conjugated
    ("μαίνομαι", "perfect", "active", "indicative", "μέμηνα μέμηνας μέμηνε(ν) μεμήναμεν μεμήνατε μεμήνασι(ν)"),
    ("μαίνομαι", "perfect", "active", "participle", "μεμηνώς μεμηνυῖα μεμηνός μεμηνότος"),
    # 1d: the short perfect of ἵστημι
    ("ἵστημι", "perfect", "active", "participle", "ἑστηκώς/ἑστώς ἑστηκυῖα/ἑστῶσα ἑστηκός/ἑστός ἑστηκότος/ἑστῶτος"),
    ("ἵστημι", "perfect", "active", "subjunctive", "ἑστῶ ἑστῇς ἑστῇ ἑστῶμεν ἑστῆτε ἑστῶσι(ν)"),
    # politics track 1: compounds of ἔχω augment to -ειχ- like the simplex
    ("προσέχω", "imperfect", "active", "indicative", "προσεῖχον προσεῖχες προσεῖχε(ν) προσείχομεν προσείχετε προσεῖχον"),
    # politics track 2: προσ + σχ- keeps one σ
    ("προσέχω", "aorist", "active", "infinitive", "προσχεῖν"),
    ("προσέχω", "aorist", "active", "participle", "προσχών προσχοῦσα προσχόν προσχόντος"),
    ("προσέχω", "aorist", "active", "subjunctive", "πρόσχω πρόσχῃς πρόσχῃ πρόσχωμεν πρόσχητε πρόσχωσι(ν)"),
    ("προσέχω", "aorist", "active", "imperative", "πρόσχες προσχέτω πρόσχετε προσχόντων"),
    ("μετέχω", "aorist", "active", "imperative", "μετάσχες μετασχέτω μετάσχετε μετασχόντων"),
    # politics track 6: οἶμαι / ᾤμην beside οἴομαι / ᾠόμην
    ("οἴομαι", "present", "middle", "indicative", "οἴομαι/οἶμαι οἴῃ/οἴει οἴεται οἰόμεθα οἴεσθε οἴονται"),
    ("οἴομαι", "imperfect", "middle", "indicative", "ᾠόμην/ᾤμην ᾤου ᾤετο ᾠόμεθα ᾤεσθε ᾤοντο"),
    # history track 9: ἀναγιγνώσκω has its root aorist and perfect
    ("ἀναγιγνώσκω", "aorist", "active", "indicative", "ἀνέγνων ἀνέγνως ἀνέγνω ἀνέγνωμεν ἀνέγνωτε ἀνέγνωσαν"),
    ("ἀναγιγνώσκω", "aorist", "active", "infinitive", "ἀναγνῶναι"),
    ("ἀναγιγνώσκω", "aorist", "active", "participle", "ἀναγνούς ἀναγνοῦσα ἀναγνόν ἀναγνόντος"),
    ("ἀναγιγνώσκω", "aorist", "active", "imperative", "ἀνάγνωθι ἀναγνώτω ἀναγνῶτε ἀναγνόντων"),
    ("ἀναγιγνώσκω", "perfect", "active", "indicative", "ἀνέγνωκα ἀνέγνωκας ἀνέγνωκε(ν) ἀνεγνώκαμεν ἀνεγνώκατε ἀνεγνώκασι(ν)"),
    # unchanged: a labial-stem perfect whose present has a nasal infix
    ("λαμβάνω", "perfect", "middle/passive", "indicative", "εἴλημμαι εἴληψαι εἴληπται εἰλήμμεθα εἴληφθε εἰλημμένοι_εἰσί(ν)"),
]


@pytest.mark.parametrize("lemma,tense,voice,mood,expected", LEXICON_GOLD, ids=[f"{g[0]}-{g[1]}-{g[2]}-{g[3]}" for g in LEXICON_GOLD])
def test_lexicon_verbs(lex, lemma, tense, voice, mood, expected):
    assert table(conjugate_entry(lex[lemma]), tense, voice, mood) == expected.replace("_", " ")


# --------------------------------------------------------------------------- verbs from a morph dict

ELENCHO = {"parts": {"present": ["ἐλέγχω"], "future": ["ἐλέγξω"], "aorist": ["ἤλεγξα"], "perfect-mp": ["ἐλήλεγμαι"], "aorist-passive": ["ἠλέγχθην"]}}
AISCHYNO = {"parts": {"present": ["αἰσχύνω"], "future": ["αἰσχυνῶ"], "aorist": ["ᾔσχυνα"], "perfect-mp": ["ᾔσχυμμαι"], "aorist-passive": ["ᾐσχύνθην"]}}
METECHO = {"parts": {"present": ["μετέχω"], "future": ["μεθέξω"], "aorist": ["μετέσχον"]}}
EXELAUNO = {"parts": {"present": ["ἐξελαύνω"], "future": ["ἐξελῶ"], "aorist": ["ἐξήλασα"], "aorist-passive": ["ἐξηλάθην"]}}
ELAUNO = {"parts": {"present": ["ἐλαύνω"], "future": ["ἐλῶ"], "aorist": ["ἤλασα"]}}
SYLLAMBANO = {"parts": {"present": ["συλλαμβάνω"], "future": ["συλλήψομαι"], "aorist": ["συνέλαβον"]}, "verb": {"aorist_stem": "συλλαβ"}}
EMBALLO = {"parts": {"present": ["ἐμβάλλω"], "aorist": ["ἐνέβαλον"]}, "verb": {"aorist_stem": "ἐμβαλ"}}
EKBALLO = {"parts": {"present": ["ἐκβάλλω"], "aorist": ["ἐξέβαλον"]}, "verb": {"aorist_stem": "ἐκβαλ"}}
EPIKEIMAI = {"parts": {"present": ["ἐπίκειμαι"]}}

SYNTHETIC_GOLD = [
    # 1c: perfect middle/passive of γχ- and ν-stems
    ("ἐλέγχω", "verb-omega", ELENCHO, "perfect", "middle/passive", "indicative", "ἐλήλεγμαι ἐλήλεγξαι ἐλήλεγκται ἐληλέγμεθα ἐλήλεγχθε ἐληλεγμένοι_εἰσί(ν)"),
    ("ἐλέγχω", "verb-omega", ELENCHO, "perfect", "middle/passive", "infinitive", "ἐληλέγχθαι"),
    ("ἐλέγχω", "verb-omega", ELENCHO, "perfect", "middle/passive", "participle", "ἐληλεγμένος ἐληλεγμένη ἐληλεγμένον ἐληλεγμένου"),
    ("αἰσχύνω", "verb-omega", AISCHYNO, "perfect", "middle/passive", "indicative", "ᾔσχυμμαι ᾐσχυμμένος_εἶ ᾔσχυνται ᾐσχύμμεθα ᾔσχυνθε ᾐσχυμμένοι_εἰσί(ν)"),
    ("αἰσχύνω", "verb-omega", AISCHYNO, "pluperfect", "middle/passive", "indicative", "ᾐσχύμμην ᾐσχυμμένος_ἦσθα ᾔσχυντο ᾐσχύμμεθα ᾔσχυνθε ᾐσχυμμένοι_ἦσαν"),
    ("αἰσχύνω", "verb-omega", AISCHYNO, "perfect", "middle/passive", "infinitive", "ᾐσχύνθαι"),
    # politics track 1: no DCC imperfect needed for εἶχον in compounds
    ("μετέχω", "verb-omega", METECHO, "imperfect", "active", "indicative", "μετεῖχον μετεῖχες μετεῖχε(ν) μετείχομεν μετείχετε μετεῖχον"),
    # politics track 3: the Attic future of ἐλαύνω contracts like τιμάω
    ("ἐξελαύνω", "verb-omega", EXELAUNO, "future", "active", "indicative", "ἐξελῶ ἐξελᾷς ἐξελᾷ ἐξελῶμεν ἐξελᾶτε ἐξελῶσι(ν)"),
    ("ἐξελαύνω", "verb-omega", EXELAUNO, "future", "active", "infinitive", "ἐξελᾶν"),
    ("ἐλαύνω", "verb-omega", ELAUNO, "future", "active", "indicative", "ἐλῶ ἐλᾷς ἐλᾷ ἐλῶμεν ἐλᾶτε ἐλῶσι(ν)"),
    # politics track 5: compound -σον imperatives
    ("ἐξελαύνω", "verb-omega", EXELAUNO, "aorist", "active", "imperative", "ἐξέλασον ἐξελασάτω ἐξελάσατε ἐξελασάντων"),
    # politics track 4: an override stem written with an assimilated prefix
    ("συλλαμβάνω", "verb-omega", SYLLAMBANO, "aorist", "active", "infinitive", "συλλαβεῖν"),
    ("συλλαμβάνω", "verb-omega", SYLLAMBANO, "aorist", "active", "participle", "συλλαβών συλλαβοῦσα συλλαβόν συλλαβόντος"),
    ("ἐμβάλλω", "verb-omega", EMBALLO, "aorist", "active", "infinitive", "ἐμβαλεῖν"),
    ("ἐκβάλλω", "verb-omega", EKBALLO, "aorist", "active", "infinitive", "ἐκβαλεῖν"),
    # history track 9: compounds of κεῖμαι
    ("ἐπίκειμαι", "verb-deponent", EPIKEIMAI, "present", "middle", "indicative", "ἐπίκειμαι ἐπίκεισαι ἐπίκειται ἐπικείμεθα ἐπίκεισθε ἐπίκεινται"),
    ("ἐπίκειμαι", "verb-deponent", EPIKEIMAI, "imperfect", "middle", "indicative", "ἐπεκείμην ἐπέκεισο ἐπέκειτο ἐπεκείμεθα ἐπέκεισθε ἐπέκειντο"),
    ("ἐπίκειμαι", "verb-deponent", EPIKEIMAI, "present", "middle", "infinitive", "ἐπικεῖσθαι"),
    ("ἐπίκειμαι", "verb-deponent", EPIKEIMAI, "present", "middle", "participle", "ἐπικείμενος ἐπικειμένη ἐπικείμενον ἐπικειμένου"),
    ("ἐπίκειμαι", "verb-deponent", EPIKEIMAI, "future", "middle", "indicative", "ἐπικείσομαι ἐπικείσῃ ἐπικείσεται ἐπικεισόμεθα ἐπικείσεσθε ἐπικείσονται"),
    ("σύγκειμαι", "verb-deponent", {"parts": {"present": ["σύγκειμαι"]}}, "imperfect", "middle", "indicative", "συνεκείμην συνέκεισο συνέκειτο συνεκείμεθα συνέκεισθε συνέκειντο"),
]


@pytest.mark.parametrize("lemma,sub,morph,tense,voice,mood,expected", SYNTHETIC_GOLD,
                         ids=[f"{g[0]}-{g[3]}-{g[4]}-{g[5]}" for g in SYNTHETIC_GOLD])
def test_synthetic_verbs(lemma, sub, morph, tense, voice, mood, expected):
    assert table(conjugate(lemma, sub, morph), tense, voice, mood) == expected.replace("_", " ")


# --------------------------------------------------------------------------- nominals

def forms(lemma, kind, subclass, morph, gender=None):
    t = decline(lemma, kind, subclass, morph)
    return " ".join("/".join(c["forms"][gender] if gender else c["forms"]) for c in t["cells"]), t


@pytest.mark.parametrize("lemma,gender,expected", [
    # 1b: only comparatives have the contracted -ω / -ους forms
    ("ἐπιστήμων", "mf", "ἐπιστήμων ἐπιστήμονος ἐπιστήμονι ἐπιστήμονα ἐπίστημον ἐπιστήμονες ἐπιστημόνων ἐπιστήμοσι(ν) ἐπιστήμονας ἐπιστήμονες"),
    ("ἐπιστήμων", "n", "ἐπίστημον ἐπιστήμονος ἐπιστήμονι ἐπίστημον ἐπίστημον ἐπιστήμονα ἐπιστημόνων ἐπιστήμοσι(ν) ἐπιστήμονα ἐπιστήμονα"),
    ("σώφρων", "mf", "σώφρων σώφρονος σώφρονι σώφρονα σῶφρον σώφρονες σωφρόνων σώφροσι(ν) σώφρονας σώφρονες"),
    ("μείζων", "mf", "μείζων μείζονος μείζονι μείζονα/μείζω μεῖζον μείζονες/μείζους μειζόνων μείζοσι(ν) μείζονας/μείζους μείζονες/μείζους"),
    ("κακίων", "n", "κάκιον κακίονος κακίονι κάκιον κάκιον κακίονα/κακίω κακιόνων κακίοσι(ν) κακίονα/κακίω κακίονα/κακίω"),
])
def test_adjectives_in_on(lemma, gender, expected):
    neuter = {"ἐπιστήμων": "ἐπίστημον", "σώφρων": "σῶφρον", "μείζων": "μεῖζον", "κακίων": "κάκιον"}[lemma]
    got, t = forms(lemma, "adjective", "adj-3-on", {"terminations": 2, "neuter": neuter}, gender)
    assert got == expected


def test_non_comparative_on_adjective_compares_and_has_an_adverb():
    _, t = forms("σώφρων", "adjective", "adj-3-on", {"terminations": 2, "neuter": "σῶφρον"}, "mf")
    assert t["comparison"]["comparative"] == ["σωφρονέστερος"] and t["comparison"]["superlative"] == ["σωφρονέστατος"]
    assert t["adverb"] == ["σωφρόνως"]
    assert "Comparative" not in t["note"]


@pytest.mark.parametrize("gender,expected", [
    # history track 7: barytone σ-stem adjectives keep the accent on the stem
    ("mf", "πλήρης πλήρους πλήρει πλήρη πλῆρες πλήρεις πλήρων πλήρεσι(ν) πλήρεις πλήρεις"),
    ("n", "πλῆρες πλήρους πλήρει πλῆρες πλῆρες πλήρη πλήρων πλήρεσι(ν) πλήρη πλήρη"),
])
def test_barytone_sigma_adjective(gender, expected):
    got, t = forms("πλήρης", "adjective", "adj-3-es", {"terminations": 2, "neuter": "πλῆρες"}, gender)
    assert got == expected
    assert t["adverb"] == ["πλήρως"]
    assert t["comparison"]["comparative"] == ["πληρέστερος"]


@pytest.mark.parametrize("lemma,genitive,gender,expected", [
    # history track 8: contracted second declension from the lemma
    ("πλοῦς", "πλοῦ", "m", "πλοῦς πλοῦ πλῷ πλοῦν πλοῦ πλοῖ πλῶν πλοῖς πλοῦς πλοῖ"),
    ("ῥοῦς", "ῥοῦ", "m", "ῥοῦς ῥοῦ ῥῷ ῥοῦν ῥοῦ ῥοῖ ῥῶν ῥοῖς ῥοῦς ῥοῖ"),
    ("ὀστοῦν", "ὀστοῦ", "n", "ὀστοῦν ὀστοῦ ὀστῷ ὀστοῦν ὀστοῦν ὀστᾶ ὀστῶν ὀστοῖς ὀστᾶ ὀστᾶ"),
    ("περίπλους", "περίπλου", "m", "περίπλους περίπλου περίπλῳ περίπλουν περίπλου περίπλοι περίπλων περίπλοις περίπλους περίπλοι"),
])
def test_contracted_second_declension(lemma, genitive, gender, expected):
    got, t = forms(lemma, "noun", "noun-2", {"genitive": genitive, "gender": gender})
    assert got == expected


def test_contracted_second_declension_matches_the_hand_table_of_nous():
    from app.greek.morph.nominal import decline_noun

    generic = decline_noun("νοῦς", "νοῦ", "m", "noun-2")  # hand table
    got, _ = forms("πλοῦς", "noun", "noun-2", {"genitive": "πλοῦ", "gender": "m"})
    assert [f.replace("πλ", "ν", 1) for f in got.split()] == [c["forms"][0] for c in generic["cells"]]


# --------------------------------------------------------------------------- 1d: missing forms

def _entry(lex, lemma):
    return lex[lemma]


def test_houto_is_a_form_of_houtos(lex):
    assert normalize_answer("οὕτω") in entry_forms(lex["οὕτως"])


def test_ge_compounds_of_ego(lex):
    e = lex["ἐγώ"]
    assert "ἔγωγε" in cell_forms(e, "nom.sg.1st person")
    assert "ἔμοιγε" in cell_forms(e, "dat.sg.1st person")
    assert "ἔμεγε" in cell_forms(e, "acc.sg.1st person")


@pytest.mark.parametrize("cell,form", [
    ("perfect.active.participle.nom.sg.m", "ἑστώς"),
    ("perfect.active.participle.gen.sg.m", "ἑστῶτος"),
    ("perfect.active.participle.dat.pl.m", "ἑστῶσι(ν)"),
    ("perfect.active.participle.nom.sg.f", "ἑστῶσα"),
    ("perfect.active.participle.gen.pl.f", "ἑστωσῶν"),
    ("perfect.active.participle.acc.pl.n", "ἑστῶτα"),
    ("perfect.active.participle.gen.sg.m", "ἑστηκότος"),
    ("perfect.active.indicative.3pl", "ἑστᾶσι(ν)"),
    ("perfect.active.infinitive.inf", "ἑστάναι"),
])
def test_short_perfect_of_histemi(lex, cell, form):
    assert form in cell_forms(lex["ἵστημι"], cell), cell_forms(lex["ἵστημι"], cell)


@pytest.mark.parametrize("lemma,gender,expected", [
    ("ἐμαυτοῦ", "m", "ἐμαυτοῦ ἐμαυτῷ ἐμαυτόν"),
    ("ἐμαυτοῦ", "f", "ἐμαυτῆς ἐμαυτῇ ἐμαυτήν"),
    ("σεαυτοῦ", "m", "σεαυτοῦ/σαυτοῦ σεαυτῷ/σαυτῷ σεαυτόν/σαυτόν"),
    ("ἑαυτοῦ", "f", "ἑαυτῆς/αὑτῆς ἑαυτῇ/αὑτῇ ἑαυτήν/αὑτήν"),
])
def test_reflexive_pronouns(lemma, gender, expected):
    t = decline(lemma, "pronoun", "pronoun", {})
    sg = [c for c in t["cells"] if c["number"] == "sg" and c["forms"][gender]]
    assert " ".join("/".join(c["forms"][gender]) for c in sg) == expected


def test_every_course_and_core_verb_still_conjugates():
    for e in data.all_entries():
        if e["kind"] == "verb":
            t = conjugate_entry(e)
            assert t and t["systems"], e["lemma"]
            for key, fs in all_cells(e):
                assert all(f and "σσχ" not in f and "ἐἐ" not in f for f in fs), (e["lemma"], key, fs)
