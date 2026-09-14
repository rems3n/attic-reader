from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
import wave
from typing import Iterator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .greek import attic_ipa, normalize_polytonic
from .greek.segment import segment_sentences
from .models import (
    BatchSynthesizeResponse,
    PhonemizeResponse,
    SegmentResponse,
    SentenceClip,
    SynthesizeRequest,
    TextRequest,
)
from .ocr import OCRUnavailable, recognize_ancient_greek_with_report
from .ocr_preprocess import opencv_available
from .tts import (
    TTSUnavailable,
    provider_statuses,
    synthesize_best,
    synthesize_sentences,
    synthesize_sentences_stream,
)
from .tts.kokoro import KokoroAtticTTS
from .tts import prerender
from .library import LibraryError, get_item, load_manifest, summary, CATEGORIES
from . import vocab
from .greek.morph import paradigms

app = FastAPI(title="Attic Reader API", version="0.2.0")
log = logging.getLogger("attic")
# Uvicorn configures its own loggers only; make ours visible (per-sentence
# synthesis timings are INFO).
logging.getLogger("attic").setLevel(logging.INFO)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def _truthy(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower() in {"1", "true", "yes", "on"}


@app.on_event("startup")
def _log_capabilities() -> None:
    log.warning("OCR preprocessing engine: %s", "opencv" if opencv_available() else "pillow fallback (degraded)")
    # Load Kokoro (and download it on a fresh volume) before the first user
    # asks, so the first Generate does not pay ~60-120 s of model start-up.
    if _truthy("ENABLE_KOKORO", True) and _truthy("KOKORO_WARMUP", True):
        def warm_then_prerender() -> None:
            tts = KokoroAtticTTS()
            tts.warm_up()
            if KokoroAtticTTS.warm_state() == "ready" and prerender.enabled():
                prerender.run(tts)

        import threading

        threading.Thread(target=warm_then_prerender, name="kokoro-warmup", daemon=True).start()

def _cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-TTS-Provider"],
)


def _wav_duration_seconds(data: bytes) -> float | None:
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            return round(frames / rate, 3) if rate else None
    except (wave.Error, EOFError):
        return None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/ocr")
async def ocr(file: UploadFile = File(...)) -> dict[str, object]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image file.")

    data = await file.read()
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be under 15 MB.")

    try:
        text, report = recognize_ancient_greek_with_report(data)
    except OCRUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read image: {exc}") from exc

    # `preprocess` tells the client which path ran (opencv vs pillow fallback)
    # and what was corrected, so a bad read can be diagnosed from the phone.
    return {"text": text, "preprocess": report}


@app.post("/api/phonemize", response_model=PhonemizeResponse)
def phonemize(request: TextRequest) -> PhonemizeResponse:
    normalized = normalize_polytonic(request.text)
    return PhonemizeResponse(normalized_text=normalized, ipa=attic_ipa(normalized))


@app.post("/api/segment", response_model=SegmentResponse)
def segment(request: TextRequest) -> SegmentResponse:
    """Split Greek into sentences. Spans index into the text exactly as sent."""
    return SegmentResponse(
        sentences=[s.as_dict() for s in segment_sentences(request.text)]  # type: ignore[arg-type]
    )


@app.get("/api/tts/status")
def tts_status() -> dict[str, object]:
    return {"providers": provider_statuses(), "library_prerender": prerender.status()}


@app.get("/api/library")
def library_index() -> dict[str, object]:
    """Built-in readings grouped by category, with which speeds are pre-rendered."""
    tts = KokoroAtticTTS()
    items = [summary(item, prerender.ready_speeds(item, tts)) for item in load_manifest()]
    return {
        "categories": [{"id": cid, "label": label} for cid, label in CATEGORIES],
        "items": items,
        "prerender": prerender.status(),
    }


@app.get("/api/library/{item_id}")
def library_item(item_id: str) -> dict[str, object]:
    try:
        item = get_item(item_id)
    except LibraryError:
        raise HTTPException(status_code=404, detail=f"No reading with id {item_id!r}.")
    return {**summary(item, prerender.ready_speeds(item)), "text": item["text"], "sentences": item["sentences"]}


@app.get("/api/vocab")
def vocab_index() -> dict[str, object]:
    """DCC core vocabulary: every word (light summary) plus facet counts for
    building a study deck by topic, semantic group, part of speech or tier."""
    entries = vocab.load_entries()
    return {
        "attribution": vocab.ATTRIBUTION,
        "attribution_url": vocab.ATTRIBUTION_URL,
        "facets": vocab.facets(entries),
        "items": [vocab.summary(e) for e in entries],
    }


@app.get("/api/vocab/{entry_id}")
def vocab_entry(entry_id: str) -> dict[str, object]:
    try:
        entry = vocab.get_entry(entry_id)
    except vocab.VocabError:
        raise HTTPException(status_code=404, detail=f"No vocabulary entry with id {entry_id!r}.")
    return vocab.detail(entry)


@app.get("/api/grammar")
def grammar_index() -> dict[str, object]:
    """Grammar section: model paradigms grouped by topic."""
    return paradigms.index()


@app.get("/api/grammar/{paradigm_id}")
def grammar_item(paradigm_id: str) -> dict[str, object]:
    try:
        return paradigms.get(paradigm_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"No paradigm with id {paradigm_id!r}.")


@app.post("/api/synthesize")
def synthesize(request: SynthesizeRequest) -> StreamingResponse:
    """Whole-text synthesis as one WAV (sentence-chunked internally)."""
    normalized = normalize_polytonic(request.text)
    ipa = attic_ipa(normalized)

    try:
        audio, provider = synthesize_best(normalized, ipa, speed=request.speed)
    except TTSUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'inline; filename="ancient-greek.wav"',
            "X-TTS-Provider": provider,
        },
    )


def _ndjson(obj: dict[str, object]) -> bytes:
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")


def _stream_sentences(normalized: str, sentences, ipas: list[str], speed: float) -> Iterator[bytes]:
    started = time.perf_counter()
    try:
        provider, clips = synthesize_sentences_stream([s.text for s in sentences], ipas, speed=speed)
    except TTSUnavailable as exc:
        yield _ndjson({"type": "error", "detail": str(exc)})
        return
    yield _ndjson(
        {
            "type": "start",
            "provider": provider,
            "normalized_text": normalized,
            "speed": speed,
            "sentences": [{**s.as_dict(), "ipa": ipa} for s, ipa in zip(sentences, ipas)],
        }
    )
    try:
        for sentence, (clip, words) in zip(sentences, clips):
            yield _ndjson(
                {
                    "type": "clip",
                    "index": sentence.index,
                    "audio_base64": base64.b64encode(clip).decode("ascii") if clip else None,
                    "mime_type": "audio/wav",
                    "duration_seconds": _wav_duration_seconds(clip) if clip else None,
                    # Per-word time spans (char offsets into the sentence text,
                    # seconds into the clip) for follow-along highlighting.
                    "words": words,
                }
            )
    except TTSUnavailable as exc:
        yield _ndjson({"type": "error", "detail": str(exc)})
        return
    yield _ndjson({"type": "done", "elapsed_seconds": round(time.perf_counter() - started, 2)})


@app.post("/api/synthesize/stream")
def synthesize_stream(request: SynthesizeRequest) -> StreamingResponse:
    """NDJSON stream: a 'start' line with the sentence plan, then one 'clip' line
    per sentence as soon as it is rendered, then 'done' (or 'error')."""
    normalized = normalize_polytonic(request.text)
    sentences = segment_sentences(normalized)
    if not sentences:
        raise HTTPException(status_code=422, detail="No sentences found in the text.")
    ipas = [attic_ipa(s.text) for s in sentences]
    return StreamingResponse(
        _stream_sentences(normalized, sentences, ipas, request.speed),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@app.post("/api/synthesize/batch", response_model=BatchSynthesizeResponse)
def synthesize_batch(request: SynthesizeRequest) -> BatchSynthesizeResponse:
    """One clip per sentence. Spans index into ``normalized_text``."""
    normalized = normalize_polytonic(request.text)
    sentences = segment_sentences(normalized)
    if not sentences:
        raise HTTPException(status_code=422, detail="No sentences found in the text.")

    ipas = [attic_ipa(s.text) for s in sentences]
    try:
        clips, provider = synthesize_sentences([s.text for s in sentences], ipas, speed=request.speed)
    except TTSUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    rows: list[SentenceClip] = []
    for sentence, ipa, clip in zip(sentences, ipas, clips):
        rows.append(
            SentenceClip(
                index=sentence.index,
                text=sentence.text,
                start=sentence.start,
                end=sentence.end,
                ipa=ipa,
                audio_base64=base64.b64encode(clip).decode("ascii") if clip else None,
                duration_seconds=_wav_duration_seconds(clip) if clip else None,
            )
        )

    return BatchSynthesizeResponse(
        provider=provider,
        normalized_text=normalized,
        speed=request.speed,
        sentences=rows,
    )
