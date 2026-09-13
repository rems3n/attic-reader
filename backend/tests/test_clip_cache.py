import pytest

from app.tts import clip_cache
from app.tts.kokoro import KokoroAtticTTS


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("CLIP_CACHE_DIR", str(tmp_path / "clips"))
    yield tmp_path / "clips"


def test_put_get_round_trip_and_stats(isolated_cache):
    key = clip_cache.clip_key("kokoro-attic", "im_nicola", 0.6375, "ˈɛːlios.")
    assert clip_cache.get(key) is None and not clip_cache.has(key)
    clip_cache.put(key, b"RIFF....")
    assert clip_cache.get(key) == b"RIFF...."
    assert clip_cache.has(key)
    assert clip_cache.stats()["clips"] == 1


def test_key_depends_on_speed_voice_and_phonemes():
    base = clip_cache.clip_key("kokoro-attic", "im_nicola", 0.85, "a.")
    assert base != clip_cache.clip_key("kokoro-attic", "im_nicola", 0.6375, "a.")
    assert base != clip_cache.clip_key("kokoro-attic", "bm_george", 0.85, "a.")
    assert base != clip_cache.clip_key("kokoro-attic", "im_nicola", 0.85, "b.")


def test_iter_synthesize_renders_once_then_serves_from_cache(fake_kokoro):
    tts = KokoroAtticTTS()
    first = list(tts.iter_synthesize(["ho ˈɛːlios.", "hɛː kʰˈɔːra."], speed=0.75))
    assert len(fake_kokoro.calls) == 2
    second = list(tts.iter_synthesize(["ho ˈɛːlios.", "hɛː kʰˈɔːra."], speed=0.75))
    assert len(fake_kokoro.calls) == 2  # no new model calls
    assert first == second
    # A different speed is a different clip.
    list(tts.iter_synthesize(["ho ˈɛːlios."], speed=1.0))
    assert len(fake_kokoro.calls) == 3


def test_cache_directory_defaults_next_to_hf_home(monkeypatch, tmp_path):
    monkeypatch.delenv("CLIP_CACHE_DIR", raising=False)
    monkeypatch.setenv("HF_HOME", str(tmp_path / "data" / "hf-cache"))
    assert clip_cache.cache_dir() == tmp_path / "data" / "clip-cache"
