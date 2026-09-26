"""Stage 2 walk against the fake-voice API (setup as in e2e_course.py):

- Lesson 9.2, Read step: the original-text panel (Thucydides 2.14) opens and
  shows adapted sentences under the aligned original sentences.
- Lesson 10.4, Grammar step: the conditions diagram renders as SVG.
- Lesson 11.3: every exercise answered from the data.
- Reading gate II: every item answered, passed; the unseen Xenophon passage
  comes from the original text.

Every Stage 0–2 lesson is marked done first so everything is open.
FONTS=<dir with node_modules/@fontsource…> routes Google Fonts to local
copies so screenshots show Literata and IBM Plex Sans.
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from e2e_course import CHROME, FRONT, api, run_items  # noqa: E402

SHOTS = os.environ.get("E2E_SHOTS", tempfile.mkdtemp(prefix="attic-e2e-"))


def route_fonts(ctx) -> None:
    root = os.environ.get("FONTS")
    if not root:
        return
    lit = Path(root) / "node_modules/@fontsource-variable/literata/files"
    plex = Path(root) / "node_modules/@fontsource/ibm-plex-sans/files"
    css = "".join(
        f"@font-face{{font-family:'Literata';font-weight:200 900;src:url(https://fonts.gstatic.com/local/literata-{s}-wght-normal.woff2) format('woff2');}}\n"
        for s in ("latin", "latin-ext", "greek", "greek-ext")
    ) + "".join(
        f"@font-face{{font-family:'IBM Plex Sans';font-weight:{w};src:url(https://fonts.gstatic.com/local/ibm-plex-sans-latin-{w}-normal.woff2) format('woff2');}}\n"
        for w in (400, 500, 600)
    )

    def handler(route):
        url = route.request.url
        if "fonts.googleapis.com" in url:
            return route.fulfill(status=200, content_type="text/css", body=css)
        name = url.rsplit("/", 1)[-1]
        path = (lit if name.startswith("literata") else plex) / name
        return route.fulfill(status=200, content_type="font/woff2", body=path.read_bytes()) if path.exists() else route.abort()

    ctx.route("https://fonts.googleapis.com/**", handler)
    ctx.route("https://fonts.gstatic.com/**", handler)


def main() -> int:
    course = api("/api/course")
    now = int(time.time() * 1000)
    done = {lid: {"status": "done", "best": 1, "attempts": 1, "firstDone": now - 2 * 86400000, "lastDone": now - 2 * 86400000, "updated": now} for lid in course["lesson_order"]}
    doc = {"version": 2, "cards": {}, "settings": {"direction": "both", "cardTypes": [], "sessionSize": 20, "syncCode": "", "autoSpeak": False, "showEnglish": True, "accents": "lenient"}, "log": [],
           "course": {"lessons": done, "tests": {}, "skills": {}, "errors": [], "rereads": {}, "goal": {"minutesPerDay": 15}, "activity": []}}
    l92 = api("/api/course/lesson/9.2")
    assert l92["original_text"] and l92["original_text"]["author"] == "Thucydides"
    l113 = api("/api/course/lesson/11.3")
    gate = api("/api/course/test/gate-2?seed=1")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        for name, vp in (("phone", {"width": 390, "height": 844}), ("desktop", {"width": 1280, "height": 900})):
            ctx = browser.new_context(viewport=vp, device_scale_factor=2)
            route_fonts(ctx)
            page = ctx.new_page()
            page.on("console", lambda m: print("  [console]", m.text) if m.type == "error" and "CERT" not in m.text else None)
            page.goto(f"{FRONT}/learn")
            page.evaluate("(d) => localStorage.setItem('attic.srs.v1', JSON.stringify(d))", doc)

            # original text panel
            page.goto(f"{FRONT}/learn/lesson/9.2?step=2")
            toggle = page.locator(".originalToggle")
            expect(toggle).to_contain_text("Thucydides")
            toggle.click()
            expect(page.locator(".originalList > li")).to_have_count(len(l92["original_text"]["sentences"]))
            expect(page.locator(".adaptedUnder").first).to_be_visible()
            page.locator(".original").scroll_into_view_if_needed()
            page.locator(".original").screenshot(path=f"{SHOTS}/s2-{name}-original.png")

            # a diagram in the grammar step
            page.goto(f"{FRONT}/learn/lesson/10.4?step=5")
            expect(page.locator(".diagramBody svg").first).to_be_visible()
            page.screenshot(path=f"{SHOTS}/s2-{name}-grammar.png", full_page=True)
            if name == "desktop":
                ctx.close()
                continue

            # all exercises of 11.3
            page.goto(f"{FRONT}/learn/lesson/11.3?step=6")
            expect(page.locator(".exerciseCount")).to_have_text(f"1 / {len(l113['exercises'])}", timeout=15000)
            run_items(page, l113["exercises"], practice=True, label="11.3 exercises")

            # reading gate II
            page.goto(f"{FRONT}/learn/test/gate-2")
            expect(page.locator("h1")).to_contain_text(gate["title_grc"])
            page.get_by_role("button", name="Start").click()
            items = [i for s in gate["sections"] for i in s["items"]]
            reading = next(s for s in gate["sections"] if s.get("passage_source"))
            run_items(page, items, practice=False, label="gate-2")
            expect(page.locator(".eyebrow")).to_have_text("PASSED")
            page.screenshot(path=f"{SHOTS}/s2-{name}-gate2-passed.png", full_page=True)
            assert reading["passage"].startswith("ἦν δέ τις ἐν τῇ στρατιᾷ Ξενοφῶν")
            ctx.close()
        browser.close()
    print(f"stage 2 e2e OK · screenshots in {SHOTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
