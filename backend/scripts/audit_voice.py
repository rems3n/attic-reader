#!/usr/bin/env python3
"""Generate a compact Ancient Greek pronunciation audit pack.

This is intentionally not a fluency benchmark.  Each clip isolates one or two
features that distinguish a Classical-oriented reading from Modern Greek or a
later merger.  The manifest includes our current learner-IPA expectation so a
human reviewer can compare the generated audio systematically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.greek import attic_ipa, normalize_polytonic
from app.tts.mms import MMSAncientGreekTTS
from app.tts.piper import PiperTTS, TTSUnavailable

CASES = [
    ("stops", "βίος, γένος, δῶρον"),
    ("eta-vs-iota", "ἡμέρα, ἱερός"),
    ("omega-vs-omicron", "δῶρον, λόγος"),
    ("upsilon", "Κῦρος, ὕδωρ"),
    ("ai-diphthong", "παῖς, αἰεί"),
    ("oi-diphthong", "οἶκος, οἶνος"),
    ("ei-ou", "εἶμι, οὐρανός"),
    ("au-eu", "αὐτός, εὖ"),
    ("aspirates", "θεός, φίλος, χρόνος"),
    ("rough-breathing", "ὁ, ἡ, ἥλιος"),
    ("gamma-nasal", "ἄγγελος, ἀνάγκη"),
    ("geminates", "θάλαττα, ἄλλος"),
    ("short-sentence", "ὁ Δικαιόπολις αὐτουργός ἐστιν."),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["mms", "piper"], default="mms")
    parser.add_argument("--out", default="voice-audit")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if args.provider == "mms":
        engine = MMSAncientGreekTTS()
        synth = lambda greek, ipa: engine.synthesize(greek)
    else:
        engine = PiperTTS()
        synth = lambda greek, ipa: engine.synthesize(ipa)

    manifest: list[dict[str, str]] = []
    for index, (feature, raw_text) in enumerate(CASES, start=1):
        greek = normalize_polytonic(raw_text)
        ipa = attic_ipa(greek)
        filename = f"{index:02d}-{feature}.wav"
        row = {
            "feature": feature,
            "greek": greek,
            "expected_learner_ipa": ipa,
            "audio": filename,
        }
        manifest.append(row)
        print(f"[{index:02d}/{len(CASES)}] {feature}: {greek} -> {ipa}")
        try:
            audio = synth(greek, ipa)
        except TTSUnavailable as exc:
            print(f"ERROR: {exc}")
            (out / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return 2
        (out / filename).write_bytes(audio)

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {len(manifest)} clips + manifest to {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
