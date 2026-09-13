from __future__ import annotations

"""Kokoro neural TTS adapter with direct Attic phoneme input.

Kokoro's KPipeline.generate_from_tokens accepts a raw phoneme string, which lets
us bypass its English/modern-language G2P entirely.  That is the key property we
need: the Ancient Greek pronunciation remains controlled by app.greek.g2p.
"""

import io
import logging
import os
import re
import threading
import time
import wave
from typing import Any, Iterator

from .piper import TTSUnavailable

SAMPLE_RATE = 24000
log = logging.getLogger("attic.tts")

# Kokoro's published vocabulary includes the IPA symbols used by our Attic MVP,
# with two exceptions:
#   * the non-syllabic tie mark U+032F is not a token.  Removing it does not
#     merge the vowels; it simply represents ai̯/oi̯/etc. as ai/oi/etc.
#   * ASCII "g" (U+0067) is NOT in the vocab; Kokoro uses IPA "ɡ" (U+0261).
#     Without this mapping every γ was silently dropped by the model.
KOKORO_REMOVE = {"̯"}
KOKORO_MAP = {"g": "ɡ"}

# Verified against hexgrad/Kokoro-82M config.json (114 symbols). Kept here so a
# vocab regression is loud (warning + audit field) rather than silent deletion.
KOKORO_VOCAB = set(
    ";:,.!?—…\"()“” ̃ʣʥʦʨᵝꭧAIOQSTWYᵊabcdefhijklmnopqrstuvwxyzɑɐɒæβɔɕçɖðʤəɚɛɜɟɡɥɨɪʝɯɰŋɳɲɴøɸθœɹɾɻʁɽʂʃʈʧʊʋʌɣɤχʎʒʔˈˌːʰʲ↓→↗↘ᵻ"
)

# Sentence-final punctuation as it appears in the canonical IPA string.  The G2P
# maps the Greek question mark to "?" and ano teleia to ",", so only these three
# end a sentence here.  Clause punctuation is used only to break up a sentence
# that is too long for the model on its own.
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_END_RE = re.compile(r"(?<=[,;:—])\s+")


def unknown_kokoro_symbols(phonemes: str) -> list[str]:
    """Return symbols the model vocabulary cannot represent (would be dropped)."""
    return sorted({ch for ch in phonemes if ch not in KOKORO_VOCAB})


def prepare_kokoro_phonemes(ipa: str) -> str:
    out = "".join(KOKORO_MAP.get(ch, ch) for ch in ipa if ch not in KOKORO_REMOVE)
    # Kokoro is trained on punctuation as prosodic tokens.  Keep our sentence
    # punctuation but normalize whitespace for stable chunking.
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _pack_words(words: list[str], max_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _split_long_sentence(sentence: str, max_chars: int) -> list[str]:
    """Break one over-long sentence at clause punctuation, then at words."""
    clauses = [c.strip() for c in _CLAUSE_END_RE.split(sentence) if c.strip()]
    packed = _pack_words(clauses, max_chars)
    out: list[str] = []
    for piece in packed:
        if len(piece) <= max_chars:
            out.append(piece)
        else:
            out.extend(_pack_words(piece.split(), max_chars))
    return out


def split_phonemes(ipa: str, max_chars: int = 450) -> list[str]:
    """Chunk a phoneme string one sentence per chunk.

    Each sentence becomes its own chunk so the renderer can put a natural pause
    between sentences.  A sentence longer than Kokoro's ~510-token window is
    split at clause punctuation and, as a last resort, at word boundaries.
    """
    ipa = prepare_kokoro_phonemes(ipa)
    if not ipa:
        return []
    chunks: list[str] = []
    for sentence in _SENTENCE_END_RE.split(ipa):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= max_chars:
            chunks.append(sentence)
        else:
            chunks.extend(_split_long_sentence(sentence, max_chars))
    return chunks


def has_speech(phonemes: str) -> bool:
    """True when the chunk contains something pronounceable (not only punctuation)."""
    return any(ch.isalpha() for ch in phonemes)


def wav_bytes(samples: Any, sample_rate: int = SAMPLE_RATE) -> bytes:
    try:
        import numpy as np
    except ImportError as exc:
        raise TTSUnavailable("Kokoro requires numpy.") from exc
    samples = np.asarray(samples, dtype=np.float32).reshape(-1)
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    if peak > 1.0:
        samples = samples / peak
    pcm = (np.clip(samples, -1.0, 1.0) * 32767.0).astype("<i2")
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return output.getvalue()


def _to_float32(audio: Any) -> Any:
    """Accept a torch tensor or anything numpy can consume."""
    import numpy as np

    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    return np.asarray(audio, dtype=np.float32).reshape(-1)


class KokoroAtticTTS:
    provider_id = "kokoro-attic"
    display_name = "Kokoro · direct Classical Attic phonemes"

    _pipeline: Any | None = None
    _pipeline_key: str | None = None
    _load_lock = threading.Lock()

    def __init__(self) -> None:
        self.repo_id = os.getenv("KOKORO_REPO_ID", "hexgrad/Kokoro-82M")
        # im_nicola chosen by the user on 2026-09-12 after listening: correct /y/
        # and /h/, no English linking-R after long vowels. bm_george is the
        # accepted fallback. lang_code only selects which G2P the pipeline loads;
        # we bypass it, but "i" avoids the spaCy dependency that "a"/"b" pull in.
        self.voice = os.getenv("KOKORO_VOICE", "im_nicola")
        self.lang_code = os.getenv("KOKORO_LANG_CODE", "i")
        self.device = os.getenv("KOKORO_DEVICE") or None
        # Base narration pace.  The API's `speed` is a learner multiplier on top
        # of this (1.0 = default pace), so the tuned default survives the UI.
        self.speed = float(os.getenv("KOKORO_SPEED", "0.92"))
        self.max_chars = int(os.getenv("KOKORO_CHUNK_CHARS", "450"))
        self.pause_ms = int(os.getenv("KOKORO_PAUSE_MS", "140"))

    def is_available(self) -> tuple[bool, str]:
        try:
            from kokoro import KPipeline  # noqa: F401
        except ImportError:
            return False, "Install Kokoro: pip install 'kokoro>=0.9.4' soundfile"
        return True, f"voice={self.voice}; raw phoneme mode"

    def _load(self) -> Any:
        key = f"{self.repo_id}|{self.lang_code}|{self.device}"
        cls = self.__class__
        if cls._pipeline is not None and cls._pipeline_key == key:
            return cls._pipeline
        # One loader at a time: the startup warm-up thread and a first request
        # must not both construct (and download) the model.
        with cls._load_lock:
            if cls._pipeline is not None and cls._pipeline_key == key:
                return cls._pipeline
            try:
                from kokoro import KPipeline
            except ImportError as exc:
                raise TTSUnavailable(
                    "Kokoro is not installed. Run: pip install 'kokoro>=0.9.4' soundfile"
                ) from exc
            started = time.perf_counter()
            try:
                pipeline = KPipeline(
                    lang_code=self.lang_code,
                    repo_id=self.repo_id,
                    device=self.device,
                )
            except Exception as exc:
                raise TTSUnavailable(f"Could not load Kokoro neural model: {exc}") from exc
            log.warning("Kokoro pipeline loaded in %.1fs (%s)", time.perf_counter() - started, key)
            cls._pipeline = pipeline
            cls._pipeline_key = key
            return pipeline

    def effective_speed(self, speed: float | None) -> float:
        return self.speed * (1.0 if speed is None else float(speed))

    @staticmethod
    def _wav_bytes(samples: Any, sample_rate: int = SAMPLE_RATE) -> bytes:
        return wav_bytes(samples, sample_rate)

    def _render_chunks(self, pipeline: Any, chunks: list[str], kokoro_speed: float) -> Any:
        """Render chunks through Kokoro and join them with a short pause."""
        import numpy as np

        pause = np.zeros(int(SAMPLE_RATE * self.pause_ms / 1000), dtype=np.float32)
        rendered: list[Any] = []
        for index, phonemes in enumerate(chunks):
            # generate_from_tokens accepts a raw phoneme string and bypasses
            # the language-specific G2P stage entirely.
            results = list(
                pipeline.generate_from_tokens(
                    phonemes,
                    voice=self.voice,
                    speed=kokoro_speed,
                )
            )
            if not results or results[0].audio is None:
                raise TTSUnavailable("Kokoro returned no audio.")
            rendered.append(_to_float32(results[0].audio))
            if index < len(chunks) - 1 and pause.size:
                rendered.append(pause)
        return np.concatenate(rendered) if len(rendered) > 1 else rendered[0]

    def synthesize(self, ipa: str, speed: float | None = None) -> bytes:
        """Render one IPA string (any number of sentences) into a single WAV."""
        chunks = [c for c in split_phonemes(ipa, max_chars=self.max_chars) if has_speech(c)]
        if not chunks:
            raise TTSUnavailable("No phonemes were available for Kokoro synthesis.")

        pipeline = self._load()
        try:
            samples = self._render_chunks(pipeline, chunks, self.effective_speed(speed))
            return wav_bytes(samples, SAMPLE_RATE)
        except TTSUnavailable:
            raise
        except Exception as exc:
            raise TTSUnavailable(f"Kokoro synthesis failed: {exc}") from exc

    def iter_synthesize(self, ipas: list[str], speed: float | None = None) -> Iterator[bytes | None]:
        """Yield one WAV per IPA string as soon as it is rendered (``None`` = no speech).

        Streaming matters on a CPU host: a paragraph takes tens of seconds in
        total, and mobile browsers abort requests that stay silent for ~60 s.
        """
        pipeline = self._load()
        kokoro_speed = self.effective_speed(speed)
        try:
            for index, ipa in enumerate(ipas):
                chunks = [c for c in split_phonemes(ipa, max_chars=self.max_chars) if has_speech(c)]
                if not chunks:
                    yield None
                    continue
                started = time.perf_counter()
                samples = self._render_chunks(pipeline, chunks, kokoro_speed)
                elapsed = time.perf_counter() - started
                audio_seconds = len(samples) / SAMPLE_RATE
                log.info(
                    "kokoro sentence %d: %.1fs audio in %.2fs (rtf %.2f, %d chunk%s)",
                    index, audio_seconds, elapsed, elapsed / max(audio_seconds, 1e-6),
                    len(chunks), "" if len(chunks) == 1 else "s",
                )
                yield wav_bytes(samples, SAMPLE_RATE)
        except TTSUnavailable:
            raise
        except Exception as exc:
            raise TTSUnavailable(f"Kokoro synthesis failed: {exc}") from exc

    def synthesize_many(self, ipas: list[str], speed: float | None = None) -> list[bytes | None]:
        """Render one WAV per IPA string; ``None`` where a string has no speech."""
        return list(self.iter_synthesize(ipas, speed=speed))

    # ---- warm-up -------------------------------------------------------
    _warm_lock = threading.Lock()
    _warm_state: str = "cold"  # cold | warming | ready | failed:<reason>

    @classmethod
    def warm_state(cls) -> str:
        return cls._warm_state

    def warm_up(self) -> None:
        """Download/load the model and run one tiny synthesis (blocking)."""
        cls = self.__class__
        with cls._warm_lock:
            if cls._warm_state in {"warming", "ready"}:
                return
            cls._warm_state = "warming"
        started = time.perf_counter()
        try:
            pipeline = self._load()
            self._render_chunks(pipeline, ["ˈɛːlios."], self.speed)
            cls._warm_state = "ready"
            log.warning("Kokoro warm-up done in %.1fs (voice=%s)", time.perf_counter() - started, self.voice)
        except Exception as exc:  # noqa: BLE001 - report, never crash startup
            cls._warm_state = f"failed: {exc}"
            log.error("Kokoro warm-up failed after %.1fs: %s", time.perf_counter() - started, exc)

    def warm_up_in_background(self) -> threading.Thread:
        thread = threading.Thread(target=self.warm_up, name="kokoro-warmup", daemon=True)
        thread.start()
        return thread
