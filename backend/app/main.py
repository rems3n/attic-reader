from __future__ import annotations

import base64
import io
import logging
import os
import wave

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
from .tts import TTSUnavailable, provider_statuses, synthesize_best, synthesize_sentences

app = FastAPI(title="Attic Reader API", version="0.2.0")
log = logging.getLogger("attic")


@app.on_event("startup")
def _log_capabilities() -> None:
    log.warning("OCR preprocessing engine: %s", "opencv" if opencv_available() else "pillow fallback (degraded)")

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
    return {"providers": provider_statuses()}


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
