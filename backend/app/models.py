from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class SynthesizeRequest(TextRequest):
    # Learner playback multiplier: 1.0 is the tuned default narration pace
    # (KOKORO_SPEED); 0.6 is a slow, deliberate reading; 1.25 is brisk.
    speed: float = Field(default=1.0, ge=0.5, le=1.5)


class PhonemizeResponse(BaseModel):
    normalized_text: str
    ipa: str


class SentenceSpan(BaseModel):
    index: int
    text: str
    start: int
    end: int


class SegmentResponse(BaseModel):
    sentences: list[SentenceSpan]


class SentenceClip(SentenceSpan):
    ipa: str
    # Base64-encoded WAV, or null when the sentence has nothing pronounceable.
    audio_base64: str | None
    mime_type: str = "audio/wav"
    duration_seconds: float | None


class BatchSynthesizeResponse(BaseModel):
    provider: str
    normalized_text: str
    speed: float
    sentences: list[SentenceClip]
