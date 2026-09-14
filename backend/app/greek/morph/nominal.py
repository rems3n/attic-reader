"""Declension of nouns, adjectives, pronouns and numerals (Classical Attic).

Regular classes are generated from endings + the persistent-accent rules in
`accent.py`; irregular words come from `tables.py`. Output shape:

    noun:       {"kind": "noun", "lemma", "gender", "cells": [{"case", "number", "forms": [..]}], "note"}
    adjective:  {"kind": "adjective"|"pronoun"|"article", "lemma", "genders": [..],
                 "cells": [{"case", "number", "forms": {gender: [..]}}], "comparison", "adverb", "note"}
"""

from __future__ import annotations

import re

from . import tables
from .accent import (
    nfd,
    accent_from_start,
    accent_position,
    accentuate,
    finish,
    nfc,
    persistent,
    recessive,
    strip_accent,
    syllable_is_long,
    syllables,
)

CASES = ("nom", "gen", "dat", "acc", "voc")
GEN_DAT = {"gen", "dat"}

# Words whose penult vowel is long but unmarked in the lemma; the macron
# matters only for circumflex vs acute (νῖκαι, πολῖτα).
LONG_STEMS = {
    "νίκη": "νῑ́κη",
    "πολίτης": "πολῑ́της",
    "ἰσχυρός": "ἰσχῡρός",
}

FIRST_SG = {
    "eta": ["η", "ης", "ῃ", "ην", "η"],
    "alpha-long": ["ᾱ", "ᾱς", "ᾳ", "ᾱν", "ᾱ"],
    "alpha-short-as": ["α", "ᾱς", "ᾳ", "αν", "α"],
    "alpha-short-es": ["α", "ης", "ῃ", "αν", "α"],
    "masc-es": ["ης", "ου", "ῃ", "ην", "η"],
    "masc-as": ["ᾱς", "ου", "ᾳ", "ᾱν", "ᾱ"],
}
FIRST_PL = ["αι", "ων", "αις", "ᾱς", "αι"]
SECOND_SG = {"m": ["ος", "ου", "ῳ", "ον", "ε"], "n": ["ον", "ου", "ῳ", "ον", "ον"]}
SECOND_PL = {"m": ["οι", "ων", "οις", "ους", "οι"], "n": ["α", "ων", "οις", "α", "α"]}
THIRD_PL = {"mf": ["ες", "ων", "σι(ν)", "ας", "ες"], "n": ["α", "ων", "σι(ν)", "α", "α"]}
SIGMA_SG = ["ος", "ους", "ει", "ος", "ος"]
SIGMA_PL = ["η", "ῶν", "εσι(ν)", "η", "η"]
IOTA_SG = ["ις", "εως", "ει", "ιν", "ι"]
IOTA_PL = ["εις", "εων", "εσι(ν)", "εις", "εις"]
EUS_SG = ["εύς", "έως", "εῖ", "έᾱ", "εῦ"]
EUS_PL = [["ῆς", "εῖς"], "έων", "εῦσι(ν)", "έᾱς", ["ῆς", "εῖς"]]
ES_ADJ = {  # ἀληθής -ές (oxytone σ-stems)
    ("mf", "sg"): ["ής", "οῦς", "εῖ", "ῆ", "ές"],
    ("n", "sg"): ["ές", "οῦς", "εῖ", "ές", "ές"],
    ("mf", "pl"): ["εῖς", "ῶν", "έσι(ν)", "εῖς", "εῖς"],
    ("n", "pl"): ["ῆ", "ῶν", "έσι(ν)", "ῆ", "ῆ"],
}
US_ADJ = {  # ταχύς ταχεῖα ταχύ
    ("m", "sg"): ["ύς", "έος", "εῖ", "ύν", "ύ"],
    ("f", "sg"): ["εῖα", "είᾱς", "είᾳ", "εῖαν", "εῖα"],
    ("n", "sg"): ["ύ", "έος", "εῖ", "ύ", "ύ"],
    ("m", "pl"): ["εῖς", "έων", "έσι(ν)", "εῖς", "εῖς"],
    ("f", "pl"): ["εῖαι", "ειῶν", "είαις", "είᾱς", "εῖαι"],
    ("n", "pl"): ["έα", "έων", "έσι(ν)", "έα", "έα"],
}
ON_ADJ = {  # βελτίων βέλτιον (stem -ον-)
    ("mf", "sg"): ["ων", "ονος", "ονι", ["ονα", "ω"], "ον"],
    ("n", "sg"): ["ον", "ονος", "ονι", "ον", "ον"],
    ("mf", "pl"): [["ονες", "ους"], "ονων", "οσι(ν)", ["ονας", "ους"], ["ονες", "ους"]],
    ("n", "pl"): [["ονα", "ω"], "ονων", "οσι(ν)", ["ονα", "ω"], ["ονα", "ω"]],
}

VOC_RECESSIVE = {"ἀδελφός": "ἄδελφε", "δεσπότης": "δέσποτα", "πονηρός": "πόνηρε"}


def _has_accent(text: str) -> bool:
    return accent_position(text) is not None


def _join(stem: str, ending: str, idx: int, case: str, oxytone: bool, fixed_from_end: int | None = None) -> str:
    """Attach an ending and place the accent.

    * an accented ending (ῶν, έως …) wins over the stem accent;
    * otherwise the stem accent persists (with the law of limitation), and
      oxytone words take a circumflex on the ending in the genitive/dative.
    """
    paren = ""
    if ending.endswith("(ν)"):
        ending, paren = ending[:-3], "(ν)"
    if _has_accent(ending):
        form = strip_accent(stem) + ending
    elif fixed_from_end is not None:
        form = accentuate(stem + ending, fixed_from_end, "acute")
    else:
        kind = "circumflex" if (oxytone and case in GEN_DAT) else "acute"
        form = persistent(stem + ending, idx, kind)
    return finish(form) + paren


def _cells_noun(forms_sg: list, forms_pl: list) -> list[dict]:
    cells = []
    for number, forms in (("sg", forms_sg), ("pl", forms_pl)):
        for case, f in zip(CASES, forms):
            cells.append({"case": case, "number": number, "forms": f if isinstance(f, list) else [f]})
    return cells


def _stem_info(lemma: str) -> tuple[str, int, bool]:
    """(lemma with long-vowel hints, accent index from start, oxytone?)."""
    hinted = LONG_STEMS.get(lemma, lemma)
    idx = accent_from_start(hinted)
    pos = accent_position(hinted)
    oxytone = pos is not None and pos[0] == 1
    return hinted, idx, oxytone


# ---------------------------------------------------------------------------
# Nouns
# ---------------------------------------------------------------------------


def first_declension_type(lemma: str, genitive: str, gender: str) -> str:
    bare_l = strip_accent(lemma)
    bare_g = strip_accent(genitive)
    if gender == "m":
        return "masc-as" if bare_l.endswith("ας") else "masc-es"
    if bare_l.endswith("η"):
        return "eta"
    # feminine in -α
    if bare_g.endswith("ης"):
        return "alpha-short-es"
    pos = accent_position(lemma)
    n = len(syllables(lemma))
    if pos == (1, "acute") or pos == (1, "circumflex"):
        return "alpha-long"  # στρατιά, διαφορά
    if pos == (2, "acute"):
        return "alpha-long"  # χώρα, ἡμέρα, οἰκία (a short α would force a circumflex)
    if n >= 3 and pos and pos[0] == 3:
        return "alpha-short-as"  # ἀλήθεια, θάλαττα-type with -ας genitive
    if pos == (2, "circumflex"):
        return "alpha-short-as"  # μοῖρα
    return "alpha-long"


def decline_noun(lemma: str, genitive: str, gender: str, subclass: str) -> dict:
    if lemma in tables.NOUNS:
        out = dict(tables.NOUNS[lemma])
        out["lemma"] = lemma
        return out
    hinted, idx, oxytone = _stem_info(lemma)
    note = ""
    if subclass == "noun-1":
        typ = first_declension_type(lemma, genitive, gender)
        endings = FIRST_SG[typ]
        n_end = 2 if typ.startswith("masc") else 1
        stem = hinted[:-n_end]
        if typ == "masc-es" and strip_accent(lemma).endswith("της"):
            endings = endings[:4] + ["α"]  # πολῖτα, στρατιῶτα
        sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, endings)]
        pl = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, FIRST_PL)]
        pl[1] = finish(strip_accent(stem) + "ῶν")  # nouns: gen. pl. always -ῶν
        if lemma in VOC_RECESSIVE:
            sg[4] = VOC_RECESSIVE[lemma]
        note = {
            "eta": "First declension in -η (-η, -ης, -ῃ, -ην).",
            "alpha-long": "First declension with long ᾱ throughout the singular (after ε, ι, ρ or by accent).",
            "alpha-short-as": "First declension with short α in the nominative/accusative singular and -ᾱς, -ᾳ in the genitive/dative (after ε, ι, ρ).",
            "alpha-short-es": "First declension with short α in the nominative/accusative and -ης, -ῃ in the genitive/dative.",
            "masc-es": "First-declension masculine in -ης: genitive singular -ου, vocative -α (nouns in -της) or -η.",
            "masc-as": "First-declension masculine in -ᾱς: genitive singular -ου.",
        }[typ] + " Genitive plural always -ῶν."
        return {"kind": "noun", "lemma": lemma, "gender": gender, "declension": "1", "note": note, "cells": _cells_noun(sg, pl)}

    if subclass == "noun-2":
        g = "n" if gender == "n" else "m"
        stem = hinted[:-2]
        sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SECOND_SG[g])]
        pl = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SECOND_PL[g])]
        if lemma in VOC_RECESSIVE:
            sg[4] = VOC_RECESSIVE[lemma]
        if lemma == "θεός":
            sg[4] = "θεός"
        note = "Second declension " + ("neuter in -ον (nominative = accusative = vocative; plural in -α)." if g == "n" else "in -ος.")
        if oxytone:
            note += " Oxytone: the genitive and dative take a circumflex (-οῦ, -ῷ, -ῶν, -οῖς)."
        return {"kind": "noun", "lemma": lemma, "gender": gender, "declension": "2", "note": note, "cells": _cells_noun(sg, pl)}

    if subclass == "noun-3-sigma":
        stem = hinted[:-2]
        sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SIGMA_SG)]
        pl = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SIGMA_PL)]
        note = "Third-declension σ-stem neuter (stem γενεσ-): the σ drops between vowels and the vowels contract (γένε-ος → γένους, γένε-α → γένη, γενέ-ων → γενῶν)."
        return {"kind": "noun", "lemma": lemma, "gender": gender, "declension": "3", "note": note, "cells": _cells_noun(sg, pl)}

    if subclass == "noun-3-iota":
        stem = hinted[:-2]
        sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, IOTA_SG)]
        pl = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, IOTA_PL)]
        # -εως / -εων keep the accent on the antepenult (πόλεως, δυνάμεως),
        # and so does the dative plural (δυνάμεσι)
        sg[1] = finish(accentuate(stem + "εως", 3, "acute"))
        pl[1] = finish(accentuate(stem + "εων", 3, "acute"))
        pl[2] = finish(accentuate(stem + "εσι", 3, "acute")) + "(ν)"
        sg[4] = lemma[:-1]  # πρᾶξι, πόλι: the nominative without -ς
        note = "Third-declension ι-stem (πόλις type): stem πολι-/πολε-; genitive -εως and -εων keep the accent on the antepenult; accusative singular -ιν."
        return {"kind": "noun", "lemma": lemma, "gender": gender, "declension": "3", "note": note, "cells": _cells_noun(sg, pl)}

    if subclass == "noun-3-eus":
        stem = hinted[:-3]
        sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, EUS_SG)]
        pl = [[_join(stem, x, idx, c, oxytone) for x in e] if isinstance(e, list) else _join(stem, e, idx, c, oxytone) for c, e in zip(CASES, EUS_PL)]
        note = "Third-declension -εύς nouns (stem βασιλευ-/βασιλε-): genitive -έως, accusative -έᾱ, nominative plural -ῆς (older) or -εῖς."
        return {"kind": "noun", "lemma": lemma, "gender": gender, "declension": "3", "note": note, "cells": _cells_noun(sg, pl)}

    # consonant stems (and anything irregular the tables do not cover)
    return _decline_third_consonant(lemma, hinted, genitive, gender, idx, oxytone)


def _lemma_nominative(table: dict, lemma: str) -> dict:
    """The nominative singular is the lemma as given (a properispomenon like
    πρᾶξις carries length information the rules cannot recover)."""
    pos = accent_position(lemma)
    properispomenon = pos == (2, "circumflex")
    n_lemma = len(syllables(lemma))
    for c in table["cells"]:
        if c["case"] == "nom" and c["number"] == "sg" and c["forms"] and c["forms"][0] != lemma and strip_accent(c["forms"][0]) == strip_accent(lemma):
            c["forms"] = [lemma]
        if c["case"] == "voc" and c["number"] == "sg" and c["forms"] and strip_accent(c["forms"][0]) == strip_accent(lemma) and c["forms"][0] != lemma:
            c["forms"] = [lemma]
        # πρᾶξις → πρᾶξιν, πρᾶξι: the hidden-long penult of a properispomenon
        # lemma stays long in the other singular forms with a short ending.
        if properispomenon and c["number"] == "sg" and c["forms"]:
            fixed = []
            for f in c["forms"]:
                bare = strip_accent(f)
                sylls = syllables(bare)
                if (len(sylls) == n_lemma and bare[:-1] == strip_accent(lemma)[:-1]
                        and accent_position(f) == (2, "acute") and not syllable_is_long(sylls[-1], True)):
                    f = accentuate(bare, 2, "circumflex")
                fixed.append(f)
            c["forms"] = fixed
    return table


def _dative_plural_stem(stem: str) -> str:
    """Stem + σι with the usual assimilations (φύλακ-σι → φύλαξι, σώματ-σι → σώμασι)."""
    bare = stem
    if bare.endswith(("π", "β", "φ")):
        return bare[:-1] + "ψ"
    if bare.endswith(("κ", "γ", "χ")):
        return bare[:-1] + "ξ"
    if bare.endswith(("τ", "δ", "θ")):
        if bare.endswith("ντ"):  # γίγαντ-σι → γίγᾱσι, γέροντ-σι → γέρουσι
            core = bare[:-2]
            v = core[-1]
            core = core[:-1] + {"α": "ᾱ", "ε": "ει", "ο": "ου"}.get(v, v)
            return core + "σ"
        return bare[:-1] + "σ"
    if bare.endswith("ν"):
        return bare[:-1] + "σ"
    return bare + "σ"


def _decline_third_consonant(lemma: str, hinted: str, genitive: str, gender: str, idx: int, oxytone: bool) -> dict:
    gen_bare = strip_accent(genitive)
    if not gen_bare.endswith("ος"):
        raise ValueError(f"cannot find the stem of {lemma} from {genitive}")
    stem = genitive[:-2]
    stem = strip_accent(stem)
    bare_lemma = strip_accent(lemma)
    neuter = gender == "n"
    monosyllabic = len(syllables(lemma)) == 1

    def form(ending: str, case: str, number: str) -> str:
        if monosyllabic and case in GEN_DAT:
            # πούς → ποδός, ποδί, ποδῶν, ποσί
            paren = "(ν)" if ending.endswith("(ν)") else ""
            e = ending[:-3] if paren else ending
            kind = "circumflex" if (case == "gen" and number == "pl") else "acute"
            return finish(accentuate(stem + e, 1, kind)) + paren
        return _join(stem, ending, idx, case, oxytone)

    # accusative singular: -ν for dental stems in unaccented -ις/-υς (χάριν, ἔριν)
    acc_ending = "α"
    if bare_lemma.endswith(("ις", "υς")) and stem.endswith(("δ", "τ", "θ")) and not oxytone:
        acc_sg = finish(persistent(stem[:-1] + "ν", idx))
    else:
        acc_sg = lemma if neuter else form(acc_ending, "acc", "sg")

    # vocative singular
    voc_sg = lemma
    if not neuter:
        if bare_lemma.endswith("ων") and gen_bare.endswith("ονος") and not oxytone:
            voc_sg = finish(recessive(stem))  # δαῖμον
        elif bare_lemma.endswith("ων") and gen_bare.endswith("οντος") and not oxytone:
            voc_sg = finish(recessive(stem[:-1]))  # γέρον
        elif bare_lemma.endswith("ις") and stem.endswith(("δ", "τ")):
            voc_sg = finish(persistent(stem[:-1], idx, "acute"))  # ἐλπί, χάρι, πατρί
    sg = [lemma, form("ος", "gen", "sg"), form("ι", "dat", "sg"), acc_sg, voc_sg]

    dat_pl_stem = _dative_plural_stem(stem)
    endings = THIRD_PL["n" if neuter else "mf"]
    pl = []
    for case, e in zip(CASES, endings):
        if case == "dat":
            if monosyllabic:
                pl.append(finish(accentuate(dat_pl_stem + "ι", 1, "acute")) + "(ν)")
            else:
                pl.append(finish(persistent(dat_pl_stem + "ι", idx)) + "(ν)")
        else:
            pl.append(form(e, case, "pl"))
    kind_note = "neuter " if neuter else ""
    note = (
        f"Third-declension {kind_note}consonant stem {stem}- (from the genitive {genitive}): "
        "endings -ος, -ι, -α; plural -ες, -ων, -σι(ν), -ας."
    )
    if neuter:
        note = f"Third-declension neuter stem {stem}-: nominative = accusative = vocative; plural in -α, dative plural {pl[2]}."
    if monosyllabic:
        note += " Monosyllabic stem: the genitive and dative accent the ending."
    return {"kind": "noun", "lemma": lemma, "gender": gender, "declension": "3", "note": note, "cells": _cells_noun(sg, pl)}


# ---------------------------------------------------------------------------
# Adjectives (and -ος pronouns)
# ---------------------------------------------------------------------------


def _adj_cells(rows: dict[tuple[str, str], list], genders: tuple[str, ...]) -> list[dict]:
    cells = []
    for number in ("sg", "pl"):
        for i, case in enumerate(CASES):
            forms = {}
            for g in genders:
                key = (g, number) if (g, number) in rows else ("mf", number)
                f = rows[key][i]
                forms[g] = f if isinstance(f, list) else [f]
            cells.append({"case": case, "number": number, "forms": forms})
    return cells


def decline_adjective(lemma: str, morph: dict, subclass: str, kind: str = "adjective") -> dict:
    if lemma in tables.ADJECTIVES:
        out = dict(tables.ADJECTIVES[lemma])
        out["lemma"] = lemma
        out.setdefault("comparison", _comparison(lemma, subclass))
        return out
    hinted, idx, oxytone = _stem_info(lemma)
    terminations = morph.get("terminations", 3)
    rows: dict[tuple[str, str], list] = {}
    note = ""

    if subclass in {"adj-1-2", "pronoun", "numeral"} or strip_accent(lemma).endswith("ος"):
        stem = hinted[:-2]
        m_sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SECOND_SG["m"])]
        m_pl = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SECOND_PL["m"])]
        n_sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SECOND_SG["n"])]
        n_pl = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, SECOND_PL["n"])]
        neuter = morph.get("neuter")
        if neuter and not strip_accent(neuter).endswith("ον"):
            # αὐτό, ἄλλο, τοιοῦτο: pronominal neuter without -ν
            n_sg[0] = n_sg[3] = n_sg[4] = neuter
        if terminations == 3:
            fem = morph.get("feminine", "")
            fem_type = "eta" if strip_accent(fem).endswith("η") else "alpha-long"
            f_sg = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, FIRST_SG[fem_type])]
            f_pl = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, FIRST_PL)]
            rows = {("m", "sg"): m_sg, ("f", "sg"): f_sg, ("n", "sg"): n_sg, ("m", "pl"): m_pl, ("f", "pl"): f_pl, ("n", "pl"): n_pl}
            genders: tuple[str, ...] = ("m", "f", "n")
            note = "First/second-declension adjective of three endings (-ος, -η/-ᾱ, -ον)."
            if fem_type != "eta":
                note = "First/second-declension adjective of three endings (-ος, -ᾱ, -ον: feminine in ᾱ after ε, ι, ρ)."
        else:
            rows = {("mf", "sg"): m_sg, ("n", "sg"): n_sg, ("mf", "pl"): m_pl, ("n", "pl"): n_pl}
            genders = ("mf", "n")
            note = "Adjective of two endings (compounds and some others): masculine and feminine share the -ος forms."
        if oxytone:
            note += " Oxytone: circumflex in the genitive and dative."
        if kind == "pronoun":
            note = note.replace("adjective", "pronoun/adjective")
    elif subclass == "adj-3-es":
        stem = hinted[:-2]
        for key, ends in ES_ADJ.items():
            rows[key] = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, ends)]
        genders = ("mf", "n")
        note = "Third-declension σ-stem adjective (-ής, -ές): the σ drops and the vowels contract (ἀληθέ-ος → ἀληθοῦς, ἀληθέ-α → ἀληθῆ, ἀληθέ-ες → ἀληθεῖς)."
    elif subclass == "adj-3-on":
        stem = hinted[:-2]
        for key, ends in ON_ADJ.items():
            rows[key] = [[_join(stem, x, idx, c, oxytone) for x in e] if isinstance(e, list) else _join(stem, e, idx, c, oxytone) for c, e in zip(CASES, ends)]
        neuter = finish(recessive(strip_accent(stem) + "ον"))  # βέλτιον, ἧττον
        rows[("mf", "sg")][4] = neuter
        rows[("n", "sg")][0] = rows[("n", "sg")][3] = rows[("n", "sg")][4] = neuter
        genders = ("mf", "n")
        note = "Comparative in -ων, -ον (stem -ον-): beside the regular forms Attic uses contracted -ω (acc. sg., nom./acc. pl. neuter) and -ους (nom./acc. pl. masc./fem.)."
    elif subclass == "adj-us":
        stem = hinted[:-2]
        for key, ends in US_ADJ.items():
            rows[key] = [_join(stem, e, idx, c, oxytone) for c, e in zip(CASES, ends)]
        genders = ("m", "f", "n")
        note = "Adjective in -ύς, -εῖα, -ύ: masculine/neuter third declension (stem -υ-/-ε-), feminine first declension in -εῖα."
    else:
        raise ValueError(f"no adjective rule for {lemma} ({subclass})")

    out = {"kind": kind, "lemma": lemma, "genders": list(genders), "note": note, "cells": _adj_cells(rows, genders)}
    if lemma in tables.NO_VOCATIVE:
        for c in out["cells"]:
            if c["case"] == "voc":
                c["forms"] = {g: [] for g in c["forms"]}
    out["comparison"] = _comparison(lemma, subclass)
    out["adverb"] = _adverb(lemma, subclass, hinted, idx)
    return out


def _comparison(lemma: str, subclass: str) -> dict | None:
    if lemma in tables.COMPARISON:
        comp, sup = tables.COMPARISON[lemma]
        if not comp and not sup:
            return None
        return {"comparative": comp, "superlative": sup, "regular": False}
    if lemma in tables.NO_COMPARISON or lemma in tables.NO_COMPARISON_EXTRA:
        return None
    bare = strip_accent(lemma)
    if subclass == "adj-1-2" or bare.endswith("ος"):
        hinted = LONG_STEMS.get(lemma, lemma)
        stem = hinted[:-2]
        # -ώτερος after a short open penult (σοφ-ός → σοφώτερος); -ότερος when
        # the penult vowel is long or followed by two consonants (δικαιότερος,
        # μακρότερος).
        m = re.search(r"([αεηιουω][\u0300-\u036f]*)([^αεηιουω\u0300-\u036f]*)$", nfd(stem))
        trailing = m.group(2) if m else ""
        penult = syllables(strip_accent(stem))[-1]
        closed = len(trailing) >= 2 or syllable_is_long(penult)
        link = "ο" if closed else "ω"
        return {
            "comparative": [finish(recessive(strip_accent(stem) + link + "τερος"))],
            "superlative": [finish(recessive(strip_accent(stem) + link + "τατος"))],
            "regular": True,
        }
    if subclass == "adj-3-es":
        stem = strip_accent(lemma[:-2])
        return {"comparative": [finish(recessive(stem + "εστερος"))], "superlative": [finish(recessive(stem + "εστατος"))], "regular": True}
    if subclass == "adj-us":
        stem = strip_accent(lemma[:-2])
        return {"comparative": [finish(recessive(stem + "υτερος"))], "superlative": [finish(recessive(stem + "υτατος"))], "regular": True}
    return None


def _adverb(lemma: str, subclass: str, hinted: str, idx: int) -> list[str]:
    if lemma == "ἀγαθός":
        return ["εὖ"]
    if lemma in tables.ADVERB_OVERRIDE:
        return tables.ADVERB_OVERRIDE[lemma]
    if lemma in tables.SUPERLATIVE_ADVERB:
        return tables.SUPERLATIVE_ADVERB[lemma]
    if lemma in tables.NO_COMPARISON and subclass != "adj-1-2":
        return []
    if subclass in {"adj-1-2", "numeral"} or strip_accent(lemma).endswith("ος"):
        if lemma in {"αὐτός", "ἄλλος", "ἕκαστος", "ἑκάτερος", "ἐμός", "σός", "ὑμέτερος", "ἡμέτερος", "μυρίος", "ὅσος", "οἷος", "ποῖος", "πότερος", "τοιοῦτος", "τοσοῦτος", "τοιόσδε"}:
            return []
        return [finish(persistent(hinted[:-2] + "ως", idx, "circumflex"))]
    if subclass == "adj-3-es":
        return [finish(strip_accent(lemma[:-2]) + "ῶς")]
    if subclass == "adj-us":
        return [finish(strip_accent(lemma[:-2]) + "έως")]
    if subclass == "adj-3-on":
        return [finish(recessive(strip_accent(lemma[:-2]) + "ον"))]
    return []


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def decline(lemma: str, kind: str, subclass: str, morph: dict) -> dict | None:
    """Full paradigm for a lexicon entry, or None for indeclinable words."""
    if kind == "article":
        return {**tables.ARTICLE, "lemma": lemma}
    if lemma in tables.PRONOUNS:
        return {**tables.PRONOUNS[lemma], "lemma": lemma}
    if lemma in tables.NOUNS:
        return {**tables.NOUNS[lemma], "lemma": lemma}
    if lemma in tables.ADJECTIVES:
        out = {**tables.ADJECTIVES[lemma], "lemma": lemma}
        out.setdefault("comparison", _comparison(lemma, subclass))
        return out
    if kind == "noun":
        return _lemma_nominative(decline_noun(lemma, morph["genitive"], morph["gender"], subclass), lemma)
    if kind in {"adjective", "numeral"} and "terminations" in morph:
        return decline_adjective(lemma, morph, subclass if subclass.startswith("adj") else "adj-1-2")
    if kind == "pronoun" and len(morph.get("forms", [])) == 3 and strip_accent(lemma).endswith("ος"):
        m = {"terminations": 3, "feminine": morph["forms"][1], "neuter": morph["forms"][2]}
        return decline_adjective(lemma, m, "adj-1-2", kind="pronoun")
    return None


def decline_entry(entry: dict) -> dict | None:
    return decline(entry["lemma"], entry["kind"], entry["subclass"], entry.get("morph", {}))
