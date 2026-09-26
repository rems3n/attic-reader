"""Source, verify and process the course's Creative Commons images.

The course ships placeholder image records (cream panel + Greek caption).
This script turns a row in ``course_data/images/sources.csv`` (or a
track's ``sources-<track>.csv``) into a real
picture with a verified licence and fills the matching manifest record.

    python scripts/build_images.py report            # ids still without a row / a file
    python scripts/build_images.py resolve           # search:… refs → concrete object ids
    python scripts/build_images.py verify            # licence + image URL from the source API
    python scripts/build_images.py fetch             # download originals into the cache
    python scripts/build_images.py process           # crop, pad, grade, WebP ≤ 60 KB
    python scripts/build_images.py manifest          # write file/credit/licence into manifest*.json
    python scripts/build_images.py all               # resolve → verify → fetch → process → manifest
    python scripts/build_images.py … --only kerameus agora-view   # a subset of ids

Needs network access (museum APIs); the Claude sandbox cannot run it, so
run it locally or in CI. Nothing here is required at app runtime.

CSV columns (``sources.csv``):

    id        manifest image id (must already exist in a manifest*.json)
    source    met | cma | aic | si | commons | manual
    ref       object id (met/cma/aic/si), "File:…" (commons), a URL (manual),
              or "search:<query>|<title regex>" (met/cma/aic/commons) —
              `resolve` picks the first public-domain hit whose title matches
              and records it in resolved.json so the choice is stable and
              reviewable
    license   required for manual; for the others the API's answer wins and a
              non-CC answer fails verification
    credit    required for manual; else built from the API (artist · museum)
    crop      "x,y,w,h" as fractions of the source image (0–1), or empty
    aspect    "3:2" (default) or "1:1" (picture dictionary)
    notes     free text

Accepted licences: CC0, Public domain, CC BY 1.0–4.0, CC BY-SA 1.0–4.0.
Anything else (CC BY-NC…, "all rights reserved", unknown) is refused.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app" / "course_data" / "images"
SOURCES = DATA / "sources.csv"
RESOLVED = DATA / "resolved.json"
VERIFIED = DATA / "verified.json"
CACHE = ROOT / ".image-cache"
OUT_DIR = ROOT.parent / "frontend" / "public" / "course" / "pics"
PUBLIC_PREFIX = "course/pics"

CREAM = (0xFF, 0xF3, 0xD6)
PAD = 0.12
MAX_BYTES = 60 * 1024
WIDTHS = {"3:2": (900, 600), "1:1": (720, 720)}
USER_AGENT = "attic-reader-image-pass/1 (https://github.com/rems3n/attic-reader)"

ACCEPTED = re.compile(r"^(cc0( 1\.0)?|public domain|pd( [a-z0-9 ]+)?|cc by( sa)?( [1-4]\.0)?)$", re.I)


# ------------------------------------------------------------------ helpers

def license_ok(text: str | None) -> bool:
    """True for CC0 / public domain / CC BY / CC BY-SA (any version)."""
    if not text:
        return False
    t = text.strip().replace("Attribution-ShareAlike", "BY SA").replace("ShareAlike", "SA").replace("Attribution", "BY").replace("Creative Commons", "CC")
    t = re.sub(r"\s+", " ", re.sub(r"[-_]", " ", t))
    return bool(ACCEPTED.match(t))


def parse_crop(text: str | None) -> tuple[float, float, float, float] | None:
    """'x,y,w,h' fractions → tuple, or None. Values are clamped to the image."""
    if not text or not text.strip():
        return None
    parts = [float(p) for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError(f"crop needs 4 numbers: {text!r}")
    x, y, w, h = parts
    if not (0 <= x < 1 and 0 <= y < 1 and 0 < w <= 1 and 0 < h <= 1):
        raise ValueError(f"crop fractions out of range: {text!r}")
    return (x, y, min(w, 1 - x), min(h, 1 - y))


def read_sources(only: set[str] | None = None) -> list[dict]:
    if not SOURCES.exists():
        sys.exit(f"missing {SOURCES}")
    rows = []
    # sources.csv plus sources-<track>.csv (same columns)
    for path in [SOURCES, *sorted(SOURCES.parent.glob("sources-*.csv"))]:
        with path.open(encoding="utf-8", newline="") as f:
            rows += [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    rows = [r for r in rows if r.get("id") and not r["id"].startswith("#")]
    if only:
        rows = [r for r in rows if r["id"] in only]
    return rows


FAILURES = DATA / "failures.json"
_failed: dict[str, dict] = {}


def fail(image_id: str, step: str, reason: str) -> None:
    """Print a failure and remember it for failures.json (the first failing
    step per image is the one to fix)."""
    print(f"✗ {image_id}: {reason}")
    _failed.setdefault(image_id, {"step": step, "reason": reason})


def write_failures(rows: list[dict]) -> None:
    """failures.json: every row that did not make it to a finished picture,
    with the step and reason, plus its source row — push it so the rows can
    be fixed."""
    by_id = {r["id"]: r for r in rows}
    old = load_json(FAILURES, {}) if FAILURES.exists() else {}
    done = {i for i in by_id if i not in _failed}
    merged = {k: v for k, v in old.items() if k not in done}
    for i, f in _failed.items():
        merged[i] = {**f, "source": by_id.get(i, {}).get("source"), "ref": by_id.get(i, {}).get("ref")}
    save_json(FAILURES, dict(sorted(merged.items())))
    print(f"\n{len(merged)} images still failing → {FAILURES.relative_to(ROOT.parent)}")


def load_json(path: Path, default):
    return json.loads(path.read_text("utf-8")) if path.exists() else default


def save_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", "utf-8")


def manifests() -> dict[Path, dict]:
    return {p: load_json(p, {"images": []}) for p in sorted(DATA.glob("manifest*.json"))}


def manifest_records() -> dict[str, tuple[Path, dict]]:
    out: dict[str, tuple[Path, dict]] = {}
    for path, doc in manifests().items():
        for img in doc["images"]:
            out[img["id"]] = (path, img)
    return out


def _backoff(exc: Exception, attempt: int) -> float:
    """Rate limits (429) and bot walls (403, the Met's CDN) need a longer pause."""
    code = getattr(exc, "code", None)
    return (10.0 if code in (403, 429) else 1.5) * (attempt + 1)


def http_json(url: str, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 — retry then raise
            if attempt == retries - 1 or getattr(exc, "code", None) == 404:
                raise
            time.sleep(_backoff(exc, attempt))
    raise RuntimeError("unreachable")


def http_bytes(url: str, retries: int = 4) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1 or getattr(exc, "code", None) == 404:
                raise
            time.sleep(_backoff(exc, attempt))
    raise RuntimeError("unreachable")


# ------------------------------------------------------------------ sources
#
# Each source returns {"ok", "license", "credit", "image_url", "source_url",
# "title", "reason"}; `resolve_search` turns a search: ref into an object id.

def met_verify(ref: str) -> dict:
    obj = http_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{ref}")
    ok = bool(obj.get("isPublicDomain")) and bool(obj.get("primaryImage"))
    artist = obj.get("artistDisplayName") or obj.get("culture") or ""
    return {
        "ok": ok,
        "license": "CC0" if obj.get("isPublicDomain") else "not open access",
        "credit": " · ".join(p for p in [obj.get("title", ""), artist, "The Metropolitan Museum of Art (Open Access)"] if p),
        "image_url": obj.get("primaryImage"),
        "source_url": obj.get("objectURL"),
        "title": obj.get("title", ""),
        "match_text": " ".join(str(x) for x in [obj.get("objectName"), obj.get("classification"), obj.get("culture"), obj.get("period"), " ".join(t.get("term", "") for t in obj.get("tags") or [])] if x),
        "reason": None if ok else "isPublicDomain false or no image",
    }


def met_search(query: str) -> list[str]:
    q = urllib.parse.quote(query)
    # departmentId 13 = Greek and Roman Art: the course wants Greek objects only
    res = http_json(f"https://collectionapi.metmuseum.org/public/collection/v1/search?departmentId=13&q={q}&hasImages=true&isPublicDomain=true")
    return [str(i) for i in (res.get("objectIDs") or [])[:40]]


def cma_verify(ref: str) -> dict:
    d = http_json(f"https://openaccess-api.clevelandart.org/api/artworks/{ref}")["data"]
    lic = d.get("share_license_status", "")
    web = ((d.get("images") or {}).get("web") or {}).get("url")
    ok = lic.upper() == "CC0" and bool(web)
    who = ", ".join(c.get("description", "") for c in d.get("creators", []) if c.get("description"))
    return {
        "ok": ok,
        "license": lic or "unknown",
        "credit": " · ".join(p for p in [d.get("title", ""), who, "The Cleveland Museum of Art (Open Access)"] if p),
        "image_url": web,
        "source_url": d.get("url"),
        "title": d.get("title", ""),
        "match_text": " ".join(str(x) for x in [d.get("type"), d.get("culture"), d.get("technique"), d.get("description")] if x),
        "reason": None if ok else f"share_license_status={lic!r}",
    }


def cma_search(query: str) -> list[str]:
    q = urllib.parse.quote(query)
    res = http_json(f"https://openaccess-api.clevelandart.org/api/artworks/?q={q}&cc0=1&has_image=1&limit=40&department=Greek%20and%20Roman%20Art")
    return [str(d["id"]) for d in res.get("data", [])]


def aic_verify(ref: str) -> dict:
    d = http_json(f"https://api.artic.edu/api/v1/artworks/{ref}?fields=id,title,image_id,is_public_domain,credit_line,artist_display")["data"]
    ok = bool(d.get("is_public_domain")) and bool(d.get("image_id"))
    return {
        "ok": ok,
        "license": "CC0" if d.get("is_public_domain") else "not public domain",
        "credit": " · ".join(p for p in [d.get("title", ""), (d.get("artist_display") or "").split("\n")[0], "The Art Institute of Chicago (CC0)"] if p),
        "image_url": f"https://www.artic.edu/iiif/2/{d['image_id']}/full/1686,/0/default.jpg" if d.get("image_id") else None,
        "source_url": f"https://www.artic.edu/artworks/{d['id']}",
        "title": d.get("title", ""),
        "reason": None if ok else "is_public_domain false or no image",
    }


def aic_search(query: str) -> list[str]:
    q = urllib.parse.quote(query)
    res = http_json(f"https://api.artic.edu/api/v1/artworks/search?q={q}&query[term][is_public_domain]=true&limit=40&fields=id")
    return [str(d["id"]) for d in res.get("data", [])]


def si_verify(ref: str) -> dict:
    key = os.environ.get("SMITHSONIAN_API_KEY")
    if not key:
        return {"ok": False, "reason": "set SMITHSONIAN_API_KEY (free key from api.data.gov)"}
    d = http_json(f"https://api.si.edu/openaccess/api/v1.0/content/{urllib.parse.quote(ref)}?api_key={key}")["response"]
    dnr = d.get("content", {}).get("descriptiveNonRepeating", {})
    media = (dnr.get("online_media") or {}).get("media") or []
    cc0 = [m for m in media if (m.get("usage") or {}).get("access") == "CC0" and m.get("content")]
    ok = bool(cc0)
    return {
        "ok": ok,
        "license": "CC0" if ok else "not CC0",
        "credit": " · ".join(p for p in [d.get("title", ""), dnr.get("data_source", "Smithsonian Institution")] if p),
        "image_url": cc0[0]["content"] if ok else None,
        "source_url": dnr.get("record_link"),
        "title": d.get("title", ""),
        "reason": None if ok else "no CC0 media",
    }


def commons_verify(ref: str) -> dict:
    title = ref if ref.startswith("File:") else f"File:{ref}"
    q = urllib.parse.urlencode({"action": "query", "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": "1800", "titles": title, "format": "json"})
    pages = http_json(f"https://commons.wikimedia.org/w/api.php?{q}")["query"]["pages"]
    page = next(iter(pages.values()))
    info = (page.get("imageinfo") or [{}])[0]
    meta = {k: re.sub(r"<[^>]+>", "", (v or {}).get("value", "")).strip() for k, v in (info.get("extmetadata") or {}).items()}
    lic = meta.get("LicenseShortName") or meta.get("License") or ""
    ok = license_ok(lic) and bool(info.get("url"))
    artist = meta.get("Artist") or meta.get("Credit") or "unknown author"
    return {
        "ok": ok,
        "license": lic or "unknown",
        "credit": f"{meta.get('ObjectName') or title[5:]} · {artist} · Wikimedia Commons ({lic})",
        "image_url": info.get("thumburl") or info.get("url"),
        "source_url": info.get("descriptionurl"),
        "title": title,
        "match_text": " ".join(meta.get(k, "") for k in ("ObjectName", "ImageDescription", "Categories")),
        "reason": None if ok else f"licence {lic!r}",
    }


def commons_search(query: str) -> list[str]:
    q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query, "srnamespace": "6", "srlimit": "40", "format": "json"})
    res = http_json(f"https://commons.wikimedia.org/w/api.php?{q}")
    return [r["title"] for r in res["query"]["search"]]


def manual_verify(row: dict) -> dict:
    lic, credit, url = row.get("license"), row.get("credit"), row.get("ref")
    ok = license_ok(lic) and bool(credit) and bool(url)
    return {"ok": ok, "license": lic, "credit": credit, "image_url": url, "source_url": row.get("notes") or url, "title": row["id"], "reason": None if ok else "manual rows need an accepted license, a credit and an image URL"}


VERIFIERS = {"met": met_verify, "cma": cma_verify, "aic": aic_verify, "si": si_verify, "commons": commons_verify}
SEARCHERS = {"met": met_search, "cma": cma_search, "aic": aic_search, "commons": commons_search}


# ------------------------------------------------------------------ commands

def cmd_report(rows: list[dict]) -> int:
    records = manifest_records()
    by_id = {r["id"]: r for r in rows}
    placeholders = {i: img for i, (_, img) in records.items() if img.get("license") == "placeholder"}
    diagrams = [i for i, img in placeholders.items() if img.get("kind") == "diagram"]
    missing_row = [i for i, img in placeholders.items() if img.get("kind") != "diagram" and i not in by_id]
    unknown = [r["id"] for r in rows if r["id"] not in records]
    no_file = [i for i, (_, img) in records.items() if i in by_id and (not img.get("file") or not (ROOT.parent / "frontend" / "public" / img["file"]).exists())]
    done = [i for i, (_, img) in records.items() if img.get("license") != "placeholder" and img.get("file")]
    print(f"{len(records)} image records · {len(rows)} source rows · {len(done)} finished")
    if unknown:
        print(f"\nrows whose id is in no manifest ({len(unknown)}): " + ", ".join(unknown))
    if no_file:
        print(f"\nrows not yet processed ({len(no_file)}): " + ", ".join(no_file))
    if missing_row:
        print(f"\nplaceholders without a source row ({len(missing_row)}):")
        for i in missing_row:
            img = placeholders[i]
            print(f"  {i:26} {img.get('kind', ''):11} {img.get('alt_en', '')}")
    if diagrams:
        print(f"\ndiagrams to draw as our own SVG, CC BY-SA ({len(diagrams)}): " + ", ".join(diagrams))
    return 0


# When a search finds nothing: shorter queries (drop words from the end, keep
# two), then the same queries at another source. Every hit is still licence-
# checked and must match the row's title pattern.
FALLBACK = {"met": ["cma", "commons"], "cma": ["met", "commons"], "aic": ["met", "commons"], "commons": ["met", "cma"]}
MAX_CANDIDATES = 25


def relaxed_queries(query: str) -> list[str]:
    words = query.split()
    out = [query] + [" ".join(words[:n]) for n in range(len(words) - 1, 1, -1)]
    return list(dict.fromkeys(q for q in out if q))


def find_hit(source: str, query: str, pattern: str, fallback: bool = True) -> tuple[str, str, str] | None:
    """(source, object id, title) of the first open-access hit, or None."""
    rx = re.compile(pattern, re.I) if pattern else None
    sources = [source] + (FALLBACK.get(source, []) if fallback else [])
    for src in sources:
        if src not in SEARCHERS:
            continue
        seen: set[str] = set()
        for q in relaxed_queries(query):
            try:
                candidates = SEARCHERS[src](q)
            except Exception:  # noqa: BLE001 — try the next query / source
                continue
            for cand in [c for c in candidates if c not in seen][:MAX_CANDIDATES]:
                seen.add(cand)
                try:
                    info = VERIFIERS[src](cand)
                except Exception:  # noqa: BLE001
                    continue
                text = f"{info.get('title', '')} {info.get('match_text', '')}"
                if info.get("ok") and license_ok(info.get("license")) and (rx is None or rx.search(text)):
                    return src, cand, info.get("title", "")
    return None


def cmd_resolve(rows: list[dict], fallback: bool = True) -> int:
    resolved = load_json(RESOLVED, {})
    failed: list[str] = []
    for row in rows:
        ref, source = row["ref"], row["source"]
        if not ref.startswith("search:"):
            continue
        if row["id"] in resolved and resolved[row["id"]].get("ref") == ref:
            continue
        query, _, pattern = ref[7:].partition("|")
        if source not in SEARCHERS:
            fail(row["id"], "resolve", f"no search for source {source!r}")
            failed.append(row["id"])
            continue
        hit = find_hit(source, query.strip(), pattern.strip(), fallback)
        if not hit:
            fail(row["id"], "resolve", f"no open-access hit for {query.strip()!r} matching {pattern.strip()!r}")
            failed.append(row["id"])
            continue
        src, obj, title = hit
        resolved[row["id"]] = {"ref": ref, "source": src, "object": obj, "title": title}
        note = f" (fallback from {source})" if src != source else ""
        print(f"✓ {row['id']}: {src} {obj} — {title}{note}")
        save_json(RESOLVED, resolved)  # keep progress if the run is interrupted
    save_json(RESOLVED, resolved)
    if failed:
        print(f"\n{len(failed)} unresolved: {' '.join(failed)}")
        print("Loosen the query or title pattern in the sources file, or give a File:/object id, or a manual row.")
    return 1 if failed else 0


def concrete_ref(row: dict, resolved: dict) -> str | None:
    return concrete_source_ref(row, resolved)[1]


def concrete_source_ref(row: dict, resolved: dict) -> tuple[str, str | None]:
    """(source, object id) for a row; a search row takes the source its hit came from."""
    if row["ref"].startswith("search:"):
        hit = resolved.get(row["id"])
        if hit and hit.get("ref") == row["ref"]:
            return hit.get("source", row["source"]), hit["object"]
        return row["source"], None
    return row["source"], row["ref"]


def cmd_verify(rows: list[dict]) -> int:
    resolved = load_json(RESOLVED, {})
    verified = load_json(VERIFIED, {})
    failures = 0
    for row in rows:
        source, ref = concrete_source_ref(row, resolved)
        if ref is None:
            fail(row["id"], "verify", f"unresolved search ref (run resolve)")
            failures += 1
            continue
        try:
            info = manual_verify(row) if source == "manual" else VERIFIERS[source](ref)
        except KeyError:
            info = {"ok": False, "reason": f"unknown source {source!r}"}
        except Exception as exc:  # noqa: BLE001
            info = {"ok": False, "reason": f"API error: {exc}"}
        if not info.get("ok"):
            fail(row["id"], "verify", f"{info.get('reason')}")
            failures += 1
            verified.pop(row["id"], None)
            continue
        if not license_ok(info.get("license")):
            fail(row["id"], "verify", f"licence {info.get('license')!r} not accepted")
            failures += 1
            verified.pop(row["id"], None)
            continue
        verified[row["id"]] = {"source": source, "ref": ref, **{k: info.get(k) for k in ("license", "credit", "image_url", "source_url", "title")}}
        print(f"✓ {row['id']}: {info['license']} — {info['credit'][:80]}")
    save_json(VERIFIED, verified)
    return 1 if failures else 0


def cache_path(image_id: str, url: str) -> Path:
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
    return CACHE / f"{image_id}-{hashlib.sha1(url.encode()).hexdigest()[:10]}{ext}"


def cmd_fetch(rows: list[dict]) -> int:
    verified = load_json(VERIFIED, {})
    CACHE.mkdir(exist_ok=True)
    failures = 0
    for row in rows:
        v = verified.get(row["id"])
        if not v:
            fail(row["id"], "fetch", f"not verified")
            failures += 1
            continue
        target = cache_path(row["id"], v["image_url"])
        if target.exists():
            continue
        try:
            target.write_bytes(http_bytes(v["image_url"]))
            print(f"✓ {row['id']}: {target.stat().st_size // 1024} KB")
        except Exception as exc:  # noqa: BLE001
            fail(row["id"], "fetch", f"download failed: {exc}")
            failures += 1
    return 1 if failures else 0


def process_image(data: bytes, crop: tuple[float, float, float, float] | None, aspect: str, grade: bool = True) -> bytes:
    """Crop → fit into the aspect box with a cream field and 12 % padding →
    mild warm grade → WebP under MAX_BYTES."""
    from PIL import Image, ImageEnhance, ImageOps

    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "transparency" in im.info else "RGB")
    w, h = im.size
    if crop:
        x, y, cw, ch = crop
        im = im.crop((round(x * w), round(y * h), round((x + cw) * w), round((y + ch) * h)))
    box_w, box_h = WIDTHS.get(aspect, WIDTHS["3:2"])
    inner_w, inner_h = round(box_w * (1 - 2 * PAD)), round(box_h * (1 - 2 * PAD))
    im.thumbnail((inner_w, inner_h), Image.LANCZOS)
    canvas = Image.new("RGB", (box_w, box_h), CREAM)
    ox, oy = (box_w - im.width) // 2, (box_h - im.height) // 2
    if im.mode == "RGBA":
        canvas.paste(im, (ox, oy), im)
    else:
        canvas.paste(im, (ox, oy))
    if grade:
        # a touch less saturation and a faint warm cast, so photographs from
        # many museums sit together on the cream panels
        canvas = ImageEnhance.Color(canvas).enhance(0.92)
        warm = Image.new("RGB", canvas.size, (0xF4, 0xB9, 0x42))
        canvas = Image.blend(canvas, warm, 0.035)
    for quality in (86, 80, 74, 68, 60, 52, 44):
        buf = io.BytesIO()
        canvas.save(buf, "WEBP", quality=quality, method=6)
        if buf.tell() <= MAX_BYTES:
            return buf.getvalue()
    return buf.getvalue()


def cmd_process(rows: list[dict], grade: bool = True) -> int:
    verified = load_json(VERIFIED, {})
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = manifest_records()
    failures = 0
    for row in rows:
        v = verified.get(row["id"])
        if not v:
            fail(row["id"], "process", f"not verified")
            failures += 1
            continue
        src = cache_path(row["id"], v["image_url"])
        if not src.exists():
            fail(row["id"], "process", f"not fetched")
            failures += 1
            continue
        kind = records.get(row["id"], (None, {}))[1].get("kind")
        aspect = row.get("aspect") or ("1:1" if kind == "dictionary" else "3:2")
        try:
            out = process_image(src.read_bytes(), parse_crop(row.get("crop")), aspect, grade)
        except Exception as exc:  # noqa: BLE001
            fail(row["id"], "process", f"{exc}")
            failures += 1
            continue
        (OUT_DIR / f"{row['id']}.webp").write_bytes(out)
        flag = "" if len(out) <= MAX_BYTES else "  (over 60 KB even at low quality — tighten the crop)"
        print(f"✓ {row['id']}: {len(out) // 1024} KB {aspect}{flag}")
    return 1 if failures else 0


def cmd_manifest(rows: list[dict]) -> int:
    verified = load_json(VERIFIED, {})
    docs = manifests()
    records = {img["id"]: (path, img) for path, doc in docs.items() for img in doc["images"]}
    changed: set[Path] = set()
    failures = 0
    for row in rows:
        v = verified.get(row["id"])
        webp = OUT_DIR / f"{row['id']}.webp"
        if not v or not webp.exists():
            fail(row["id"], "manifest", f"needs verify + process first")
            failures += 1
            continue
        if row["id"] not in records:
            fail(row["id"], "manifest", f"no manifest record (add one with alt text first)")
            failures += 1
            continue
        path, img = records[row["id"]]
        img.update({"file": f"{PUBLIC_PREFIX}/{row['id']}.webp", "license": v["license"], "credit": v["credit"], "source_url": v["source_url"]})
        changed.add(path)
    for path in changed:
        path.write_text(json.dumps(docs[path], ensure_ascii=False, indent=1) + "\n", "utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["report", "resolve", "verify", "fetch", "process", "manifest", "all"])
    ap.add_argument("--only", nargs="*", help="image ids to limit the run to")
    ap.add_argument("--no-grade", action="store_true", help="skip the colour grade")
    ap.add_argument("--no-fallback", action="store_true", help="resolve: search only the row's own source with its full query")
    args = ap.parse_args()
    rows = read_sources(set(args.only) if args.only else None)
    if args.command == "report":
        sys.exit(cmd_report(rows))
    steps = {"resolve": lambda: cmd_resolve(rows, not args.no_fallback), "verify": lambda: cmd_verify(rows), "fetch": lambda: cmd_fetch(rows), "process": lambda: cmd_process(rows, not args.no_grade), "manifest": lambda: cmd_manifest(rows)}
    if args.command == "all":
        rc = 0
        for name in ("resolve", "verify", "fetch", "process", "manifest"):
            print(f"\n== {name}")
            rc |= steps[name]()
        write_failures(rows)
        sys.exit(rc)
    rc = steps[args.command]()
    write_failures(rows)
    sys.exit(rc)


if __name__ == "__main__":
    main()
