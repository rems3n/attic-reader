"""/api/speak (single word audio) and the sync-code progress store."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.tts import prerender


def test_speak_returns_wav_and_caches(fake_kokoro):
    client = TestClient(app)
    r = client.post("/api/speak", json={"text": "λόγος", "speed": 0.75})
    assert r.status_code == 200 and r.headers["content-type"].startswith("audio/wav")
    assert r.content[:4] == b"RIFF"
    calls = len(fake_kokoro.calls)
    client.post("/api/speak", json={"text": "λόγος", "speed": 0.75})
    assert len(fake_kokoro.calls) == calls  # served from the clip cache
    assert client.post("/api/speak", json={"text": "x" * 400}).status_code == 422


def test_progress_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("PROGRESS_DIR", str(tmp_path))
    client = TestClient(app)
    assert client.get("/api/progress/my-secret-code").status_code == 404
    assert client.put("/api/progress/short", json={"a": 1}).status_code == 422
    doc = {"cards": {"λογος:recognition": {"ef": 2.5, "updated": 1}}}
    r = client.put("/api/progress/my-secret-code", json=doc)
    assert r.status_code == 200 and r.json()["bytes"] > 0
    back = client.get("/api/progress/my-secret-code").json()
    assert back["document"] == doc and back["saved_at"] > 0
    assert not any(p.name.startswith("my-secret") for p in tmp_path.iterdir())  # hashed on disk


def test_vocab_prerender_plan(fake_kokoro):
    from app.tts.kokoro import KokoroAtticTTS

    jobs = prerender.vocab_plan(KokoroAtticTTS())
    assert len(jobs) >= 500 and all(j[0] == 0.75 for j in jobs)
