from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from .piper import TTSUnavailable


class EspeakAncientGreekTTS:
    """Dependency-light fallback using eSpeak's dedicated Ancient Greek voice.

    This is intentionally separate from the custom Attic IPA/Piper path. eSpeak's
    ``grc`` voice supplies its own Ancient Greek grapheme-to-phoneme rules and is
    useful as a zero-cost baseline/fallback when no neural voice is configured.
    """

    def __init__(self) -> None:
        self.command = os.getenv("ESPEAK_COMMAND", "espeak")
        self.voice = os.getenv("ESPEAK_VOICE", "grc")
        self.speed = int(os.getenv("ESPEAK_SPEED", "125"))

    def synthesize(self, greek_text: str) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = Path(tmp.name)

        try:
            cmd = [
                *shlex.split(self.command),
                "-v",
                self.voice,
                "-s",
                str(self.speed),
                "-w",
                str(output_path),
                greek_text,
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except FileNotFoundError as exc:
                raise TTSUnavailable(
                    "eSpeak is not installed and Piper is not configured."
                ) from exc

            if proc.returncode != 0:
                raise TTSUnavailable(proc.stderr.strip() or "eSpeak synthesis failed")

            return output_path.read_bytes()
        finally:
            output_path.unlink(missing_ok=True)
