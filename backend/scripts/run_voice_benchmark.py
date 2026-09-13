from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.greek import attic_ipa, normalize_polytonic
from app.tts.kokoro import KokoroAtticTTS, prepare_kokoro_phonemes
from app.tts.mms import MMSAncientGreekTTS
from app.tts.piper import PiperTTS, TTSUnavailable


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="../benchmarks/attic_benchmark.json")
    parser.add_argument("--out", default="../benchmark-output")
    parser.add_argument("--providers", nargs="+", default=["kokoro", "mms"])
    parser.add_argument(
        "--voices",
        nargs="+",
        default=None,
        help="Kokoro voices to render (one WAV per voice). Defaults to $KOKORO_VOICE.",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent.parent
    benchmark = (base / args.benchmark).resolve()
    out = (base / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = json.loads(benchmark.read_text(encoding="utf-8"))

    manifest = []
    for row in rows:
        greek = normalize_polytonic(row["text"])
        ipa = attic_ipa(greek)
        item = {**row, "ipa": ipa, "kokoro_phonemes": prepare_kokoro_phonemes(ipa), "audio": {}}
        print(f"\n[{row['id']}] {greek}\n  IPA: {ipa}")
        jobs: list[tuple[str, str | None]] = []
        for provider in args.providers:
            if provider == "kokoro" and args.voices:
                jobs.extend((provider, voice) for voice in args.voices)
            else:
                jobs.append((provider, None))
        for provider, voice in jobs:
            # Manifest keys are always the provider ID (success or error) so a
            # consumer can parse the manifest without special-casing failures.
            provider_id = {"kokoro": "kokoro-attic", "mms": "mms-grc", "piper": "piper"}.get(provider, provider)
            if voice:
                provider_id = f"{provider_id}__{voice}"
            try:
                if provider == "kokoro":
                    tts = KokoroAtticTTS()
                    if voice:
                        tts.voice = voice
                    audio = tts.synthesize(ipa)
                elif provider == "mms":
                    audio = MMSAncientGreekTTS().synthesize(greek)
                elif provider == "piper":
                    audio = PiperTTS().synthesize(ipa)
                else:
                    raise ValueError(provider)
                path = out / f"{row['id']}__{provider_id}.wav"
                path.write_bytes(audio)
                item["audio"][provider_id] = path.name
                print(f"  {provider_id}: {path.name}")
            except Exception as exc:
                item["audio"][provider_id] = {"error": str(exc)}
                print(f"  {provider_id}: ERROR: {exc}")
        manifest.append(item)

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
