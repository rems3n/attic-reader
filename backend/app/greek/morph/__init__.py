"""Deterministic Classical Attic morphology (paradigm generation).

Greek → forms only; nothing here knows about the TTS provider. The engine is
rule-based and every class is checked against hand-written gold tables in
tests/test_morph_*.py. Where a word is irregular it is spelled out in
`irregular.py` rather than patched into the rules.
"""

from .accent import accentuate, persistent, recessive, strip_accent, syllables  # noqa: F401
from .nominal import decline, decline_entry  # noqa: F401
