from app.tts.mms import prepare_mms_grc_text


def test_mms_preserves_polytonic_greek():
    assert prepare_mms_grc_text("Ἐπεὶ δὲ ὁ Κῦρος.") == "ἐπεὶ δὲ ὁ κῦρος"


def test_mms_removes_english_and_normalizes_punctuation():
    assert prepare_mms_grc_text("λόγος, TEST · θεός;") == "λόγος θεός"


def test_mms_preserves_apostrophe_and_hyphen():
    assert prepare_mms_grc_text("ἀλλ’ ἐγώ—οὐ") == "ἀλλ' ἐγώ–οὐ"


def test_split_greek_prefers_sentence_boundaries():
    from app.tts.mms import split_greek_for_tts

    text = "ὁ μὲν Δικαιόπολις αὐτουργός ἐστιν. ἐν τοῖς ἀγροῖς οἰκεῖ. τί ποιεῖ;"
    assert split_greek_for_tts(text) == [
        "ὁ μὲν Δικαιόπολις αὐτουργός ἐστιν.",
        "ἐν τοῖς ἀγροῖς οἰκεῖ.",
        "τί ποιεῖ;",
    ]


def test_split_greek_respects_max_chars_without_breaking_words():
    from app.tts.mms import split_greek_for_tts

    chunks = split_greek_for_tts("λόγος " * 20, max_chars=30)
    assert len(chunks) > 1
    assert all(len(chunk) <= 30 for chunk in chunks)
    assert all(" " in chunk or chunk == "λόγος" for chunk in chunks)
