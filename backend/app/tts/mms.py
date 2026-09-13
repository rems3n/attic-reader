from __future__ import annotations

"""Meta MMS Ancient Greek neural TTS adapter.

The checkpoint ``facebook/mms-tts-grc`` is a dedicated VITS model for ISO 639-3
``grc`` (Ancient Greek).  Unlike our Piper path it consumes polytonic Greek
orthography directly, so this adapter intentionally does *not* feed it our IPA.

We keep it isolated behind the same provider interface because its learned
pronunciation still needs listening validation against our Classical Attic target.
"""

import io
import os
import re
import threading
import unicodedata
import wave
from pathlib import Path
from typing import Any


from .piper import TTSUnavailable

# The public MMS grc vocabulary is lowercase polytonic Greek plus spaces,
# apostrophe, hyphen, en-dash and a special underscore token.  We conservatively
# strip unsupported punctuation rather than letting a tokenizer map it to noise.
_ALLOWED_RE = re.compile(
    r"[^\u0370-\u03ff\u1f00-\u1fff '\u2019\-\u2013]+",
    flags=re.UNICODE,
)


def prepare_mms_grc_text(text: str) -> str:
    """Normalize user/OCR text into the orthography expected by MMS grc.

    - NFC keeps precomposed polytonic characters (matching the published vocab).
    - Lowercase because the model vocabulary is lowercase.
    - Greek punctuation becomes a pause/space; the published vocabulary does not
      include comma/period/semicolon/ano teleia.
    - Curly apostrophe becomes ASCII apostrophe.
    - Unsupported non-Greek material is removed for the speech model only.  The
      editable source text is never modified by this function.
    """

    text = unicodedata.normalize("NFC", text).lower()
    text = text.replace("’", "'").replace("ʼ", "'").replace("᾽", "'").replace("—", "–")
    # Preserve phrase boundaries as spaces.  Sentence splitting is handled above
    # the model when we add timed sentence playback.
    for mark in [",", ".", ";", "·", ":", "!", "?", "·", "\n", "\r", "\t"]:
        text = text.replace(mark, " ")
    text = _ALLOWED_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_greek_for_tts(text: str, max_chars: int = 180) -> list[str]:
    """Split long Greek into VITS-friendly chunks without breaking words."""
    text = unicodedata.normalize("NFC", text).strip()
    if not text:
        return []

    # Greek semicolon is a question mark; ano teleia/colon are strong phrase
    # boundaries. Keep the mark in the source chunk so the next split remains
    # explainable even though prepare_mms_grc_text later strips punctuation.
    candidates = re.split(r"(?<=[.;·:!?·])\s+|[\r\n]+", text)
    chunks: list[str] = []
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        if len(candidate) <= max_chars:
            chunks.append(candidate)
            continue

        words = candidate.split()
        current: list[str] = []
        current_len = 0
        for word in words:
            extra = len(word) + (1 if current else 0)
            if current and current_len + extra > max_chars:
                chunks.append(" ".join(current))
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len += extra
        if current:
            chunks.append(" ".join(current))
    return chunks


class MMSAncientGreekTTS:
    provider_id = "mms-grc"
    display_name = "Meta MMS · Ancient Greek neural"

    _load_lock = threading.Lock()
    _model: Any | None = None
    _tokenizer: Any | None = None
    _torch: Any | None = None
    _model_key: str | None = None

    def __init__(self) -> None:
        self.model_id = os.getenv("MMS_MODEL_ID", "facebook/mms-tts-grc")
        self.model_path = os.getenv("MMS_MODEL_PATH")
        self.device = os.getenv("MMS_DEVICE", "cpu")
        self.local_files_only = os.getenv("MMS_LOCAL_FILES_ONLY", "false").lower() in {
            "1",
            "true",
            "yes",
        }

    @property
    def model_source(self) -> str:
        return self.model_path or self.model_id

    def is_available(self) -> tuple[bool, str]:
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
        except ImportError:
            return False, "Install backend extra: pip install -e '.[mms]'"

        if self.model_path and not Path(self.model_path).exists():
            return False, f"MMS_MODEL_PATH not found: {self.model_path}"

        # With a model path we know the weights are present. With a Hub id, the
        # package can download/cache them on first synthesis when network exists.
        if self.model_path:
            return True, "local model configured"
        if self.local_files_only:
            return False, "MMS_LOCAL_FILES_ONLY is enabled but no MMS_MODEL_PATH is set"
        return True, "model downloads on first use"

    def _load(self) -> tuple[Any, Any, Any]:
        key = f"{self.model_source}|{self.device}|{self.local_files_only}"
        with self._load_lock:
            if (
                self.__class__._model is not None
                and self.__class__._tokenizer is not None
                and self.__class__._model_key == key
            ):
                return self.__class__._torch, self.__class__._tokenizer, self.__class__._model

            try:
                import torch
                from transformers import AutoTokenizer, VitsModel
            except ImportError as exc:
                raise TTSUnavailable(
                    "Meta MMS Ancient Greek is not installed. "
                    "Run: pip install -e '.[mms]'"
                ) from exc

            source = self.model_source
            kwargs: dict[str, Any] = {"local_files_only": self.local_files_only}
            try:
                tokenizer = AutoTokenizer.from_pretrained(source, **kwargs)
                model = VitsModel.from_pretrained(source, **kwargs)
                model = model.to(self.device)
                model.eval()
            except Exception as exc:  # HF raises several environment/network types
                raise TTSUnavailable(f"Could not load MMS Ancient Greek model: {exc}") from exc

            self.__class__._torch = torch
            self.__class__._tokenizer = tokenizer
            self.__class__._model = model
            self.__class__._model_key = key
            return torch, tokenizer, model

    @staticmethod
    def _wav_bytes(samples: Any, sample_rate: int) -> bytes:
        try:
            import numpy as np
        except ImportError as exc:
            raise TTSUnavailable("MMS requires numpy; install the mms extra.") from exc
        samples = np.asarray(samples, dtype=np.float32).reshape(-1)
        peak = float(np.max(np.abs(samples))) if samples.size else 0.0
        if peak > 1.0:
            samples = samples / peak
        pcm = np.clip(samples, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype("<i2")

        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())
        return output.getvalue()

    def synthesize(self, greek_text: str) -> bytes:
        chunks = split_greek_for_tts(
            greek_text, max_chars=int(os.getenv("MMS_CHUNK_CHARS", "180"))
        )
        prepared_chunks = [prepare_mms_grc_text(chunk) for chunk in chunks]
        prepared_chunks = [chunk for chunk in prepared_chunks if chunk]
        if not prepared_chunks:
            raise TTSUnavailable("No Ancient Greek text remained after MMS normalization.")

        torch, tokenizer, model = self._load()
        try:
            import numpy as np

            sample_rate = int(model.config.sampling_rate)
            pause_ms = int(os.getenv("MMS_PAUSE_MS", "180"))
            pause = np.zeros(max(0, int(sample_rate * pause_ms / 1000)), dtype=np.float32)
            seed = int(os.getenv("MMS_SEED", "7"))
            rendered: list[Any] = []

            for index, prepared in enumerate(prepared_chunks):
                inputs = tokenizer(prepared, return_tensors="pt")
                inputs = {name: tensor.to(self.device) for name, tensor in inputs.items()}
                torch.manual_seed(seed + index)
                with torch.inference_mode():
                    waveform = model(**inputs).waveform
                rendered.append(waveform.squeeze().detach().cpu().numpy().astype(np.float32))
                if index < len(prepared_chunks) - 1 and pause.size:
                    rendered.append(pause)

            samples = np.concatenate(rendered) if len(rendered) > 1 else rendered[0]
            return self._wav_bytes(samples, sample_rate)
        except TTSUnavailable:
            raise
        except Exception as exc:
            raise TTSUnavailable(f"MMS Ancient Greek synthesis failed: {exc}") from exc
