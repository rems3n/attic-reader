from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass
from typing import Iterator

from .espeak import EspeakAncientGreekTTS
from .mms import MMSAncientGreekTTS
from .kokoro import KokoroAtticTTS
from .piper import PiperTTS, TTSUnavailable


@dataclass(frozen=True)
class ProviderStatus:
    id: str
    name: str
    quality: str
    available: bool
    enabled: bool
    note: str


def _truthy(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def provider_statuses() -> list[dict[str, object]]:
    kokoro = KokoroAtticTTS()
    kokoro_ok, kokoro_note = kokoro.is_available()
    if kokoro_ok:
        kokoro_note = f"{kokoro_note}; model {KokoroAtticTTS.warm_state()}"

    mms = MMSAncientGreekTTS()
    mms_ok, mms_note = mms.is_available()

    piper = PiperTTS()
    piper_ok = bool(piper.model and os.path.exists(piper.model))
    piper_note = (
        "custom raw-phoneme neural path configured"
        if piper_ok
        else "Set PIPER_MODEL to a compatible neural voice"
    )

    espeak_bin = shutil.which(os.getenv("ESPEAK_COMMAND", "espeak").split()[0])
    espeak_ok = bool(espeak_bin)
    espeak_enabled = _truthy("ALLOW_ESPEAK_FALLBACK", default=False)

    rows = [
        ProviderStatus(
            id="kokoro-attic",
            name="Kokoro · direct Classical Attic phonemes",
            quality="neural",
            available=kokoro_ok,
            enabled=_truthy("ENABLE_KOKORO", default=True),
            note=kokoro_note,
        ),
        ProviderStatus(
            id="mms-grc",
            name="Meta MMS · Ancient Greek neural (Modern-Greek phonology; comparison only)",
            quality="neural",
            available=mms_ok,
            enabled=_truthy("ENABLE_MMS", default=False),
            note=mms_note,
        ),
        ProviderStatus(
            id="piper",
            name="Piper · custom Attic phonemes",
            quality="neural",
            available=piper_ok,
            enabled=True,
            note=piper_note,
        ),
        ProviderStatus(
            id="espeak-grc",
            name="eSpeak NG · Ancient Greek diagnostic",
            quality="robotic",
            available=espeak_ok,
            enabled=espeak_enabled,
            note=(
                "diagnostic fallback enabled"
                if espeak_enabled
                else "installed but intentionally disabled for learner playback"
            ),
        ),
    ]
    return [asdict(row) for row in rows]


_NO_VOICE_MESSAGE = (
    " | eSpeak is intentionally disabled because its voice is too robotic; "
    "set ALLOW_ESPEAK_FALLBACK=true only for diagnostics."
)


def _has_greek(text: str) -> bool:
    return any("Ͱ" <= ch <= "Ͽ" or "ἀ" <= ch <= "῿" for ch in text)


def synthesize_best(greek_text: str, attic_ipa: str, speed: float | None = None) -> tuple[bytes, str]:
    """Try natural neural providers first; robotic eSpeak is opt-in only.

    ``speed`` is a learner multiplier (1.0 = the provider's default pace). Only
    Kokoro honours it natively today; the other providers ignore it.
    """

    errors: list[str] = []

    if _truthy("ENABLE_KOKORO", default=True):
        try:
            return KokoroAtticTTS().synthesize(attic_ipa, speed=speed), "kokoro-attic"
        except TTSUnavailable as exc:
            errors.append(f"Kokoro: {exc}")

    if _truthy("ENABLE_MMS", default=False):
        try:
            return MMSAncientGreekTTS().synthesize(greek_text), "mms-grc"
        except TTSUnavailable as exc:
            errors.append(f"MMS: {exc}")

    try:
        return PiperTTS().synthesize(attic_ipa), "piper"
    except TTSUnavailable as exc:
        errors.append(f"Piper: {exc}")

    if _truthy("ALLOW_ESPEAK_FALLBACK", default=False):
        try:
            return EspeakAncientGreekTTS().synthesize(greek_text), "espeak-grc"
        except TTSUnavailable as exc:
            errors.append(f"eSpeak: {exc}")

    raise TTSUnavailable(
        "No learner-quality neural voice is currently available. "
        + " | ".join(errors)
        + _NO_VOICE_MESSAGE
    )


def synthesize_sentences_stream(
    sentences: list[str], ipas: list[str], speed: float | None = None
) -> tuple[str, Iterator[bytes | None]]:
    """Like :func:`synthesize_sentences` but yields clips as they are rendered.

    Returns ``(provider_id, iterator)``. The provider is chosen (and its model
    loaded) before the first clip so the caller can announce it up front.
    """
    if len(sentences) != len(ipas):
        raise ValueError("sentences and ipas must align")

    if _truthy("ENABLE_KOKORO", default=True):
        kokoro = KokoroAtticTTS()
        try:
            kokoro._load()
        except TTSUnavailable:
            pass
        else:
            return "kokoro-attic", kokoro.iter_synthesize(ipas, speed=speed)

    clips, provider = synthesize_sentences(sentences, ipas, speed=speed)
    return provider, iter(clips)


def synthesize_sentences(
    sentences: list[str], ipas: list[str], speed: float | None = None
) -> tuple[list[bytes | None], str]:
    """Render one clip per sentence with a single provider.

    Returns ``(clips, provider_id)``; a clip is ``None`` for a sentence with
    nothing pronounceable (punctuation only, Latin-only, …). The whole batch
    comes from one provider so playback is consistent across sentences.
    """

    if len(sentences) != len(ipas):
        raise ValueError("sentences and ipas must align")

    errors: list[str] = []

    if _truthy("ENABLE_KOKORO", default=True):
        try:
            return KokoroAtticTTS().synthesize_many(ipas, speed=speed), "kokoro-attic"
        except TTSUnavailable as exc:
            errors.append(f"Kokoro: {exc}")

    def _per_sentence(render, inputs: list[str]) -> list[bytes | None]:
        # Silence is decided on the Greek sentence (the IPA of a Latin-only or
        # punctuation-only sentence contains no Greek letters either way).
        return [
            render(item) if _has_greek(sentence) else None
            for sentence, item in zip(sentences, inputs)
        ]

    if _truthy("ENABLE_MMS", default=False):
        try:
            mms = MMSAncientGreekTTS()
            return _per_sentence(mms.synthesize, sentences), "mms-grc"
        except TTSUnavailable as exc:
            errors.append(f"MMS: {exc}")

    try:
        piper = PiperTTS()
        return _per_sentence(piper.synthesize, ipas), "piper"
    except TTSUnavailable as exc:
        errors.append(f"Piper: {exc}")

    if _truthy("ALLOW_ESPEAK_FALLBACK", default=False):
        try:
            espeak = EspeakAncientGreekTTS()
            return _per_sentence(espeak.synthesize, sentences), "espeak-grc"
        except TTSUnavailable as exc:
            errors.append(f"eSpeak: {exc}")

    raise TTSUnavailable(
        "No learner-quality neural voice is currently available. "
        + " | ".join(errors)
        + _NO_VOICE_MESSAGE
    )
