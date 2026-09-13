from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


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
