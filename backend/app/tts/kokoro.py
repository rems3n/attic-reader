from __future__ import annotations

"""Kokoro neural TTS adapter with direct Attic phoneme input.

Kokoro's KPipeline.generate_from_tokens accepts a raw phoneme string, which lets
us bypass its English/modern-language G2P entirely.  That is the key property we
need: the Ancient Greek pronunciation remains controlled by app.greek.g2p.
"""

import io
import os
import re
import wave
from typing import Any

from .piper import TTSUnavailable

# Kokoro's published vocabulary includes the IPA symbols used by our Attic MVP,
# with two exceptions:
#   * the non-syllabic tie mark U+032F is not a token.  Removing it does not
#     merge the vowels; it simply represents ai̯/oi̯/etc. as ai/oi/etc.
#   * ASCII "g" (U+0067) is NOT in the vocab; Kokoro uses IPA "ɡ" (U+0261).
#     Without this mapping every γ was silently dropped by the model.
KOKORO_REMOVE = {"\u032f"}
KOKORO_MAP = {"g": "\u0261"}

# Verified against hexgrad/Kokoro-82M config.json (114 symbols). Kept here so a
# vocab regression is loud (warning + audit field) rather than silent deletion.
KOKORO_VOCAB = set(
    ";:,.!?—…\"()“” ̃ʣʥʦʨᵝꭧAIOQSTWYᵊabcdefhijklmnopqrstuvwxyzɑɐɒæβɔɕçɖðʤəɚɛɜɟɡɥɨɪʝɯɰŋɳɲɴøɸθœɹɾɻʁɽʂʃʈʧʊʋʌɣɤχʎʒʔˈˌːʰʲ↓→↗↘ᵻ"
)


def unknown_kokoro_symbols(phonemes: str) -> list[str]:
    """Return symbols the model vocabulary cannot represent (would be dropped)."""
    return sorted({ch for ch in phonemes if ch not in KOKORO_VOCAB})


def prepare_kokoro_phonemes(ipa: str) -> str:
    out = "".join(KOKORO_MAP.get(ch, ch) for ch in ipa if ch not in KOKORO_REMOVE)
    # Kokoro is trained on punctuation as prosodic tokens.  Keep our sentence
    # punctuation but normalize whitespace for stable chunking.
    out = re.sub(r"\s+", " ", out).strip()
    return out


def split_phonemes(ipa: str, max_chars: int = 450) -> list[str]:
    """Split phonemes below Kokoro's ~510-token limit on punctuation first."""
    ipa = prepare_kokoro_phonemes(ipa)
    if not ipa:
        return []
    if len(ipa) <= max_chars:
        return [ipa]

    pieces = re.split(r"(?<=[.!?;:,])\s+", ipa)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        candidate = f"{current} {piece}".strip() if current else piece
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(piece) <= max_chars:
            current = piece
            continue
        # Last-resort word boundary split.
        words = piece.split()
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


class KokoroAtticTTS:
    provider_id = "kokoro-attic"
    display_name = "Kokoro · direct Classical Attic phonemes"

    _pipeline: Any | None = None
    _pipeline_key: str | None = None

    def __init__(self) -> None:
        self.repo_id = os.getenv("KOKORO_REPO_ID", "hexgrad/Kokoro-82M")
        # im_nicola chosen by the user on 2026-09-12 after listening: correct /y/
        # and /h/, no English linking-R after long vowels. bm_george is the
        # accepted fallback. lang_code only selects which G2P the pipeline loads;
        # we bypass it, but "i" avoids the spaCy dependency that "a"/"b" pull in.
        self.voice = os.getenv("KOKORO_VOICE", "im_nicola")
        self.lang_code = os.getenv("KOKORO_LANG_CODE", "i")
        self.device = os.getenv("KOKORO_DEVICE") or None
        self.speed = float(os.getenv("KOKORO_SPEED", "0.92"))

    def is_available(self) -> tuple[bool, str]:
        try:
            from kokoro import KPipeline  # noqa: F401
        except ImportError:
            return False, "Install Kokoro: pip install 'kokoro>=0.9.4' soundfile"
        return True, f"voice={self.voice}; raw phoneme mode"

    def _load(self) -> Any:
        key = f"{self.repo_id}|{self.lang_code}|{self.device}"
        if self.__class__._pipeline is not None and self.__class__._pipeline_key == key:
            return self.__class__._pipeline
        try:
            from kokoro import KPipeline
        except ImportError as exc:
            raise TTSUnavailable(
                "Kokoro is not installed. Run: pip install 'kokoro>=0.9.4' soundfile"
            ) from exc
        try:
            pipeline = KPipeline(
                lang_code=self.lang_code,
                repo_id=self.repo_id,
                device=self.device,
            )
        except Exception as exc:
            raise TTSUnavailable(f"Could not load Kokoro neural model: {exc}") from exc
        self.__class__._pipeline = pipeline
        self.__class__._pipeline_key = key
        return pipeline

    @staticmethod
    def _wav_bytes(samples: Any, sample_rate: int = 24000) -> bytes:
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

    def synthesize(self, ipa: str) -> bytes:
        chunks = split_phonemes(
            ipa, max_chars=int(os.getenv("KOKORO_CHUNK_CHARS", "450"))
        )
        if not chunks:
            raise TTSUnavailable("No phonemes were available for Kokoro synthesis.")

        pipeline = self._load()
        try:
            import numpy as np
            rendered: list[Any] = []
            pause_ms = int(os.getenv("KOKORO_PAUSE_MS", "140"))
            pause = np.zeros(int(24000 * pause_ms / 1000), dtype=np.float32)
            for index, phonemes in enumerate(chunks):
                # generate_from_tokens accepts a raw phoneme string and bypasses
                # the language-specific G2P stage entirely.
                results = list(
                    pipeline.generate_from_tokens(
                        phonemes,
                        voice=self.voice,
                        speed=self.speed,
                    )
                )
                if not results or results[0].audio is None:
                    raise TTSUnavailable("Kokoro returned no audio.")
                rendered.append(results[0].audio.detach().cpu().numpy().astype(np.float32))
                if index < len(chunks) - 1 and pause.size:
                    rendered.append(pause)
            samples = np.concatenate(rendered) if len(rendered) > 1 else rendered[0]
            return self._wav_bytes(samples, 24000)
        except TTSUnavailable:
            raise
        except Exception as exc:
            raise TTSUnavailable(f"Kokoro synthesis failed: {exc}") from exc
