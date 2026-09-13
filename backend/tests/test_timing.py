import json

import pytest
from fastapi.testclient import TestClient

from app.greek import attic_ipa
from app.main import app
from app.tts.kokoro import KokoroAtticTTS, prepare_kokoro_phonemes
from app.tts.timing import align_words, char_boundaries, token_spans


def test_char_boundaries_with_bos_eos_and_uniform_durations():
    ph = "ab cd"
    bounds = char_boundaries(ph, [2] + [1] * 5 + [2], n_samples=9 * 2400)  # 9 frames -> 0.9 s
    assert bounds == pytest.approx([0.2, 0.3, 0.4, 0.5, 0.6, 0.7])


def test_char_boundaries_rejects_mismatched_lengths():
    assert char_boundaries("abc", [1, 1], 2400) is None
    assert char_boundaries("abc", [1, 1, 1, 1, 1, 1], 2400) is None


def test_token_spans_skip_punctuation_only_tokens():
    assert token_spans("ho ˈɛːlios — ˈestin.") == [(0, 2), (3, 10), (13, 20)]


def test_align_words_maps_greek_words_to_phoneme_tokens():
    sentence = "ὁ ἥλιος ἐστίν."
    ph = prepare_kokoro_phonemes(attic_ipa(sentence))
    pred = [0] + [1] * len(ph) + [0]
    n_samples = len(ph) * 240  # 10 ms per char
    words = align_words(sentence, [(ph, pred, n_samples)])
    assert words is not None and len(words) == 3
    assert [sentence[w.start : w.end] for w in words] == ["ὁ", "ἥλιος", "ἐστίν"]
    assert words[0].t0 == 0.0 and words[0].t1 == pytest.approx(0.02)  # "ho" = 2 chars
    assert words[1].t0 == pytest.approx(0.03)
    assert words[-1].t1 == pytest.approx(len(ph) * 0.01 - 0.01, abs=0.011)  # trailing "." excluded
    assert all(words[i].t1 <= words[i + 1].t0 + 1e-9 for i in range(len(words) - 1))


def test_align_words_spans_chunks_with_pause_offset():
    sentence = "ἀρχή, τέλος."
    ph1, ph2 = "arkʰˈɛː,", "tˈelos."
    words = align_words(sentence, [(ph1, [0] + [1] * len(ph1) + [0], len(ph1) * 240), (ph2, [0] + [1] * len(ph2) + [0], len(ph2) * 240)], pause_samples=2400)
    assert words is not None
    assert words[1].t0 == pytest.approx(len(ph1) * 0.01 + 0.1)


def test_align_words_returns_none_when_counts_disagree_or_durations_missing():
    assert align_words("ὁ ἥλιος", [("ho", [0, 1, 1, 0], 480)]) is None
    assert align_words("ὁ", [("ho", None, 480)]) is None


def test_stream_clip_events_carry_word_timings(fake_kokoro):
    text = "ὁ Δικαιόπολις αὐτουργός ἐστιν. τί ποιεῖ;"
    with TestClient(app).stream("POST", "/api/synthesize/stream", json={"text": text}) as response:
        events = [json.loads(line) for line in "".join(response.iter_text()).splitlines() if line.strip()]
    clips = [e for e in events if e["type"] == "clip"]
    sentences = [s["text"] for s in events[0]["sentences"]]
    assert len(clips) == 2
    # Word offsets index into the sentence text, not the whole input.
    first = clips[0]["words"]
    assert [sentences[0][w["start"] : w["end"]] for w in first] == ["ὁ", "Δικαιόπολις", "αὐτουργός", "ἐστιν"]
    assert first[0]["t0"] == 0.0
    assert all(first[i]["t1"] <= first[i + 1]["t0"] for i in range(3))
    assert first[-1]["t1"] <= clips[0]["duration_seconds"] + 1e-6
    second = clips[1]["words"]
    assert [sentences[1][w["start"] : w["end"]] for w in second] == ["τί", "ποιεῖ"]


def test_cached_clips_keep_their_timings(fake_kokoro):
    tts = KokoroAtticTTS()
    first = list(tts.iter_synthesize_timed(["ho ˈɛːlios."], ["ὁ ἥλιος."], speed=0.75))
    second = list(tts.iter_synthesize_timed(["ho ˈɛːlios."], ["ὁ ἥλιος."], speed=0.75))
    assert len(fake_kokoro.calls) == 1
    assert first[0][1] == second[0][1] and second[0][1] is not None
