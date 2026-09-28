"""Install a visually reviewed original illustration; never impersonate a museum source.

Usage: python scripts/install_illustration.py record.json
Record: {ids: [...], source: /absolute/generated.png, prompt: ..., review: ...}
The generation itself uses ChatGPT's built-in image tool, not a paid API script.
"""
import hashlib
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend/app/course_data/images"
OUT = ROOT / "frontend/public/course/illustrations"


def install(record):
    assert record.get("review"), "A subject/composition review is required"
    assert record.get("prompt"), "Preserve the generation prompt"
    docs = {p: json.loads(p.read_text()) for p in DATA.glob("manifest*.json")}
    known = {x["id"] for d in docs.values() for x in d["images"]}
    assert set(record["ids"]) <= known, "Unknown image ID"
    asset = record["ids"][0]
    assert all(c.isalnum() or c == "-" for c in asset), "Invalid asset ID"
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"{asset}.webp"
    with Image.open(record["source"]) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        image.thumbnail((1200, 900), Image.Resampling.LANCZOS)
        encoded = io.BytesIO()
        image.save(encoded, "WEBP", quality=82, method=6)
    payload = encoded.getvalue()
    assert len(payload) > 1000, "Image encoding failed"
    temporary = dest.with_suffix(".tmp")
    temporary.write_bytes(payload)
    temporary.replace(dest)
    relative = str(dest.relative_to(ROOT / "frontend/public"))
    provenance_path = DATA / "illustrations.json"
    provenance = json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
    for image_id in record["ids"]:
        provenance[image_id] = {
            "file": relative, "generator": "ChatGPT built-in image generation",
            "prompt": record["prompt"], "review": record["review"],
            "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
        }
    for path, doc in docs.items():
        changed = False
        for entry in doc["images"]:
            if entry["id"] in record["ids"]:
                entry.update(file=relative, license="Original AI illustration",
                    credit="Attic Reader · original AI-generated educational illustration; interpretive reconstruction, not an artifact photograph",
                    source_url=None)
                changed = True
        if changed:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print(f"Installed {relative}: {', '.join(record['ids'])}")


if __name__ == "__main__":
    install(json.loads(Path(sys.argv[1]).read_text()))
