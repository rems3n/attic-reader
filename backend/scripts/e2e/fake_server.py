"""Run the API with a fake Kokoro pipeline (same as tests/conftest.py) so the
frontend can be driven end to end without model weights."""

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

os.environ.setdefault("CLIP_CACHE_DIR", tempfile.mkdtemp(prefix="e2e-clips-"))
os.environ.setdefault("PROGRESS_DIR", tempfile.mkdtemp(prefix="e2e-progress-"))
os.environ["ENABLE_KOKORO"] = "true"
os.environ["KOKORO_WARMUP"] = "false"
os.environ["LIBRARY_PRERENDER"] = "false"
PORT = int(os.environ.get("E2E_API_PORT", "8000"))
# E2E_FRONT (e.g. http://localhost:3100) adds a frontend origin besides :3000.
_extra = os.environ.get("E2E_FRONT", "").rstrip("/")
os.environ["CORS_ORIGINS"] = ",".join(filter(None, ["http://localhost:3000", "http://127.0.0.1:3000", _extra]))

from conftest import FakePipeline  # noqa: E402
from app.tts.kokoro import KokoroAtticTTS  # noqa: E402

pipeline = FakePipeline()
KokoroAtticTTS._load = lambda self: pipeline  # type: ignore[method-assign]
KokoroAtticTTS.is_available = lambda self: (True, "fake")  # type: ignore[method-assign]

import uvicorn  # noqa: E402
from app.main import app  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
