import unicodedata


def normalize_polytonic(text: str) -> str:
    """Normalize input for display/storage while preserving polytonic marks."""
    text = text.replace("\u00a0", " ")
    text = text.replace("\u037e", ";")  # Greek question mark -> stable punctuation
    # A spacing koronis/psili after a letter is an elision mark (δ᾽, ἀλλ᾽):
    # store it as the ordinary apostrophe that the tokenizer treats as punctuation.
    text = text.replace("\u1fbd", "\u2019").replace("\u1fbf", "\u2019")
    text = " ".join(text.split())
    return unicodedata.normalize("NFC", text)
