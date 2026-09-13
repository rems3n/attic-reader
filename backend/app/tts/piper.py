from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path


class TTSUnavailable(RuntimeError):
    pass


class PiperTTS:
    def __init__(self) -> None:
        self.command = os.getenv("PIPER_COMMAND", "python -m piper")
        self.model = os.getenv("PIPER_MODEL")

    def synthesize(self, ipa: str) -> bytes:
        if not self.model:
            raise TTSUnavailable(
                "PIPER_MODEL is not configured. OCR and phonemization work; "
                "set PIPER_MODEL to enable audio synthesis."
            )

        model_path = Path(self.model)
        if not model_path.exists():
            raise TTSUnavailable(f"Piper model not found: {model_path}")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = Path(tmp.name)

        try:
            cmd = [
                *shlex.split(self.command),
                "-m",
                str(model_path),
                "--output_file",
                str(output_path),
                "--",
                f"[[ {ipa} ]]",
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.returncode != 0:
                raise TTSUnavailable(proc.stderr.strip() or "Piper synthesis failed")
            return output_path.read_bytes()
        finally:
            output_path.unlink(missing_ok=True)
