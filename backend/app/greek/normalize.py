import unicodedata


def normalize_polytonic(text: str) -> str:
    """Normalize input for display/storage while preserving polytonic marks."""
    text = text.replace("\u00a0", " ")
    text = text.replace("\u037e", ";")  # Greek question mark -> stable punctuation
    text = " ".join(text.split())
    return unicodedata.normalize("NFC", text)
