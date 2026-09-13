from app.greek.g2p import attic_ipa
from app.greek.normalize import normalize_polytonic


def test_normalization_keeps_polytonic_marks():
    assert normalize_polytonic("  ἄνθρωπος  ") == "ἄνθρωπος"


def test_basic_consonants_are_not_modern_greek():
    ipa = attic_ipa("βίος δῶρον")
    assert ipa.startswith("b")
    assert "d" in ipa
    assert "v" not in ipa
    assert "ð" not in ipa


def test_rough_breathing_adds_h():
    assert attic_ipa("ἥλιος").startswith("h")


def test_aspirated_stops():
    ipa = attic_ipa("θεός φίλος χείρ")
    assert "tʰ" in ipa
    assert "pʰ" in ipa
    assert "kʰ" in ipa


def test_gamma_before_velar_is_nasal():
    assert attic_ipa("ἄγγελος").startswith("ˈaŋ")


def test_diphthong_not_modern_monophthong():
    assert "ai̯" in attic_ipa("παῖς")


def test_rough_breathing_on_second_vowel_of_initial_diphthong():
    # Polytonic orthography places the breathing on the second character.
    assert attic_ipa("αἱ") == "hai̯"
