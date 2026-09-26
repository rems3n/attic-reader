"""Full declension of participles from their four principal forms.

The verb tables give each participle as masculine, feminine and neuter
nominative singular plus the masculine genitive singular (λύων, λύουσα,
λῦον, λύοντος). That is enough to decline it in every case, number and
gender:

- ``-μενος, -μένη, -μενον`` participles are first/second-declension
  adjectives (λυόμενος, λυομένου …; feminine genitive plural λυομένων).
- every other participle is third declension in the masculine and neuter
  (stem = genitive minus -ος: λυοντ-, λυσαντ-, λελυκοτ-, λυθεντ-) and first
  declension with short -α in the feminine (λύουσα, λυούσης, … λυουσῶν).

The accent is persistent: it stays on the syllable it has in the masculine
genitive singular (the feminine keeps the syllable of its own nominative),
moving only as the law of limitation requires; the feminine genitive plural
is always -ῶν. The dative plural loses the -ντ-/-τ- before -σι with
compensatory lengthening: -οντ- → -ουσι, -αντ- → -ᾱσι, -εντ- → -εισι,
-υντ- → -ῡσι, -ωντ- → -ωσι, perfect -οτ- → -οσι.
"""

from __future__ import annotations

import unicodedata

from .accent import accent_from_start, accent_position, accentuate, finish, nfc, nfd, persistent, strip_accent

CASES = ("nom", "gen", "dat", "acc", "voc")
MACRON = "̄"
BREATHINGS = {"̓", "̔"}


def _with_macron(text: str) -> str:
    """Put a macron on the last vowel of `text` (α → ᾱ, υ → ῡ)."""
    chars = list(nfd(text))
    for i in range(len(chars) - 1, -1, -1):
        if chars[i] in "αιυ":
            chars.insert(i + 1, MACRON)
            break
    return nfc("".join(chars))


def _dative_plural_base(stem: str) -> str:
    """λυοντ → λυου, λυσαντ → λυσᾱ, λυθεντ → λυθει, δεικνυντ → δεικνῡ,
    τιμωντ → τιμω, ποιουντ → ποιου, λελυκοτ → λελυκο, ὀντ → οὐ."""
    d = nfd(stem)
    if d.endswith("ντ"):
        base = d[:-2]
        # split trailing combining marks (a breathing on an initial vowel: ὀντ-)
        marks = ""
        while base and unicodedata.combining(base[-1]):
            marks = base[-1] + marks
            base = base[:-1]
        if not base:
            return nfc(stem)
        v = base[-1]
        before = base[:-1]
        if v == "ο":
            # a breathing on this ο moves to the υ of the new diphthong (ὀντ- → οὐ-)
            return nfc(before + "ο" + "υ" + marks)
        if v == "υ" and before.endswith("ο"):
            return nfc(base + marks)  # ποιουντ- → ποιου-
        if v == "α":
            return nfc(before + "α" + marks + MACRON)
        if v == "ε":
            return nfc(before + "ε" + "ι" + marks)
        if v == "υ":
            return nfc(before + "υ" + marks + MACRON)
        return nfc(base + marks)  # -ωντ- (τιμῶσι), -ηντ-
    if d.endswith("τ"):
        return nfc(d[:-1])  # perfect -οτ-
    return nfc(stem)


def _nu(form: str) -> str:
    return form + "(ν)" if form.endswith("σι") else form


def _third(m: str, n: str, mg: str) -> dict[tuple[str, str], list[str]]:
    stem = strip_accent(mg)[:-2]
    idx = accent_from_start(mg)
    p = lambda ending: finish(persistent(stem + ending, idx))  # noqa: E731
    dat_pl = _nu(finish(persistent(_dative_plural_base(stem) + "σι", idx)))
    m_sg = [m, mg, p("ι"), p("α"), m]
    n_sg = [n, mg, m_sg[2], n, n]
    m_pl = [p("ες"), p("ων"), dat_pl, p("ας"), p("ες")]
    n_pl = [p("α"), m_pl[1], dat_pl, p("α"), p("α")]
    return {("m", "sg"): m_sg, ("n", "sg"): n_sg, ("m", "pl"): m_pl, ("n", "pl"): n_pl}


def _feminine_short_alpha(f: str) -> dict[tuple[str, str], list[str]]:
    bare = strip_accent(f)
    stem = bare[:-1]
    idx = accent_from_start(f)
    plain = strip_accent(stem)
    after_iota = plain.endswith("ι")
    ends_in_diphthong = plain[-2:] in {"αι", "ει", "οι", "υι", "αυ", "ευ", "ου"}
    if accent_position(f) == (2, "circumflex") and not ends_in_diphthong:
        stem = _with_macron(stem)  # στᾶσα, δεικνῦσα: the vowel is long (στᾶσαν, στᾶσαι)
    p = lambda ending: finish(persistent(stem + ending, idx))  # noqa: E731
    if after_iota:
        sg = [f, p("ᾱς"), p("ᾳ"), p("αν"), f]
    else:
        sg = [f, p("ης"), p("ῃ"), p("αν"), f]
    gen_pl = finish(accentuate(stem + "ων", 1, "circumflex"))
    pl = [p("αι"), gen_pl, p("αις"), p("ᾱς"), p("αι")]
    return {("f", "sg"): sg, ("f", "pl"): pl}


def _second(m: str, f: str) -> dict[tuple[str, str], list[str]] | None:
    """-μενος participles (and any other -ος/-η/-ον ones) as adjectives."""
    from .nominal import decline_adjective

    try:
        table = decline_adjective(m, {"terminations": 3, "feminine": f}, "adj-1-2")
    except Exception:  # noqa: BLE001
        return None
    rows: dict[tuple[str, str], list[str]] = {}
    for cell in table["cells"]:
        for g, forms in cell["forms"].items():
            rows.setdefault((g, cell["number"]), []).append(forms[0] if forms else "")
    return rows


def decline_participle(m: str, f: str, n: str, mg: str) -> dict[tuple[str, str], list[str]] | None:
    """{(gender, number): [nom, gen, dat, acc, voc]} for a participle given
    its masculine, feminine and neuter nominative singular and masculine
    genitive singular; None when the forms do not fit either pattern."""
    if not (m and f and n and mg):
        return None
    if strip_accent(m).endswith("ος"):
        return _second(m, f)
    if not strip_accent(mg).endswith("ος") or not strip_accent(f).endswith("α"):
        return None
    rows = _third(m, n, mg)
    rows.update(_feminine_short_alpha(f))
    return rows


def participle_cells(m: str, f: str, n: str, mg: str) -> list[tuple[str, str, str, str]]:
    """[(case, number, gender, form)] for every cell of the participle."""
    rows = decline_participle(m, f, n, mg)
    if not rows:
        return []
    out = []
    for (g, number), forms in rows.items():
        for case, form in zip(CASES, forms):
            if form:
                out.append((case, number, g, form))
    return out
