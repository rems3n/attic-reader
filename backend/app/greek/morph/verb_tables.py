"""Hand-written conjugations for the irregular verbs, plus helper constants."""

from __future__ import annotations

PERSONS = ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl")

EIMI_SUBJ = ["ὦ", "ᾖς", "ᾖ", "ὦμεν", "ἦτε", "ὦσι(ν)"]
EIMI_OPT = ["εἴην", "εἴης", "εἴη", "εἶμεν", "εἶτε", "εἶεν"]

# second-aorist imperatives that are oxytone (εἰπέ, ἐλθέ, εὑρέ, ἰδέ, λαβέ)
OXYTONE_IMPERATIVES = {"εἰπ", "ἐλθ", "εὑρ", "ἰδ", "λαβ"}


def _t(tense, voice, mood, forms, note=None):
    tags = PERSONS if mood not in {"infinitive", "participle"} else (("inf",) if mood == "infinitive" else ("m", "f", "n", "mg"))
    cells = []
    for tag, f in zip(tags, forms):
        if f is None:
            continue
        cells.append({"tag": tag, "forms": f.split("/") if isinstance(f, str) else list(f)})
    t = {"tense": tense, "voice": voice, "mood": mood, "cells": cells}
    if note:
        t["note"] = note
    return t


def from_spec(spec: dict) -> dict:
    """Hand table given in overrides.json: {tense, voice, mood, forms: "a b c ..."}."""
    return _t(spec["tense"], spec["voice"], spec["mood"], _s(spec["forms"]), spec.get("note"))


def _s(text: str) -> list:
    return [None if x == "-" else x for x in text.split()]


IRREGULAR: dict[str, dict] = {
    "εἰμί": {
        "note": "‘be’. The present indicative is enclitic except εἶ; ἔστι is accented ἔστι when it means ‘exists/is possible’ or begins a clause.",
        "tables": [
            _t("present", "active", "indicative", _s("εἰμί εἶ ἐστί(ν) ἐσμέν ἐστέ εἰσί(ν)")),
            _t("present", "active", "subjunctive", _s("ὦ ᾖς ᾖ ὦμεν ἦτε ὦσι(ν)")),
            _t("present", "active", "optative", _s("εἴην εἴης εἴη εἶμεν/εἴημεν εἶτε/εἴητε εἶεν/εἴησαν")),
            _t("present", "active", "imperative", _s("- ἴσθι ἔστω - ἔστε ἔστων/ὄντων")),
            _t("present", "active", "infinitive", ["εἶναι"]),
            _t("present", "active", "participle", ["ὤν", "οὖσα", "ὄν", "ὄντος"]),
            _t("imperfect", "active", "indicative", _s("ἦ/ἦν ἦσθα ἦν ἦμεν ἦτε ἦσαν")),
            _t("future", "middle", "indicative", _s("ἔσομαι ἔσῃ/ἔσει ἔσται ἐσόμεθα ἔσεσθε ἔσονται")),
            _t("future", "middle", "optative", _s("ἐσοίμην ἔσοιο ἔσοιτο ἐσοίμεθα ἔσοισθε ἔσοιντο")),
            _t("future", "middle", "infinitive", ["ἔσεσθαι"]),
            _t("future", "middle", "participle", ["ἐσόμενος", "ἐσομένη", "ἐσόμενον", "ἐσομένου"]),
        ],
    },
    "πάρειμι": {
        "note": "παρά + εἰμί, ‘be present’: conjugated like εἰμί with the prefix; the accent moves back onto the prefix where the law of limitation allows (πάρειμι, πάρεστι, παρῆν).",
        "tables": [
            _t("present", "active", "indicative", _s("πάρειμι πάρει πάρεστι(ν) πάρεσμεν πάρεστε πάρεισι(ν)")),
            _t("present", "active", "subjunctive", _s("παρῶ παρῇς παρῇ παρῶμεν παρῆτε παρῶσι(ν)")),
            _t("present", "active", "optative", _s("παρείην παρείης παρείη παρεῖμεν παρεῖτε παρεῖεν")),
            _t("present", "active", "imperative", _s("- πάρισθι παρέστω - πάρεστε παρέστων")),
            _t("present", "active", "infinitive", ["παρεῖναι"]),
            _t("present", "active", "participle", ["παρών", "παροῦσα", "παρόν", "παρόντος"]),
            _t("imperfect", "active", "indicative", _s("παρῆ/παρῆν παρῆσθα παρῆν παρῆμεν παρῆτε παρῆσαν")),
            _t("future", "middle", "indicative", _s("παρέσομαι παρέσῃ παρέσται παρεσόμεθα παρέσεσθε παρέσονται")),
            _t("future", "middle", "infinitive", ["παρέσεσθαι"]),
            _t("future", "middle", "participle", ["παρεσόμενος", "παρεσομένη", "παρεσόμενον", "παρεσομένου"]),
        ],
    },
    "εἶμι": {
        "note": "‘go’. The present indicative has future meaning in Attic (‘I shall go’) and serves as the future of ἔρχομαι.",
        "tables": [
            _t("present", "active", "indicative", _s("εἶμι εἶ εἶσι(ν) ἴμεν ἴτε ἴασι(ν)")),
            _t("present", "active", "subjunctive", _s("ἴω ἴῃς ἴῃ ἴωμεν ἴητε ἴωσι(ν)")),
            _t("present", "active", "optative", _s("ἴοιμι/ἰοίην ἴοις ἴοι ἴοιμεν ἴοιτε ἴοιεν")),
            _t("present", "active", "imperative", _s("- ἴθι ἴτω - ἴτε ἰόντων")),
            _t("present", "active", "infinitive", ["ἰέναι"]),
            _t("present", "active", "participle", ["ἰών", "ἰοῦσα", "ἰόν", "ἰόντος"]),
            _t("imperfect", "active", "indicative", _s("ᾖα/ᾔειν ᾔεισθα/ᾔεις ᾔει/ᾔειν ᾖμεν ᾖτε ᾖσαν/ᾔεσαν")),
        ],
    },
    "φημί": {
        "note": "‘say’. The present indicative is enclitic except φῄς. The imperfect ἔφην is used as a past ‘said’; οὔ φημι means ‘deny’.",
        "tables": [
            _t("present", "active", "indicative", _s("φημί φῄς φησί(ν) φαμέν φατέ φασί(ν)")),
            _t("present", "active", "subjunctive", _s("φῶ φῇς φῇ φῶμεν φῆτε φῶσι(ν)")),
            _t("present", "active", "optative", _s("φαίην φαίης φαίη φαῖμεν/φαίημεν φαῖτε φαῖεν")),
            _t("present", "active", "imperative", _s("- φάθι/φαθί φάτω - φάτε φάντων")),
            _t("present", "active", "infinitive", ["φάναι"]),
            _t("present", "active", "participle", ["φάς (usually φάσκων)", "φᾶσα", "φάν", "φάντος"]),
            _t("imperfect", "active", "indicative", _s("ἔφην ἔφησθα/ἔφης ἔφη ἔφαμεν ἔφατε ἔφασαν")),
            _t("future", "active", "indicative", _s("φήσω φήσεις φήσει φήσομεν φήσετε φήσουσι(ν)")),
            _t("future", "active", "infinitive", ["φήσειν"]),
            _t("aorist", "active", "indicative", _s("ἔφησα ἔφησας ἔφησε(ν) ἐφήσαμεν ἐφήσατε ἔφησαν")),
            _t("aorist", "active", "infinitive", ["φῆσαι"]),
            _t("aorist", "active", "participle", ["φήσας", "φήσασα", "φῆσαν", "φήσαντος"]),
        ],
    },
    "οἶδα": {
        "note": "‘know’: a perfect in form with present meaning; the pluperfect ᾔδη serves as the imperfect. Future εἴσομαι.",
        "tables": [
            _t("perfect", "active", "indicative", _s("οἶδα οἶσθα οἶδε(ν) ἴσμεν ἴστε ἴσασι(ν)"), "Present meaning ‘I know’."),
            _t("perfect", "active", "subjunctive", _s("εἰδῶ εἰδῇς εἰδῇ εἰδῶμεν εἰδῆτε εἰδῶσι(ν)")),
            _t("perfect", "active", "optative", _s("εἰδείην εἰδείης εἰδείη εἰδεῖμεν/εἰδείημεν εἰδεῖτε εἰδεῖεν")),
            _t("perfect", "active", "imperative", _s("- ἴσθι ἴστω - ἴστε ἴστων")),
            _t("perfect", "active", "infinitive", ["εἰδέναι"]),
            _t("perfect", "active", "participle", ["εἰδώς", "εἰδυῖα", "εἰδός", "εἰδότος"]),
            _t("pluperfect", "active", "indicative", _s("ᾔδη/ᾔδειν ᾔδησθα/ᾔδεις ᾔδει(ν) ᾖσμεν/ᾔδεμεν ᾖστε/ᾔδετε ᾖσαν/ᾔδεσαν"), "Past meaning ‘I knew’."),
            _t("future", "middle", "indicative", _s("εἴσομαι εἴσῃ/εἴσει εἴσεται εἰσόμεθα εἴσεσθε εἴσονται")),
            _t("future", "middle", "infinitive", ["εἴσεσθαι"]),
        ],
    },
    "ἔοικα": {
        "note": "‘seem, be like’ (+dat.): a perfect with present meaning. ἔοικε ‘it seems’ is common; the participle εἰκώς means ‘likely, reasonable’.",
        "tables": [
            _t("perfect", "active", "indicative", _s("ἔοικα ἔοικας ἔοικε(ν) ἐοίκαμεν ἐοίκατε ἐοίκασι(ν)")),
            _t("perfect", "active", "subjunctive", _s("ἐοίκω ἐοίκῃς ἐοίκῃ ἐοίκωμεν ἐοίκητε ἐοίκωσι(ν)")),
            _t("perfect", "active", "optative", _s("ἐοίκοιμι ἐοίκοις ἐοίκοι ἐοίκοιμεν ἐοίκοιτε ἐοίκοιεν")),
            _t("perfect", "active", "infinitive", ["ἐοικέναι"]),
            _t("perfect", "active", "participle", ["εἰκώς/ἐοικώς", "εἰκυῖα", "εἰκός", "εἰκότος"]),
            _t("pluperfect", "active", "indicative", _s("ἐῴκη ἐῴκης ἐῴκει ἐῴκεμεν ἐῴκετε ἐῴκεσαν")),
        ],
    },
    "δέδοικα": {
        "note": "‘fear’: perfect with present meaning (also δέδια); pluperfect ἐδεδοίκη/ἐδέδια ‘I feared’.",
        "tables": [
            _t("perfect", "active", "indicative", _s("δέδοικα/δέδια δέδοικας/δέδιας δέδοικε(ν)/δέδιε(ν) δεδοίκαμεν/δέδιμεν δεδοίκατε/δέδιτε δεδοίκασι(ν)/δεδίασι(ν)")),
            _t("perfect", "active", "subjunctive", _s("δεδίω δεδίῃς δεδίῃ δεδίωμεν δεδίητε δεδίωσι(ν)")),
            _t("perfect", "active", "optative", _s("δεδιείην δεδιείης δεδιείη δεδιεῖμεν δεδιεῖτε δεδιεῖεν")),
            _t("perfect", "active", "imperative", _s("- δέδιθι δεδίτω - δέδιτε δεδιόντων")),
            _t("perfect", "active", "infinitive", ["δεδιέναι/δεδοικέναι"]),
            _t("perfect", "active", "participle", ["δεδιώς/δεδοικώς", "δεδιυῖα", "δεδιός", "δεδιότος"]),
            _t("pluperfect", "active", "indicative", _s("ἐδεδοίκη/ἐδέδια ἐδεδοίκης/ἐδέδιας ἐδεδοίκει/ἐδέδιε ἐδέδιμεν ἐδέδιτε ἐδέδισαν")),
            _t("future", "middle", "indicative", _s("δείσομαι δείσῃ δείσεται δεισόμεθα δείσεσθε δείσονται")),
            _t("aorist", "active", "indicative", _s("ἔδεισα ἔδεισας ἔδεισε(ν) ἐδείσαμεν ἐδείσατε ἔδεισαν")),
            _t("aorist", "active", "subjunctive", _s("δείσω δείσῃς δείσῃ δείσωμεν δείσητε δείσωσι(ν)")),
            _t("aorist", "active", "infinitive", ["δεῖσαι"]),
            _t("aorist", "active", "participle", ["δείσας", "δείσασα", "δεῖσαν", "δείσαντος"]),
        ],
    },
    "κεῖμαι": {
        "note": "‘lie, be placed’: a -μι deponent used as the perfect passive of τίθημι (‘have been put’).",
        "tables": [
            _t("present", "middle", "indicative", _s("κεῖμαι κεῖσαι κεῖται κείμεθα κεῖσθε κεῖνται")),
            _t("present", "middle", "subjunctive", _s("κέωμαι κέῃ κέηται κεώμεθα κέησθε κέωνται")),
            _t("present", "middle", "optative", _s("κεοίμην κέοιο κέοιτο κεοίμεθα κέοισθε κέοιντο")),
            _t("present", "middle", "imperative", _s("- κεῖσο κείσθω - κεῖσθε κείσθων")),
            _t("present", "middle", "infinitive", ["κεῖσθαι"]),
            _t("present", "middle", "participle", ["κείμενος", "κειμένη", "κείμενον", "κειμένου"]),
            _t("imperfect", "middle", "indicative", _s("ἐκείμην ἔκεισο ἔκειτο ἐκείμεθα ἔκεισθε ἔκειντο")),
            _t("future", "middle", "indicative", _s("κείσομαι κείσῃ κείσεται κεισόμεθα κείσεσθε κείσονται")),
            _t("future", "middle", "infinitive", ["κείσεσθαι"]),
        ],
    },
    "ἵημι": {
        "note": "‘send, throw, let go’ (stem ἱη-/ἱε-; aorist root ἑ-). Rare as a simplex in prose; the compounds ἀφίημι, συνίημι, παρίημι are common.",
        "tables": [
            _t("present", "active", "indicative", _s("ἵημι ἵης ἵησι(ν) ἵεμεν ἵετε ἱᾶσι(ν)")),
            _t("present", "active", "subjunctive", _s("ἱῶ ἱῇς ἱῇ ἱῶμεν ἱῆτε ἱῶσι(ν)")),
            _t("present", "active", "optative", _s("ἱείην ἱείης ἱείη ἱεῖμεν ἱεῖτε ἱεῖεν")),
            _t("present", "active", "imperative", _s("- ἵει ἱέτω - ἵετε ἱέντων")),
            _t("present", "active", "infinitive", ["ἱέναι"]),
            _t("present", "active", "participle", ["ἱείς", "ἱεῖσα", "ἱέν", "ἱέντος"]),
            _t("imperfect", "active", "indicative", _s("ἵην ἵεις ἵει ἵεμεν ἵετε ἵεσαν")),
            _t("present", "middle/passive", "indicative", _s("ἵεμαι ἵεσαι ἵεται ἱέμεθα ἵεσθε ἵενται")),
            _t("present", "middle/passive", "subjunctive", _s("ἱῶμαι ἱῇ ἱῆται ἱώμεθα ἱῆσθε ἱῶνται")),
            _t("present", "middle/passive", "optative", _s("ἱείμην ἱεῖο ἱεῖτο ἱείμεθα ἱεῖσθε ἱεῖντο")),
            _t("present", "middle/passive", "imperative", _s("- ἵεσο ἱέσθω - ἵεσθε ἱέσθων")),
            _t("present", "middle/passive", "infinitive", ["ἵεσθαι"]),
            _t("present", "middle/passive", "participle", ["ἱέμενος", "ἱεμένη", "ἱέμενον", "ἱεμένου"]),
            _t("imperfect", "middle/passive", "indicative", _s("ἱέμην ἵεσο ἵετο ἱέμεθα ἵεσθε ἵεντο")),
            _t("future", "active", "indicative", _s("ἥσω ἥσεις ἥσει ἥσομεν ἥσετε ἥσουσι(ν)")),
            _t("future", "active", "infinitive", ["ἥσειν"]),
            _t("future", "middle", "indicative", _s("ἥσομαι ἥσῃ ἥσεται ἡσόμεθα ἥσεσθε ἥσονται")),
            _t("future", "passive", "indicative", _s("ἑθήσομαι ἑθήσῃ ἑθήσεται ἑθησόμεθα ἑθήσεσθε ἑθήσονται")),
            _t("aorist", "active", "indicative", _s("ἧκα ἧκας ἧκε(ν) εἷμεν εἷτε εἷσαν")),
            _t("aorist", "active", "subjunctive", _s("ὧ ᾗς ᾗ ὧμεν ἧτε ὧσι(ν)")),
            _t("aorist", "active", "optative", _s("εἵην εἵης εἵη εἷμεν εἷτε εἷεν")),
            _t("aorist", "active", "imperative", _s("- ἕς ἕτω - ἕτε ἕντων")),
            _t("aorist", "active", "infinitive", ["εἷναι"]),
            _t("aorist", "active", "participle", ["εἵς", "εἷσα", "ἕν", "ἕντος"]),
            _t("aorist", "middle", "indicative", _s("εἵμην εἷσο εἷτο εἵμεθα εἷσθε εἷντο")),
            _t("aorist", "middle", "subjunctive", _s("ὧμαι ᾗ ἧται ὥμεθα ἧσθε ὧνται")),
            _t("aorist", "middle", "optative", _s("εἵμην εἷο εἷτο εἵμεθα εἷσθε εἷντο")),
            _t("aorist", "middle", "imperative", _s("- οὗ ἕσθω - ἕσθε ἕσθων")),
            _t("aorist", "middle", "infinitive", ["ἕσθαι"]),
            _t("aorist", "middle", "participle", ["ἕμενος", "ἑμένη", "ἕμενον", "ἑμένου"]),
            _t("aorist", "passive", "indicative", _s("εἵθην εἵθης εἵθη εἵθημεν εἵθητε εἵθησαν")),
            _t("aorist", "passive", "subjunctive", _s("ἑθῶ ἑθῇς ἑθῇ ἑθῶμεν ἑθῆτε ἑθῶσι(ν)")),
            _t("aorist", "passive", "infinitive", ["ἑθῆναι"]),
            _t("aorist", "passive", "participle", ["ἑθείς", "ἑθεῖσα", "ἑθέν", "ἑθέντος"]),
            _t("perfect", "active", "indicative", _s("εἷκα εἷκας εἷκε(ν) εἵκαμεν εἵκατε εἵκασι(ν)")),
            _t("perfect", "active", "infinitive", ["εἱκέναι"]),
            _t("perfect", "middle/passive", "indicative", _s("εἷμαι εἷσαι εἷται εἵμεθα εἷσθε εἷνται")),
            _t("perfect", "middle/passive", "participle", ["εἱμένος", "εἱμένη", "εἱμένον", "εἱμένου"]),
        ],
    },
    "ἀφίημι": {
        "note": "ἀπό + ἵημι, ‘send away, let go, allow’: conjugated like ἵημι with the prefix (ἀφ- before the rough breathing, ἀπ- elsewhere: ἀφίημι, ἀφῆκα, ἀπεῖναι).",
        "tables": [
            _t("present", "active", "indicative", _s("ἀφίημι ἀφίης ἀφίησι(ν) ἀφίεμεν ἀφίετε ἀφιᾶσι(ν)")),
            _t("present", "active", "subjunctive", _s("ἀφιῶ ἀφιῇς ἀφιῇ ἀφιῶμεν ἀφιῆτε ἀφιῶσι(ν)")),
            _t("present", "active", "optative", _s("ἀφιείην ἀφιείης ἀφιείη ἀφιεῖμεν ἀφιεῖτε ἀφιεῖεν")),
            _t("present", "active", "imperative", _s("- ἀφίει ἀφιέτω - ἀφίετε ἀφιέντων")),
            _t("present", "active", "infinitive", ["ἀφιέναι"]),
            _t("present", "active", "participle", ["ἀφιείς", "ἀφιεῖσα", "ἀφιέν", "ἀφιέντος"]),
            _t("imperfect", "active", "indicative", _s("ἀφίην ἀφίεις ἀφίει ἀφίεμεν ἀφίετε ἀφίεσαν")),
            _t("present", "middle/passive", "indicative", _s("ἀφίεμαι ἀφίεσαι ἀφίεται ἀφιέμεθα ἀφίεσθε ἀφίενται")),
            _t("present", "middle/passive", "infinitive", ["ἀφίεσθαι"]),
            _t("present", "middle/passive", "participle", ["ἀφιέμενος", "ἀφιεμένη", "ἀφιέμενον", "ἀφιεμένου"]),
            _t("imperfect", "middle/passive", "indicative", _s("ἀφιέμην ἀφίεσο ἀφίετο ἀφιέμεθα ἀφίεσθε ἀφίεντο")),
            _t("future", "active", "indicative", _s("ἀφήσω ἀφήσεις ἀφήσει ἀφήσομεν ἀφήσετε ἀφήσουσι(ν)")),
            _t("future", "active", "infinitive", ["ἀφήσειν"]),
            _t("future", "middle", "indicative", _s("ἀφήσομαι ἀφήσῃ ἀφήσεται ἀφησόμεθα ἀφήσεσθε ἀφήσονται")),
            _t("future", "passive", "indicative", _s("ἀφεθήσομαι ἀφεθήσῃ ἀφεθήσεται ἀφεθησόμεθα ἀφεθήσεσθε ἀφεθήσονται")),
            _t("aorist", "active", "indicative", _s("ἀφῆκα ἀφῆκας ἀφῆκε(ν) ἀφεῖμεν ἀφεῖτε ἀφεῖσαν")),
            _t("aorist", "active", "subjunctive", _s("ἀφῶ ἀφῇς ἀφῇ ἀφῶμεν ἀφῆτε ἀφῶσι(ν)")),
            _t("aorist", "active", "optative", _s("ἀφείην ἀφείης ἀφείη ἀφεῖμεν ἀφεῖτε ἀφεῖεν")),
            _t("aorist", "active", "imperative", _s("- ἄφες ἀφέτω - ἄφετε ἀφέντων")),
            _t("aorist", "active", "infinitive", ["ἀφεῖναι"]),
            _t("aorist", "active", "participle", ["ἀφείς", "ἀφεῖσα", "ἀφέν", "ἀφέντος"]),
            _t("aorist", "middle", "indicative", _s("ἀφείμην ἀφεῖσο ἀφεῖτο ἀφείμεθα ἀφεῖσθε ἀφεῖντο")),
            _t("aorist", "middle", "subjunctive", _s("ἀφῶμαι ἀφῇ ἀφῆται ἀφώμεθα ἀφῆσθε ἀφῶνται")),
            _t("aorist", "middle", "imperative", _s("- ἀφοῦ ἀφέσθω - ἀφέσθε ἀφέσθων")),
            _t("aorist", "middle", "infinitive", ["ἀφέσθαι"]),
            _t("aorist", "middle", "participle", ["ἀφέμενος", "ἀφεμένη", "ἀφέμενον", "ἀφεμένου"]),
            _t("aorist", "passive", "indicative", _s("ἀφείθην ἀφείθης ἀφείθη ἀφείθημεν ἀφείθητε ἀφείθησαν")),
            _t("aorist", "passive", "subjunctive", _s("ἀφεθῶ ἀφεθῇς ἀφεθῇ ἀφεθῶμεν ἀφεθῆτε ἀφεθῶσι(ν)")),
            _t("aorist", "passive", "infinitive", ["ἀφεθῆναι"]),
            _t("aorist", "passive", "participle", ["ἀφεθείς", "ἀφεθεῖσα", "ἀφεθέν", "ἀφεθέντος"]),
            _t("perfect", "active", "indicative", _s("ἀφεῖκα ἀφεῖκας ἀφεῖκε(ν) ἀφείκαμεν ἀφείκατε ἀφείκασι(ν)")),
            _t("perfect", "active", "infinitive", ["ἀφεικέναι"]),
            _t("perfect", "middle/passive", "indicative", _s("ἀφεῖμαι ἀφεῖσαι ἀφεῖται ἀφείμεθα ἀφεῖσθε ἀφεῖνται")),
            _t("perfect", "middle/passive", "participle", ["ἀφειμένος", "ἀφειμένη", "ἀφειμένον", "ἀφειμένου"]),
        ],
    },
    "χρή": {
        "note": "‘it is necessary’ (+acc. and infinitive): originally a noun (‘need’) + ἐστί, so it has no personal forms.",
        "tables": [
            _t("present", "active", "indicative", [None, None, "χρή", None, None, None]),
            _t("present", "active", "subjunctive", [None, None, "χρῇ", None, None, None]),
            _t("present", "active", "optative", [None, None, "χρείη", None, None, None]),
            _t("present", "active", "infinitive", ["χρῆναι"]),
            _t("present", "active", "participle", ["χρεών (indecl.)", None, None, None]),
            _t("imperfect", "active", "indicative", [None, None, "χρῆν/ἐχρῆν", None, None, None]),
            _t("future", "active", "indicative", [None, None, "χρήσται (rare)", None, None, None]),
        ],
    },
    "δεῖ": {
        "note": "‘it is necessary, one must’ (+acc. and infinitive); ‘there is need of’ (+gen.). Impersonal 3rd singular of δέω.",
        "tables": [
            _t("present", "active", "indicative", [None, None, "δεῖ", None, None, None]),
            _t("present", "active", "subjunctive", [None, None, "δέῃ", None, None, None]),
            _t("present", "active", "optative", [None, None, "δέοι", None, None, None]),
            _t("present", "active", "infinitive", ["δεῖν"]),
            _t("present", "active", "participle", ["δέον", None, None, "δέοντος"]),
            _t("imperfect", "active", "indicative", [None, None, "ἔδει", None, None, None]),
            _t("future", "active", "indicative", [None, None, "δεήσει", None, None, None]),
            _t("aorist", "active", "indicative", [None, None, "ἐδέησε(ν)", None, None, None]),
            _t("aorist", "active", "subjunctive", [None, None, "δεήσῃ", None, None, None]),
            _t("aorist", "active", "infinitive", ["δεῆσαι"]),
        ],
    },
}
