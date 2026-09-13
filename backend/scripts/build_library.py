"""Build the reading library from Perseus Digital Library TEI editions.

Reads app/library_data/sources.json, fetches each TEI file from the PerseusDL
canonical-greekLit repository (or a local cache dir), resolves the requested
section refs, and writes app/library_data/<id>.json plus manifest.json.

    python scripts/build_library.py [--cache DIR] [--only ID ...]

Prints one line per passage (sentence count, first words, unknown Kokoro
symbols) so the result can be checked by eye before committing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.greek import normalize_polytonic, segment_sentences  # noqa: E402
from app.greek.g2p import attic_ipa  # noqa: E402
from app.tts.kokoro import prepare_kokoro_phonemes, unknown_kokoro_symbols  # noqa: E402

TEI = "{http://www.tei-c.org/ns/1.0}"
BREAK = "\ue000"  # private-use char (never whitespace): marks a speech boundary
DATA_DIR = BACKEND_ROOT / "app" / "library_data"


def element_text(el: ET.Element) -> str:
    """Text of a TEI element without editorial apparatus (notes, page breaks)."""
    parts: list[str] = []

    def walk(node: ET.Element) -> None:
        tag = node.tag.replace(TEI, "")
        if tag in {"note", "bibl", "pb", "milestone", "label"}:
            if node.tail:
                parts.append(node.tail)
            return
        if tag == "sp":
            # Each speech on its own line so the sentence splitter separates turns.
            parts.append(BREAK)
        if tag == "said":
            # Perseus Plato: <said who="#Σωκράτης">…</said>; rend="merge" continues
            # the same speaker's turn, so it gets neither a break nor a label.
            if node.get("rend") != "merge":
                who = (node.get("who") or "").lstrip("#").strip()
                parts.append(BREAK + (who + ": " if who else ""))
        if tag == "speaker":
            # Keep the speaker's name as a spoken label followed by a pause.
            parts.append((node.text or "").strip() + ": ")
            if node.tail:
                parts.append(node.tail)
            return
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
        if node.tail:
            parts.append(node.tail)

    if el.text:
        parts.append(el.text)
    for child in el:
        walk(child)
    # Source whitespace (including the XML's own line breaks) is collapsed;
    # only speech boundaries become real line breaks.
    joined = re.sub(r"\s+", " ", "".join(parts))
    lines = [line.strip() for line in joined.split(BREAK)]
    return "\n".join(line for line in lines if line)


def resolve_ref(root: ET.Element, ref: str) -> ET.Element:
    """Find the <div> reached by following ref parts ("1.1.2" or "1.327a") down
    the nested textpart divs. Each part matches a div's @n at that depth."""
    node = root.find(f".//{TEI}text/{TEI}body")
    if node is None:
        raise ValueError("no TEI body")
    for part in ref.split("."):
        candidates = [d for d in node.iter(f"{TEI}div") if d.get("n") == part and d is not node]
        # Prefer the shallowest match directly under the current node.
        direct = [d for d in node.findall(f"{TEI}div") if d.get("n") == part]
        if not direct:
            # Some editions wrap textparts in an edition <div>; look one level down.
            for wrapper in node.findall(f"{TEI}div"):
                direct = [d for d in wrapper.findall(f"{TEI}div") if d.get("n") == part]
                if direct:
                    break
        if not direct:
            if candidates:
                direct = [candidates[0]]
            else:
                raise ValueError(f"ref part {part!r} of {ref!r} not found")
        node = direct[0]
    return node


def build_passage(spec: dict, root: ET.Element) -> dict:
    # Sections are editorial units that often cut a sentence in half, so they
    # are joined with a space; only speech turns get their own line.
    pieces = []
    for ref in spec["refs"]:
        block = element_text(resolve_ref(root, ref))
        pieces.append("\n".join(normalize_polytonic(line) for line in block.split("\n") if line.strip()))
    text = " ".join(p for p in pieces if p)
    text = re.sub(r" *\n *", "\n", text).strip()
    limit = spec.get("max_sentences")
    if limit:
        sentences = segment_sentences(text)
        if len(sentences) > limit:
            text = text[: sentences[limit - 1].end]
    return {
        "id": spec["id"],
        "category": spec["category"],
        "level": spec["level"],
        "title": spec["title"],
        "author": spec["author"],
        "work": spec["work"],
        "ref": spec["ref"],
        "blurb": spec["blurb"],
        "dialect": "attic",
        "source": {
            "edition": "Perseus Digital Library, " + spec["urn"].rsplit(":", 1)[-1],
            "urn": spec["urn"],
            "license": "CC BY-SA 4.0",
            "url": "https://github.com/PerseusDL/canonical-greekLit/blob/master/data/" + spec["file"],
        },
        "text": text,
    }


def load_tei(spec: dict, cache: Path | None, raw_base: str) -> ET.Element:
    name = Path(spec["file"]).name
    if cache and (cache / name).exists():
        return ET.parse(cache / name).getroot()
    with urllib.request.urlopen(f"{raw_base}/{spec['file']}", timeout=120) as resp:  # noqa: S310
        data = resp.read()
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        (cache / name).write_bytes(data)
    return ET.fromstring(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=None, help="directory holding downloaded TEI files")
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()

    sources = json.loads((DATA_DIR / "sources.json").read_text("utf-8"))
    manifest: list[str] = []
    problems = 0
    for spec in sources["passages"]:
        if args.only and spec["id"] not in args.only:
            continue
        try:
            root = load_tei(spec, args.cache, sources["raw_base"])
            item = build_passage(spec, root)
        except Exception as exc:  # noqa: BLE001
            problems += 1
            print(f"FAIL {spec['id']}: {exc}")
            continue
        sentences = segment_sentences(item["text"])
        unknown = sorted({ch for s in sentences for ch in unknown_kokoro_symbols(prepare_kokoro_phonemes(attic_ipa(s.text)))})
        (DATA_DIR / f"{spec['id']}.json").write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", "utf-8")
        manifest.append(spec["id"])
        flag = "" if not unknown else f"  UNKNOWN SYMBOLS {unknown}"
        print(f"{spec['id']:16s} {len(sentences):2d} sent  {len(item['text']):4d} ch  {item['text'][:58]!r}{flag}")
        if unknown:
            problems += 1
    if not args.only:
        (DATA_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", "utf-8")
    print(f"\n{len(manifest)} passages written to {DATA_DIR}" + (f"; {problems} problem(s)" if problems else ""))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
