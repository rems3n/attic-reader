"""Read-only editorial image catalog, joined to actual course references."""
from collections import Counter
from functools import lru_cache

from . import data


def _references(node, path="", context=""):
    if isinstance(node, dict):
        context = str(node.get("prompt") or node.get("text") or node.get("title") or context)
        if node.get("sentences"):
            context = " ".join(s.get("text", "") for s in node["sentences"] if isinstance(s, dict))
        for key, value in node.items():
            location = f"{path}.{key}".strip(".")
            if (key in {"image", "cover", "pic", "diagram"} or
                    (key == "value" and node.get("kind") == "pic")) and isinstance(value, str):
                yield value, location, context[:600]
            elif isinstance(value, (dict, list)):
                yield from _references(value, location, context)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _references(value, f"{path}[{index + 1}]", context)


def _collection(stem):
    key = stem.removeprefix("manifest-")
    labels = {"manifest": "Opening · Units 0–1", "diagrams": "Grammar diagrams",
              "myth": "Mythology", "phil": "Philosophy", "hist": "History", "pol": "Politics"}
    return {"id": key, "label": labels.get(key, f"Unit {key[1:]}" if key.startswith("u") else key)}


@lru_cache(maxsize=1)
def image_catalog():
    root = data.DATA_DIR / "images"
    inventory = {i["id"]: i for i in data._read(root / "inventory.json")["images"]}
    originals = data._read(root / "illustrations.json")
    verified = data._read(root / "verified.json")
    entries = {e["id"]: e for e in data.all_entries()}
    images = {}
    for path in sorted(root.glob("manifest*.json")):
        for image in data._read(path)["images"]:
            ready = image.get("svg") or (image.get("file") and image["license"] != "placeholder")
            inv = inventory.get(image["id"], {})
            source = verified.get(image["id"], {})
            candidate = None
            if not ready and inv.get("status") == "downloaded_needs_review":
                candidate = {"file": f"course/pics/{image['id']}.webp",
                             "source_url": source.get("source_url"),
                             "credit": source.get("credit", ""), "license": source.get("license", "")}
            images[image["id"]] = {**image, "status": "completed" if ready else "remaining",
                "medium": "diagram" if image.get("svg") else "illustration" if image["license"] == "Original AI illustration" else "photo" if ready else "pending",
                "collection": _collection(path.stem), "vocabulary": [], "usages": [],
                "provenance": originals.get(image["id"]), "candidate": candidate,
                "pipeline_status": inv.get("status", "unknown")}
    for folder in ("lessons", "tests", "texts"):
        for path in sorted((data.DATA_DIR / folder).glob("*.json")):
            doc = data._read(path)
            if not isinstance(doc, dict):
                continue
            doc_id = str(doc.get("id", path.stem))
            title = doc.get("title_en") or doc.get("title") or doc_id
            href = f"/learn/lesson/{doc_id}" if folder == "lessons" else None
            for image_id, location, context in _references(doc):
                if image_id not in images:
                    continue
                images[image_id]["usages"].append({"source": folder, "id": doc_id,
                    "title": title, "location": location, "context": context, "href": href})
            for word in doc.get("vocab", []):
                if not isinstance(word, dict) or word.get("pic") not in images:
                    continue
                entry = entries.get(word.get("id"))
                if entry:
                    target = images[word["pic"]]["vocabulary"]
                    if not any(w["id"] == entry["id"] for w in target):
                        target.append({"id": entry["id"], "lemma": entry["lemma"],
                                       "definition": entry.get("definition") or entry.get("short", "")})
    rows = list(images.values())
    counts = Counter(i["status"] for i in rows)
    return {"images": rows, "summary": {"total": len(rows), **counts,
        "illustrations": sum(i["medium"] == "illustration" for i in rows),
        "photos": sum(i["medium"] == "photo" for i in rows),
        "diagrams": sum(i["medium"] == "diagram" for i in rows),
        "unique_raster_files": len({i["file"] for i in rows if i["status"] == "completed" and i.get("file")}),
        "candidates": sum(bool(i["candidate"]) for i in rows)}}
