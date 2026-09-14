"""Optional flash-card progress backup keyed by a user-chosen sync code.

No accounts: the client keeps its spaced-repetition state in the browser and
may push a copy here under a code it chooses (≥ 8 characters). The code is
hashed; only the hash names the file. Documents are opaque JSON blobs with a
size cap; merging is the client's job (newest `updated` per card wins).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
CODE_RE = re.compile(r"^[A-Za-z0-9 _.\-]{8,64}$")


class ProgressError(ValueError):
    pass


def progress_dir() -> Path:
    raw = os.getenv("PROGRESS_DIR")
    if raw:
        path = Path(raw)
    elif os.getenv("CLIP_CACHE_DIR"):
        path = Path(os.getenv("CLIP_CACHE_DIR", "")).parent / "progress"
    else:
        path = Path(tempfile.gettempdir()) / "attic-progress"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(code: str) -> Path:
    code = code.strip()
    if not CODE_RE.match(code):
        raise ProgressError("Sync code must be 8–64 letters, digits, spaces or - _ .")
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
    return progress_dir() / f"{digest}.json"


def save(code: str, document: dict) -> dict:
    payload = json.dumps(document, ensure_ascii=False)
    if len(payload.encode("utf-8")) > MAX_BYTES:
        raise ProgressError("Progress document is too large.")
    path = _path(code)
    wrapper = {"saved_at": time.time(), "document": document}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(wrapper, ensure_ascii=False), "utf-8")
    tmp.replace(path)
    return {"saved_at": wrapper["saved_at"], "bytes": len(payload)}


def load(code: str) -> dict | None:
    path = _path(code)
    if not path.exists():
        return None
    return json.loads(path.read_text("utf-8"))
