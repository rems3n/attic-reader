from app.tts.kokoro import prepare_kokoro_phonemes, split_phonemes


def test_prepare_preserves_attic_symbols():
    source = "ˈantʰrɔːpos bˈios tʰeˈos ai̯ oi̯ au̯ eu̯ ŋkʰ y"
    out = prepare_kokoro_phonemes(source)
    assert "tʰ" in out
    assert "ɔː" in out
    assert "ŋkʰ" in out
    assert "y" in out
    assert "̯" not in out
    assert "ai" in out


def test_split_phonemes_respects_limit():
    text = ("ˈantʰrɔːpos esti. " * 100).strip()
    chunks = split_phonemes(text, max_chars=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_prepare_maps_ascii_g_to_ipa_g():
    # ASCII g is not a Kokoro token; IPA ɡ (U+0261) is.
    assert prepare_kokoro_phonemes("ˈgenos") == "ˈ\u0261enos"


def test_benchmark_phonemes_have_no_unknown_symbols():
    import json
    from pathlib import Path
    from app.greek import attic_ipa
    from app.tts.kokoro import unknown_kokoro_symbols
    rows = json.loads(Path("../benchmarks/attic_benchmark.json").read_text("utf-8"))
    for row in rows:
        assert unknown_kokoro_symbols(prepare_kokoro_phonemes(attic_ipa(row["text"]))) == []
