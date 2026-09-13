"""Disk cache of rendered sentence clips.

Key: provider, voice, effective model speed and the exact phoneme string sent
to the model, so a cached clip is byte-identical to what a fresh render would
produce. Lives on the persistent volume in production (/data/clip-cache) so
pre-rendered library recordings survive redeploys.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path

# Bump when the cached payload changes shape (v2: per-token durations sidecar).
KEY_VERSION = "v2"

log = logging.getLogger("attic.tts.cache")


def cache_dir() -> Path:
    configured = os.getenv("CLIP_CACHE_DIR")
    if configured:
        return Path(configured)
    hf_home = os.getenv("HF_HOME")
    if hf_home:
        return Path(hf_home).parent / "clip-cache"
    return Path(tempfile.gettempdir()) / "attic-clip-cache"


def clip_key(provider: str, voice: str, model_speed: float, phonemes: str) -> str:
    digest = hashlib.sha256(f"{KEY_VERSION}|{provider}|{voice}|{model_speed:.4f}|{phonemes}".encode("utf-8")).hexdigest()
    return digest


def _path(key: str) -> Path:
    return cache_dir() / key[:2] / f"{key}.wav"


def get(key: str) -> bytes | None:
    path = _path(key)
    try:
        return path.read_bytes()
    except OSError:
        return None


def has(key: str) -> bool:
    return _path(key).is_file()


def get_meta(key: str) -> dict | None:
    """Sidecar metadata stored with a clip (per-token durations for word timing)."""
    try:
        return json.loads(_path(key).with_suffix(".json").read_text("utf-8"))
    except (OSError, ValueError):
        return None


def put(key: str, wav: bytes, meta: dict | None = None) -> None:
    path = _path(key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(wav)
        os.replace(tmp, path)
        if meta is not None:
            meta_path = path.with_suffix(".json")
            meta_tmp = path.with_suffix(".json.tmp")
            meta_tmp.write_text(json.dumps(meta), "utf-8")
            os.replace(meta_tmp, meta_path)
    except OSError as exc:  # cache is best-effort; never fail a synthesis over it
        log.warning("clip cache write failed (%s): %s", path, exc)


def stats() -> dict[str, object]:
    root = cache_dir()
    if not root.exists():
        return {"dir": str(root), "clips": 0, "bytes": 0}
    files = list(root.glob("*/*.wav"))
    return {"dir": str(root), "clips": len(files), "bytes": sum(f.stat().st_size for f in files)}
