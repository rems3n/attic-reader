"""Shared fixtures.

Kokoro (and torch) are not importable in every test environment, so the
synthesis tests drive the adapter with a fake pipeline that records what it was
asked to render and returns a short sine burst per chunk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pytest

from app.tts.kokoro import KokoroAtticTTS


@dataclass
class FakeResult:
    audio: Any


@dataclass
class FakePipeline:
    calls: list[dict[str, Any]] = field(default_factory=list)
    samples_per_char: int = 240  # 10 ms of 24 kHz audio per phoneme character

    def generate_from_tokens(self, phonemes: str, voice: str, speed: float):
        self.calls.append({"phonemes": phonemes, "voice": voice, "speed": speed})
        n = max(1, len(phonemes) * self.samples_per_char)
        t = np.arange(n, dtype=np.float32) / 24000.0
        yield FakeResult(audio=0.3 * np.sin(2 * np.pi * 220.0 * t))


@pytest.fixture
def fake_kokoro(monkeypatch) -> FakePipeline:
    pipeline = FakePipeline()
    monkeypatch.setattr(KokoroAtticTTS, "_load", lambda self: pipeline)
    monkeypatch.setattr(KokoroAtticTTS, "is_available", lambda self: (True, "fake"))
    monkeypatch.setenv("ENABLE_KOKORO", "true")
    monkeypatch.setenv("KOKORO_SPEED", "0.92")
    monkeypatch.setenv("KOKORO_PAUSE_MS", "100")
    return pipeline
