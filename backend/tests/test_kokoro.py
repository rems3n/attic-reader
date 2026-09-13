import io
import wave

import pytest

from app.tts.kokoro import (
    KokoroAtticTTS,
    has_speech,
    prepare_kokoro_phonemes,
    split_phonemes,
)


def test_prepare_preserves_attic_symbols():
    source = "ˈantʰrɔːpos bˈios tʰeˈos ai̯ oi̯ au̯ eu̯ ŋkʰ y"
    out = prepare_kokoro_phonemes(source)
    assert "tʰ" in out
    assert "ɔː" in out
    assert "ŋkʰ" in out
    assert "y" in out
    assert "̯" not in out
    assert "ai" in out


def test_split_phonemes_one_chunk_per_sentence():
    ipa = "ho dikaiˈopolis autuːrˈgos ˈestin. ti poiˈeː? en toi̯s agroi̯s oiˈkeː!"
    chunks = split_phonemes(ipa)
    assert chunks == [
        "ho dikaiˈopolis autuːrˈɡos ˈestin.",
        "ti poiˈeː?",
        "en tois aɡrois oiˈkeː!",
    ]


def test_split_phonemes_does_not_merge_short_sentences():
    chunks = split_phonemes("a. b. c.", max_chars=450)
    assert chunks == ["a.", "b.", "c."]


def test_split_phonemes_breaks_long_sentence_at_clauses_then_words():
    sentence = ", ".join(["ˈantʰrɔːpos ˈestin"] * 12) + "."
    chunks = split_phonemes(sentence, max_chars=60)
    assert len(chunks) > 1
    assert all(len(chunk) <= 60 for chunk in chunks)
    assert " ".join(chunks).replace("  ", " ") == prepare_kokoro_phonemes(sentence)
    # A clause boundary is preferred over a mid-clause word split.
    assert all(chunk.endswith((",", ".")) for chunk in chunks)


def test_split_phonemes_respects_limit_without_punctuation():
    text = ("ˈantʰrɔːpos esti " * 100).strip()
    chunks = split_phonemes(text, max_chars=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_prepare_maps_ascii_g_to_ipa_g():
    # ASCII g is not a Kokoro token; IPA ɡ (U+0261) is.
    assert prepare_kokoro_phonemes("ˈgenos") == "ˈɡenos"


def test_has_speech_ignores_punctuation_only_chunks():
    assert has_speech("ˈɛːli.os")
    assert not has_speech("...")
    assert not has_speech("— ?")


def test_benchmark_phonemes_have_no_unknown_symbols():
    import json
    from pathlib import Path
    from app.greek import attic_ipa
    from app.tts.kokoro import unknown_kokoro_symbols
    rows = json.loads(Path("../benchmarks/attic_benchmark.json").read_text("utf-8"))
    for row in rows:
        assert unknown_kokoro_symbols(prepare_kokoro_phonemes(attic_ipa(row["text"]))) == []


def _wav_seconds(data: bytes) -> float:
    with wave.open(io.BytesIO(data), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def test_synthesize_passes_speed_multiplier_to_kokoro(fake_kokoro):
    tts = KokoroAtticTTS()
    tts.synthesize("ho ˈɛːlios. hɛː kʰˈɔːra.", speed=0.75)
    assert [c["phonemes"] for c in fake_kokoro.calls] == ["ho ˈɛːlios.", "hɛː kʰˈɔːra."]
    assert all(c["voice"] == "im_nicola" for c in fake_kokoro.calls)
    assert all(c["speed"] == pytest.approx(0.92 * 0.75) for c in fake_kokoro.calls)


def test_synthesize_default_speed_is_base_pace(fake_kokoro):
    KokoroAtticTTS().synthesize("ho ˈɛːlios.")
    assert fake_kokoro.calls[0]["speed"] == pytest.approx(0.92)


def test_synthesize_many_returns_one_clip_per_sentence_and_none_for_silence(fake_kokoro):
    clips = KokoroAtticTTS().synthesize_many(["ho ˈɛːlios.", "...", "hɛː kʰˈɔːra."], speed=1.0)
    assert len(clips) == 3
    assert clips[1] is None
    assert clips[0] is not None and clips[2] is not None
    assert clips[0][:4] == b"RIFF"
    # 11 chars * 10 ms
    assert _wav_seconds(clips[0]) == pytest.approx(0.11, abs=0.01)
    assert len(fake_kokoro.calls) == 2


def test_synthesize_inserts_pause_between_sentences(fake_kokoro):
    audio = KokoroAtticTTS().synthesize("ho ˈɛːlios. hɛː kʰˈɔːra.")
    # 11 chars + 12 chars at 10 ms each plus a 100 ms pause.
    assert _wav_seconds(audio) == pytest.approx(0.11 + 0.12 + 0.10, abs=0.01)
