from app.greek.segment import segment_sentences


def _spans_match(text, sentences):
    return all(text[s.start : s.end] == s.text for s in sentences)


def test_splits_on_period_and_greek_question_mark():
    text = "ὁ Δικαιόπολις αὐτουργός ἐστιν. τί ποιεῖ; ἐν τοῖς ἀγροῖς οἰκεῖ."
    out = segment_sentences(text)
    assert [s.text for s in out] == [
        "ὁ Δικαιόπολις αὐτουργός ἐστιν.",
        "τί ποιεῖ;",
        "ἐν τοῖς ἀγροῖς οἰκεῖ.",
    ]
    assert [s.index for s in out] == [0, 1, 2]
    assert _spans_match(text, out)


def test_splits_on_ano_teleia_exclamation_and_unicode_question_mark():
    text = "χαῖρε· τί λέγεις; ἰού! καλῶς?"
    out = segment_sentences(text)
    assert [s.text for s in out] == ["χαῖρε·", "τί λέγεις;", "ἰού!", "καλῶς?"]
    assert _spans_match(text, out)


def test_newlines_are_boundaries_and_trailing_fragment_kept():
    text = "πρώτη γραμμή\nδευτέρα γραμμή.\n\nτρίτη χωρὶς στιγμήν"
    out = segment_sentences(text)
    assert [s.text for s in out] == ["πρώτη γραμμή", "δευτέρα γραμμή.", "τρίτη χωρὶς στιγμήν"]
    assert _spans_match(text, out)


def test_ellipsis_and_closing_quote_stay_with_sentence():
    text = "εἶπεν “οὐκ οἶδα…”. καὶ ἀπῆλθεν..."
    out = segment_sentences(text)
    assert [s.text for s in out] == ["εἶπεν “οὐκ οἶδα…”.", "καὶ ἀπῆλθεν..."]
    assert _spans_match(text, out)


def test_whitespace_only_and_empty_input():
    assert segment_sentences("") == []
    assert segment_sentences("  \n \n ") == []


def test_spans_are_exact_with_irregular_whitespace():
    text = "   ἀρχή.   τέλος;  "
    out = segment_sentences(text)
    assert [(s.start, s.end) for s in out] == [(3, 8), (11, 17)]
    assert _spans_match(text, out)


def test_segment_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post("/api/segment", json={"text": "ἀρχή. τέλος;"})
    assert response.status_code == 200
    body = response.json()
    assert body["sentences"] == [
        {"index": 0, "text": "ἀρχή.", "start": 0, "end": 5},
        {"index": 1, "text": "τέλος;", "start": 6, "end": 12},
    ]
