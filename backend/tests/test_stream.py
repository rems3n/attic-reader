import base64
import json

from fastapi.testclient import TestClient

from app.main import app
from app.tts.kokoro import KokoroAtticTTS

TEXT = "ὁ Δικαιόπολις αὐτουργός ἐστιν. 12. τί ποιεῖ;"


def _lines(response):
    return [json.loads(line) for line in response.text.splitlines() if line.strip()]


def test_stream_emits_start_then_one_clip_per_sentence_then_done(fake_kokoro):
    with TestClient(app).stream("POST", "/api/synthesize/stream", json={"text": TEXT, "speed": 0.75}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/x-ndjson")
        body = "".join(response.iter_text())
    events = [json.loads(line) for line in body.splitlines() if line.strip()]
    assert [e["type"] for e in events] == ["start", "clip", "clip", "clip", "done"]
    start = events[0]
    assert start["provider"] == "kokoro-attic"
    assert [s["text"] for s in start["sentences"]] == ["ὁ Δικαιόπολις αὐτουργός ἐστιν.", "12.", "τί ποιεῖ;"]
    assert all("ipa" in s for s in start["sentences"])
    clips = events[1:4]
    assert [c["index"] for c in clips] == [0, 1, 2]
    assert base64.b64decode(clips[0]["audio_base64"])[:4] == b"RIFF"
    assert clips[1]["audio_base64"] is None and clips[1]["duration_seconds"] is None
    assert clips[2]["duration_seconds"] > 0
    assert events[-1]["elapsed_seconds"] >= 0
    assert all(c["speed"] == 0.92 * 0.75 for c in fake_kokoro.calls)


def test_stream_reports_error_line_without_kokoro(monkeypatch):
    monkeypatch.setenv("ENABLE_KOKORO", "false")
    monkeypatch.setenv("ALLOW_ESPEAK_FALLBACK", "false")
    monkeypatch.delenv("PIPER_MODEL", raising=False)
    response = TestClient(app).post("/api/synthesize/stream", json={"text": "χαῖρε."})
    events = _lines(response)
    assert events[-1]["type"] == "error"
    assert "eSpeak is intentionally disabled" in events[-1]["detail"]


def test_warm_up_loads_pipeline_and_reports_ready(fake_kokoro, monkeypatch):
    monkeypatch.setattr(KokoroAtticTTS, "_warm_state", "cold")
    tts = KokoroAtticTTS()
    tts.warm_up()
    assert KokoroAtticTTS.warm_state() == "ready"
    assert fake_kokoro.calls and fake_kokoro.calls[0]["phonemes"] == "ˈɛːlios."


def test_status_reports_model_warm_state(fake_kokoro, monkeypatch):
    monkeypatch.setattr(KokoroAtticTTS, "_warm_state", "ready")
    body = TestClient(app).get("/api/tts/status").json()
    kokoro = next(p for p in body["providers"] if p["id"] == "kokoro-attic")
    assert "model ready" in kokoro["note"]
