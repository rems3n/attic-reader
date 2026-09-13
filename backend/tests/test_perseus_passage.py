"""Real text: Xenophon, Anabasis 1.1.1-4 (Perseus Digital Library, perseus-grc2).

Guards the whole learner pipeline on an actual edition rather than hand-typed
phrases: segmentation spans, Classical (non-Modern) phonology, Kokoro vocab
coverage, and one clip per sentence.
"""

import base64
from pathlib import Path

from fastapi.testclient import TestClient

from app.greek import attic_ipa, normalize_polytonic, segment_sentences
from app.main import app
from app.tts.kokoro import prepare_kokoro_phonemes, unknown_kokoro_symbols

PASSAGE = (Path(__file__).parents[2] / "samples" / "xenophon_anabasis_1.1.1-4.txt").read_text("utf-8")


def test_passage_segments_into_ten_sentences_with_exact_spans():
    sentences = segment_sentences(PASSAGE)
    assert len(sentences) == 10
    assert all(PASSAGE[s.start : s.end] == s.text for s in sentences)
    assert all(s.text[-1] in ".·" for s in sentences)
    assert sentences[0].text.startswith("Δαρείου καὶ Παρυσάτιδος")
    assert sentences[-1].text.endswith("Ἀρταξέρξην.")


def test_passage_phonology_is_classical_not_modern():
    ipa = attic_ipa(normalize_polytonic(PASSAGE))
    for modern in ("v", "ð", "ɣ", "f", "x", "θ"):
        assert modern not in ipa, f"Modern Greek value {modern!r} leaked into {ipa[:80]}..."
    assert "tʰ" in ipa and "pʰ" in ipa and "kʰ" in ipa
    assert "hɛː" in ipa or "ˈhɛː" in ipa  # ἡ / ἧς with rough breathing
    assert "y" in ipa  # Κῦρος
    assert "zd" in ipa  # Ξενίαν? no; ἁθροίζονται has ζ
    # Elision marks never reach the phoneme string.
    assert "ʼ" not in ipa and "'" not in ipa


def test_passage_is_fully_representable_in_kokoro_vocab():
    ipa = attic_ipa(normalize_polytonic(PASSAGE))
    assert unknown_kokoro_symbols(prepare_kokoro_phonemes(ipa)) == []


def test_passage_batch_yields_one_clip_per_sentence(fake_kokoro):
    response = TestClient(app).post("/api/synthesize/batch", json={"text": PASSAGE, "speed": 0.75})
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "kokoro-attic"
    assert len(body["sentences"]) == 10
    assert all(s["audio_base64"] for s in body["sentences"])
    assert all(base64.b64decode(s["audio_base64"])[:4] == b"RIFF" for s in body["sentences"])
    # Ten sentences, none long enough to need clause splitting -> ten Kokoro calls.
    assert len(fake_kokoro.calls) == 10
