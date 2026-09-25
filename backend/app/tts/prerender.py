"""Background pre-rendering of the reading library into the clip cache.

Runs after the Kokoro warm-up. Renders every library sentence at every
learner speed, default speed first, so a passage chosen from the library
plays instantly. It never holds the model while a user request is waiting:
`KokoroAtticTTS` releases its render lock between sentences and this job
yields whenever `user_requests_pending()` is non-zero.
"""

from __future__ import annotations

import logging
import os
import threading
import time

from ..greek import attic_ipa
from ..library import load_manifest
from . import clip_cache
from .kokoro import KokoroAtticTTS, has_speech, prepare_kokoro_phonemes, split_phonemes

log = logging.getLogger("attic.tts.prerender")

# Learner multipliers offered by the UI; the default (0.75) is rendered first.
SPEEDS = (0.75, 0.5, 0.6, 1.0)

_state: dict[str, object] = {"state": "idle", "rendered": 0, "total": 0, "cached": 0, "started": None, "finished": None}
_lock = threading.Lock()


def status() -> dict[str, object]:
    with _lock:
        return dict(_state)


def _set(**kw: object) -> None:
    with _lock:
        _state.update(kw)


def plan(tts: KokoroAtticTTS) -> list[tuple[float, str, str]]:
    """(speed, cache_key, chunk_phonemes) for every library sentence chunk × speed."""
    jobs: list[tuple[float, str, str]] = []
    for speed in SPEEDS:
        model_speed = tts.effective_speed(speed)
        for item in load_manifest():
            for sentence in item["sentences"]:
                for chunk in split_phonemes(attic_ipa(sentence), max_chars=tts.max_chars):
                    if not has_speech(chunk):
                        continue
                    key = clip_cache.clip_key(tts.provider_id, tts.voice, model_speed, chunk)
                    jobs.append((speed, key, chunk))
    return jobs


def vocab_plan(tts: KokoroAtticTTS) -> list[tuple[float, str, str]]:
    """(speed, cache_key, chunk) for every vocabulary headword at the default
    speed, so flash cards play instantly."""
    from ..vocab import load_entries

    jobs: list[tuple[float, str, str]] = []
    speed = SPEEDS[0]
    model_speed = tts.effective_speed(speed)
    for entry in load_entries():
        for chunk in split_phonemes(attic_ipa(entry["lemma"]), max_chars=tts.max_chars):
            if has_speech(chunk):
                jobs.append((speed, clip_cache.clip_key(tts.provider_id, tts.voice, model_speed, chunk), chunk))
    return jobs


COURSE_SPEEDS = (0.75, 0.6)


def course_plan(tts: KokoroAtticTTS) -> list[tuple[float, str, str]]:
    """(speed, cache_key, chunk) for every course story sentence (two learner
    speeds), every lesson word and every exercise audio string (default speed)."""
    from ..course import data as course_data

    jobs: list[tuple[float, str, str]] = []
    seen: set[str] = set()

    def add(text: str, speed: float) -> None:
        model_speed = tts.effective_speed(speed)
        for chunk in split_phonemes(attic_ipa(text), max_chars=tts.max_chars):
            if not has_speech(chunk):
                continue
            key = clip_cache.clip_key(tts.provider_id, tts.voice, model_speed, chunk)
            if key not in seen:
                seen.add(key)
                jobs.append((speed, key, chunk))

    for lid in course_data.lesson_ids():
        if not course_data.lesson_available(lid):
            continue
        raw = course_data.load_lesson(lid)
        for para in raw.get("story", []):
            for sentence in para.get("sentences", []):
                for speed in COURSE_SPEEDS:
                    add(sentence["text"], speed)
        for sentence in raw.get("notice", []):
            add(sentence, COURSE_SPEEDS[0])
        for v in raw.get("vocab", []):
            try:
                add(course_data.entry_by_id(v["id"])["lemma"], COURSE_SPEEDS[0])
            except KeyError:
                continue
        for block in ("exercises", "questions", "quiz"):
            for item in raw.get(block, []):
                audio = item.get("audio")
                if audio and audio != "prompt":
                    add(audio, COURSE_SPEEDS[0])
                elif audio == "prompt" and item.get("prompt"):
                    add(item["prompt"], COURSE_SPEEDS[0])
                for option in item.get("options", []) or []:
                    if option.get("audio"):
                        add(option["audio"], COURSE_SPEEDS[0])
    return jobs


def ready_speeds(item: dict, tts: KokoroAtticTTS | None = None) -> list[float]:
    """Speeds at which every chunk of the item is already cached."""
    tts = tts or KokoroAtticTTS()
    out: list[float] = []
    for speed in SPEEDS:
        model_speed = tts.effective_speed(speed)
        complete = True
        for sentence in item["sentences"]:
            for chunk in split_phonemes(attic_ipa(sentence), max_chars=tts.max_chars):
                if has_speech(chunk) and not clip_cache.has(clip_cache.clip_key(tts.provider_id, tts.voice, model_speed, chunk)):
                    complete = False
                    break
            if not complete:
                break
        if complete:
            out.append(speed)
    return sorted(out)


def run(tts: KokoroAtticTTS | None = None) -> dict[str, object]:
    """Render every missing clip (blocking). Safe to call repeatedly."""
    tts = tts or KokoroAtticTTS()
    jobs = plan(tts) + vocab_plan(tts) + course_plan(tts)
    todo = [j for j in jobs if not clip_cache.has(j[1])]
    _set(state="running", rendered=0, total=len(todo), cached=len(jobs) - len(todo), started=time.time(), finished=None)
    log.warning("library pre-render: %d clips to render, %d already cached", len(todo), len(jobs) - len(todo))
    started = time.perf_counter()
    try:
        pipeline = tts._load()
        for index, (speed, key, chunk) in enumerate(todo):
            # Yield to learners: a user request takes the render lock as soon as
            # we release it; while any is pending we simply wait.
            while tts.user_requests_pending() > 0:
                time.sleep(0.05)
            samples, pred_dur = tts.render_chunk_locked(pipeline, chunk, tts.effective_speed(speed))
            clip_cache.put(key, tts.wav_from_samples(samples), {"pred_dur": pred_dur} if pred_dur else None)
            _set(rendered=index + 1)
    except Exception as exc:  # noqa: BLE001 - background job must not crash the server
        _set(state=f"failed: {exc}", finished=time.time())
        log.error("library pre-render failed after %d clips: %s", int(_state["rendered"]), exc)
        return status()
    _set(state="done", finished=time.time())
    log.warning("library pre-render done: %d clips in %.0fs (%s)", len(todo), time.perf_counter() - started, clip_cache.stats())
    return status()


def run_in_background(tts: KokoroAtticTTS | None = None) -> threading.Thread:
    thread = threading.Thread(target=run, args=(tts,), name="library-prerender", daemon=True)
    thread.start()
    return thread


def enabled() -> bool:
    value = os.getenv("LIBRARY_PRERENDER", "true").lower()
    return value in {"1", "true", "yes", "on"}
