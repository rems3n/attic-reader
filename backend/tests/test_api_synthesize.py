import base64

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TEXT = "ὁ Δικαιόπολις αὐτουργός ἐστιν. τί ποιεῖ; ἐν τοῖς ἀγροῖς οἰκεῖ."


def test_synthesize_accepts_speed_and_reports_provider(fake_kokoro):
    response = client.post("/api/synthesize", json={"text": TEXT, "speed": 0.6})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert response.headers["x-tts-provider"] == "kokoro-attic"
    assert response.content[:4] == b"RIFF"
    assert len(fake_kokoro.calls) == 3  # one Kokoro call per sentence
    assert all(c["speed"] == pytest.approx(0.92 * 0.6) for c in fake_kokoro.calls)


def test_synthesize_rejects_out_of_range_speed(fake_kokoro):
    assert client.post("/api/synthesize", json={"text": TEXT, "speed": 3}).status_code == 422
    assert client.post("/api/synthesize", json={"text": TEXT, "speed": 0.1}).status_code == 422


def test_batch_returns_one_clip_per_sentence(fake_kokoro):
    response = client.post("/api/synthesize/batch", json={"text": "  " + TEXT + "  ", "speed": 1.25})
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "kokoro-attic"
    assert body["speed"] == 1.25
    assert body["normalized_text"] == TEXT
    sentences = body["sentences"]
    assert [s["text"] for s in sentences] == [
        "ὁ Δικαιόπολις αὐτουργός ἐστιν.",
        "τί ποιεῖ;",
        "ἐν τοῖς ἀγροῖς οἰκεῖ.",
    ]
    for s in sentences:
        assert body["normalized_text"][s["start"] : s["end"]] == s["text"]
        assert s["mime_type"] == "audio/wav"
        assert s["duration_seconds"] and s["duration_seconds"] > 0
        assert base64.b64decode(s["audio_base64"])[:4] == b"RIFF"
        assert s["ipa"]
    assert sentences[1]["ipa"].endswith("?")  # Greek ; is a question mark
    assert all(c["speed"] == pytest.approx(0.92 * 1.25) for c in fake_kokoro.calls)


def test_batch_marks_unpronounceable_sentence_as_silent(fake_kokoro):
    response = client.post("/api/synthesize/batch", json={"text": "χαῖρε. 12. καλῶς."})
    assert response.status_code == 200
    sentences = response.json()["sentences"]
    assert [s["audio_base64"] is None for s in sentences] == [False, True, False]
    assert sentences[1]["duration_seconds"] is None


def test_batch_without_kokoro_fails_loudly_not_with_espeak(monkeypatch):
    monkeypatch.setenv("ENABLE_KOKORO", "false")
    monkeypatch.setenv("ALLOW_ESPEAK_FALLBACK", "false")
    monkeypatch.delenv("PIPER_MODEL", raising=False)
    response = client.post("/api/synthesize/batch", json={"text": "χαῖρε."})
    assert response.status_code == 503
    assert "eSpeak is intentionally disabled" in response.json()["detail"]
