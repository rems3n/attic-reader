from __future__ import annotations

from io import BytesIO
import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .greek import attic_ipa, normalize_polytonic
from .greek.segment import segment_sentences
from .models import PhonemizeResponse, SegmentResponse, TextRequest
from .ocr import OCRUnavailable, recognize_ancient_greek
from .tts import TTSUnavailable, provider_statuses, synthesize_best

app = FastAPI(title="Attic Reader API", version="0.1.0")

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/ocr")
async def ocr(file: UploadFile = File(...)) -> dict[str, str]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Please upload an image file.")

    data = await file.read()
    if len(data) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be under 15 MB.")

    try:
        text = recognize_ancient_greek(data)
    except OCRUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read image: {exc}") from exc

    return {"text": text}


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
def synthesize(request: TextRequest) -> StreamingResponse:
    normalized = normalize_polytonic(request.text)
    ipa = attic_ipa(normalized)

    try:
        audio, provider = synthesize_best(normalized, ipa)
    except TTSUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return StreamingResponse(
        BytesIO(audio),
        media_type="audio/wav",
        headers={
            "Content-Disposition": 'inline; filename="ancient-greek.wav"',
            "X-TTS-Provider": provider,
        },
    )
