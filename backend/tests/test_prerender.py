import threading
import time

import pytest

from app.library import load_manifest
from app.tts import clip_cache, prerender
from app.tts.kokoro import KokoroAtticTTS


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("CLIP_CACHE_DIR", str(tmp_path / "clips"))


def test_prerender_renders_every_library_chunk_at_every_speed(fake_kokoro):
    tts = KokoroAtticTTS()
    library_jobs = prerender.plan(tts)
    assert len(library_jobs) > 0
    # The job also renders the vocabulary headwords; a headword may share a
    # cache key with another (or with a library chunk), so count distinct keys.
    jobs = library_jobs + prerender.vocab_plan(tts)
    distinct = len({j[1] for j in jobs})
    result = prerender.run(tts)
    assert result["state"] == "done"
    assert result["rendered"] == len(jobs)
    assert clip_cache.stats()["clips"] == distinct
    for item in load_manifest():
        assert prerender.ready_speeds(item, tts) == sorted(prerender.SPEEDS)
    # Second run finds everything cached.
    again = prerender.run(tts)
    assert again["rendered"] == 0 and again["cached"] == len(jobs)


def test_prerender_yields_to_user_requests(fake_kokoro, monkeypatch):
    tts = KokoroAtticTTS()
    # Slow fake model so the job is mid-flight when the user arrives.
    original = fake_kokoro.generate_from_tokens

    def slow(*args, **kwargs):
        time.sleep(0.01)
        yield from original(*args, **kwargs)

    monkeypatch.setattr(fake_kokoro, "generate_from_tokens", slow)
    thread = prerender.run_in_background(tts)
    time.sleep(0.05)
    started = time.perf_counter()
    clips = list(tts.iter_synthesize(["ho ˈɛːlios."], speed=0.75))
    waited = time.perf_counter() - started
    assert clips[0][:4] == b"RIFF"
    assert waited < 1.0  # not blocked behind the whole pre-render run
    thread.join(timeout=30)
    assert prerender.status()["state"] == "done"


def test_status_endpoint_exposes_prerender_progress(fake_kokoro):
    from fastapi.testclient import TestClient
    from app.main import app

    body = TestClient(app).get("/api/tts/status").json()
    assert set(body["library_prerender"]) >= {"state", "rendered", "total"}
