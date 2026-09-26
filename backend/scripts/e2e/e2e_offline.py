"""Offline check: the service worker keeps a lesson usable without signal.

Self-contained: picks free ports, starts the fake-voice API (as in
fake_server.py, with CORS for the chosen frontend port), builds a copy of the
frontend in production mode against it (the service worker only registers in
production builds), starts `next start`, then with Chromium:

1. opens /course/lesson/1.1, waits until the service worker controls the page
   and the lesson prefetch has stored the story audio;
2. goes to the Read step, plays the first sentence and taps a word;
3. stops both servers and sets the browser context offline;
4. reloads the lesson: story text, pictures, offline banner, the played
   sentence and word clip are all served by the service worker;
5. opens /course (precached shell + cached course JSON), /vocab (shell, with
   the offline message where the network is needed) and an unvisited lesson
   (offline fallback page listing what is saved).

Only the processes this script starts are stopped.

    cd backend
    E2E_CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome \\
    E2E_SHOTS=/tmp/shots .venv/bin/python scripts/e2e/e2e_offline.py

Options (env): E2E_WORKDIR (where the frontend copy is built; default a temp
dir), E2E_SKIP_BUILD=1 (reuse a build already in E2E_WORKDIR/frontend for the
same API port given by E2E_API_PORT).
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent.parent
FRONTEND = BACKEND.parent / "frontend"
CHROME = os.environ.get("E2E_CHROME")
SHOTS = os.environ.get("E2E_SHOTS", tempfile.mkdtemp(prefix="attic-e2e-"))
WORKDIR = Path(os.environ.get("E2E_WORKDIR") or tempfile.mkdtemp(prefix="attic-offline-"))


# ---------------------------------------------------------------------------
# API child process (fake Kokoro, like fake_server.py but on any port)
# ---------------------------------------------------------------------------

def serve_api(port: int, front_origin: str) -> None:
    sys.path.insert(0, str(BACKEND))
    sys.path.insert(0, str(BACKEND / "tests"))
    os.environ.setdefault("CLIP_CACHE_DIR", tempfile.mkdtemp(prefix="e2e-clips-"))
    os.environ.setdefault("PROGRESS_DIR", tempfile.mkdtemp(prefix="e2e-progress-"))
    os.environ["ENABLE_KOKORO"] = "true"
    os.environ["KOKORO_WARMUP"] = "false"
    os.environ["LIBRARY_PRERENDER"] = "false"
    os.environ["CORS_ORIGINS"] = front_origin

    from conftest import FakePipeline  # noqa: PLC0415
    from app.tts.kokoro import KokoroAtticTTS  # noqa: PLC0415

    pipeline = FakePipeline()
    KokoroAtticTTS._load = lambda self: pipeline  # type: ignore[method-assign]
    KokoroAtticTTS.is_available = lambda self: (True, "fake")  # type: ignore[method-assign]

    import uvicorn  # noqa: PLC0415
    from app.main import app  # noqa: PLC0415

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, timeout: float = 90) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status < 500:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"{url} did not come up")


def start(cmd: list[str], cwd: Path, env: dict[str, str], log: Path) -> subprocess.Popen:
    fh = open(log, "w")
    return subprocess.Popen(cmd, cwd=cwd, env=env, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)


def stop(proc: subprocess.Popen | None) -> None:
    if not proc or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass


def build_frontend(api_base: str) -> Path:
    """Copy the frontend (node_modules symlinked) and build it, so the
    checkout's own .next is left alone for anyone else using it."""
    dest = WORKDIR / "frontend"
    if os.environ.get("E2E_SKIP_BUILD") and (dest / ".next" / "BUILD_ID").exists():
        return dest
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(FRONTEND, dest, ignore=shutil.ignore_patterns("node_modules", ".next", "test-results"), symlinks=True)
    (dest / "node_modules").symlink_to(FRONTEND / "node_modules")
    env = {**os.environ, "NEXT_PUBLIC_API_BASE_URL": api_base, "NEXT_TELEMETRY_DISABLED": "1"}
    print(f"building frontend in {dest} (API {api_base}) …", flush=True)
    t = time.time()
    out = subprocess.run(["npx", "next", "build"], cwd=dest, env=env, capture_output=True, text=True)
    if out.returncode:
        print(out.stdout[-4000:], out.stderr[-4000:])
        raise SystemExit("next build failed")
    print(f"  built in {time.time() - t:.0f} s", flush=True)
    return dest


def cache_count(page, prefix: str) -> int:
    return page.evaluate(
        """async (prefix) => {
            let n = 0;
            for (const name of await caches.keys()) if (name.startsWith(prefix)) n += (await (await caches.open(name)).keys()).length;
            return n;
        }""",
        prefix,
    )


def poll(page, fn: str, seconds: float, what: str) -> None:
    """page.evaluate awaits async functions; wait_for_function does not."""
    end = time.time() + seconds
    while time.time() < end:
        if page.evaluate(fn):
            return
        time.sleep(0.4)
    raise AssertionError(f"timed out waiting for {what}")


def wait_play(page, n: int, seconds: float) -> None:
    """Wait until the n-th audio play() since the last load has started."""
    end = time.time() + seconds
    while time.time() < end:
        plays = page.evaluate("() => window.__plays || []")
        if len(plays) >= n and plays[n - 1]["ok"] is not None:
            assert plays[n - 1]["ok"] is True, plays
            return
        time.sleep(0.2)
    raise AssertionError(f"audio play #{n} did not start: {page.evaluate('() => window.__plays')}")


def play_first_sentence(page, seconds: float) -> None:
    # StoryReader's first ▶ only loads the clips when none are loaded yet
    # (clipsFor() reads the pre-load state), so tap again once they are in.
    page.locator(".sentencePlay").first.click()
    page.wait_for_timeout(1000)
    if not page.evaluate("() => (window.__plays || []).length"):
        page.locator(".sentencePlay").first.click()
    wait_play(page, 1, seconds)


def run(front: str, api_base: str, procs: dict[str, subprocess.Popen]) -> int:
    from playwright.sync_api import expect, sync_playwright  # noqa: PLC0415

    with urllib.request.urlopen(f"{api_base}/api/course/lesson/1.1", timeout=30) as r:
        lesson = json.load(r)
    first_sentence = lesson["story"][0]["sentences"][0]["text"]

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, service_workers="allow")
        # Record every audio play() and whether it started, across reloads.
        ctx.add_init_script(
            """(() => {
                window.__plays = [];
                const orig = HTMLMediaElement.prototype.play;
                HTMLMediaElement.prototype.play = function () {
                    const rec = { src: this.currentSrc || this.src, ok: null };
                    window.__plays.push(rec);
                    const p = orig.call(this);
                    p.then(() => { rec.ok = true; }, (e) => { rec.ok = String(e); });
                    return p;
                };
            })();"""
        )
        page = ctx.new_page()
        page.on("console", lambda m: print("  [console]", m.type, m.text) if m.type == "error" else None)
        audio_responses: list[tuple[str, int, bool]] = []

        def on_response(resp) -> None:
            if "/api/speak" in resp.url or "/api/synthesize/stream" in resp.url:
                audio_responses.append((resp.url.split("/api/")[1], resp.status, resp.from_service_worker))

        page.on("response", on_response)

        # ---- 1. online: open the lesson, let the worker take over and warm the caches
        page.goto(f"{front}/course/lesson/1.1")
        expect(page.locator(".lessonTitle")).to_have_text(lesson["title_grc"])
        page.wait_for_function("navigator.serviceWorker && navigator.serviceWorker.controller !== null", timeout=60000)
        print("service worker controls the page")
        has_all = """async () => {
            const names = await caches.keys();
            const has = async (prefix, needle) => {
                for (const n of names.filter((x) => x.startsWith(prefix))) {
                    for (const k of await (await caches.open(n)).keys()) if (k.url.includes(needle)) return true;
                }
                return false;
            };
            return (await has("attic-pages-", "/course/lesson/1.1")) && (await has("attic-stream-", "__sw_stream")) && (await has("attic-api-", "/api/course/lesson/1.1")) && (await has("attic-api-", "/api/course/images"));
        }"""
        poll(page, has_all, 90, "lesson page, JSON and story audio cached")
        counts = {k: cache_count(page, f"attic-{k}-") for k in ("shell", "pages", "static", "api", "audio", "stream", "images")}
        print("prefetch done; cache entries:", counts)
        assert counts["pages"] >= 5, counts  # /, /course, /vocab, /grammar + the lesson
        assert counts["static"] > 5, counts

        # ---- 2. read step: play the first sentence, tap an unglossed word
        page.get_by_role("button", name="Begin →").click()
        page.get_by_role("button", name="Now read it →").click()
        expect(page.locator(".stepName")).to_contain_text("Ἀνάγνωσις")
        expect(page.locator(".storyLine").first).to_contain_text(first_sentence.split()[0])
        play_first_sentence(page, 20)
        page.wait_for_timeout(1200)
        word = page.locator(".storyLine").first.locator(".storyWord:not(.glossed)").first
        word_text = word.inner_text().strip()
        word.click()
        poll(page, "async () => { for (const n of await caches.keys()) if (n.startsWith('attic-audio-') && (await (await caches.open(n)).keys()).length) return true; return false; }", 30, "word clip cached")
        page.screenshot(path=f"{SHOTS}/offline-01-online-read.png", full_page=False)
        print(f"online: played sentence 1 and word {word_text!r}")

        # ---- 3. no signal: stop both servers and take the context offline
        stop(procs.pop("front"))
        stop(procs.pop("api"))
        ctx.set_offline(True)
        audio_responses.clear()
        print("servers stopped, context offline")

        # ---- 4. the lesson again, from the cache
        page.reload()
        expect(page.locator(".lessonTitle")).to_have_text(lesson["title_grc"], timeout=20000)
        expect(page.locator(".offlineBanner")).to_contain_text("Offline")
        expect(page.locator(".stepName")).to_contain_text("Ἀνάγνωσις")  # step restored from progress
        expect(page.locator(".storyLine").first).to_contain_text(first_sentence.split()[0])
        play_first_sentence(page, 10)
        expect(page.locator(".storyControls .warnText")).to_have_count(0)
        page.locator(".storyLine").first.locator(".storyWord", has_text=word_text).first.click()
        wait_play(page, 2, 10)
        stream = [r for r in audio_responses if r[0].startswith("synthesize/stream")]
        speak = [r for r in audio_responses if r[0].startswith("speak")]
        assert stream and all(s == 200 and sw for _, s, sw in stream), audio_responses
        assert speak and all(s == 200 and sw for _, s, sw in speak), audio_responses
        page.screenshot(path=f"{SHOTS}/offline-02-lesson-offline.png", full_page=False)
        print(f"offline: lesson reloaded, sentence and word clips served by the worker ({len(stream)} stream, {len(speak)} speak)")

        # ---- 5a. course home from the precached shell + cached JSON
        page.goto(f"{front}/course")
        expect(page.locator("h1")).to_contain_text("Ἡ ὁδός σου", timeout=20000)
        expect(page.locator(".offlineBanner")).to_be_visible()
        page.screenshot(path=f"{SHOTS}/offline-03-course-offline.png", full_page=False)
        print("offline: /course rendered")

        # ---- 5b. vocab shell: renders, and says why the word list is missing
        page.goto(f"{front}/vocab")
        expect(page.locator(".nav")).to_be_visible(timeout=20000)
        expect(page.locator("main .error")).to_contain_text("You are offline", timeout=20000)
        page.screenshot(path=f"{SHOTS}/offline-04-vocab-offline.png", full_page=False)
        print("offline: /vocab shell with offline message")

        # ---- 5c. a page never opened: the fallback page, listing what is saved
        page.goto(f"{front}/course/lesson/2.1")
        expect(page.locator("h1")).to_have_text("You are offline", timeout=20000)
        expect(page.locator("#savedList")).to_contain_text("Lesson 1.1")
        page.screenshot(path=f"{SHOTS}/offline-05-fallback.png", full_page=False)
        print("offline: fallback page for an unvisited lesson")

        browser.close()
    return 0


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--serve-api":
        serve_api(int(sys.argv[2]), sys.argv[3])
        return 0

    api_port = int(os.environ.get("E2E_API_PORT") or free_port())
    front_port = free_port()
    api_base = f"http://127.0.0.1:{api_port}"
    front = f"http://127.0.0.1:{front_port}"
    WORKDIR.mkdir(parents=True, exist_ok=True)
    os.makedirs(SHOTS, exist_ok=True)
    procs: dict[str, subprocess.Popen] = {}
    try:
        procs["api"] = start([sys.executable, __file__, "--serve-api", str(api_port), front], BACKEND, dict(os.environ), WORKDIR / "api.log")
        wait_http(f"{api_base}/health")
        print(f"fake API on {api_base}")
        dest = build_frontend(api_base)
        procs["front"] = start(["npx", "next", "start", "-p", str(front_port), "-H", "127.0.0.1"], dest, {**os.environ, "NEXT_TELEMETRY_DISABLED": "1"}, WORKDIR / "front.log")
        wait_http(f"{front}/course")
        print(f"frontend on {front}")
        rc = run(front, api_base, procs)
        print(f"screenshots in {SHOTS}")
        print("OK" if rc == 0 else "FAILED")
        return rc
    finally:
        for proc in procs.values():
            stop(proc)


if __name__ == "__main__":
    sys.exit(main())
