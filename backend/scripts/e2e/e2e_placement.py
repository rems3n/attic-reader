"""Placement walk against the fake-voice API (see e2e_course.py for setup).

Two runs in fresh browser contexts:
  1. every item right → placed after Unit 1, Stage 0 + Unit 1 marked skipped,
     course home no longer says START HERE at 0.1;
  2. three misses in a row → placed at the beginning, nothing skipped.
"""

from __future__ import annotations

import os
import sys
import tempfile

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
from e2e_course import CHROME, FRONT, answer_item, api  # noqa: E402

SHOTS = os.environ.get("E2E_SHOTS", tempfile.mkdtemp(prefix="attic-e2e-"))
SEED = 11


def wrong_answer(page, item):
    t = item["type"]
    ex = page.locator(".exercise")
    if t in {"cloze-type", "produce-form", "transform", "compose-grc", "dictation", "endings-cloze", "answer-grc"} and not item.get("options"):
        for i in range(len(item["gaps"])):
            ex.locator("input.greekAnswer").nth(i).fill("ξξξ")
        return
    if ex.locator(".option").count():
        # pick an option that is not the answer
        options = item.get("options") or [{"id": "true", "text": "ἀληθές"}, {"id": "false", "text": "ψευδές"}]
        bad = next(o for o in options if o["id"] != item["answer"])
        buttons = ex.locator(".option")
        for i in range(buttons.count()):
            if bad.get("text") and buttons.nth(i).inner_text().strip() == bad["text"]:
                buttons.nth(i).click()
                return
    if t == "parse":
        for g in item["groups"]:
            bad = next(o["label"] for o in g["options"] if o["id"] != item["answer"][g["id"]])
            ex.locator(".parseGroup", has_text=g["label"]).locator(".chip", has_text=bad).first.click()
        return
    if t == "locate":
        toks = ex.locator(".locateLine .token")
        idx = next(i for i in range(toks.count()) if i not in item["answer"])
        toks.nth(idx).click()
        return
    if t == "reorder":
        words = item["answers"][0].split()
        for word in reversed(words):  # backwards is wrong for any sentence of two or more words
            ex.locator(".reorderBank .token", has_text=word).first.click()
        return
    if t in {"match", "word-family"}:
        pairs = item["pairs"]
        for i, p in enumerate(pairs):
            ex.locator(".matchCol").nth(0).locator(".token", has_text=p["left"]).first.click()
            ex.locator(".matchCol").nth(1).locator(".token", has_text=pairs[(i + 1) % len(pairs)]["right"]).first.click()
        return
    raise AssertionError(f"no wrong answer for type {t}")


def main() -> int:
    placement = api(f"/api/course/placement?seed={SEED}")
    blocks = placement["blocks"]
    assert blocks, "no placement blocks (is unit-1.json present?)"
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()

        # ---- run 1: pass everything
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        page = ctx.new_page()
        page.on("console", lambda m: print("  [console]", m.type, m.text) if m.type == "error" else None)
        page.goto(f"{FRONT}/course")
        expect(page.locator(".placementHint")).to_contain_text("placement test")
        page.goto(f"{FRONT}/course/placement?seed={SEED}")
        expect(page.locator("h1")).to_contain_text("Ποῦ ἄρχομαι;")
        page.screenshot(path=f"{SHOTS}/p1-intro.png", full_page=True)
        page.get_by_role("button", name="Start").click()
        for b in blocks:
            expect(page.locator(".sectionTag")).to_contain_text(f"UNIT {b['unit']}")
            for n, item in enumerate(b["items"]):
                expect(page.locator(".exerciseCount")).to_have_text(f"{n + 1} / {len(b['items'])}")
                answer_item(page, item)
                page.locator(".exerciseActions button").click()
            print(f"  unit {b['unit']}: {len(b['items'])} items answered")
        expect(page.locator(".eyebrow")).to_have_text("PLACED")
        last = blocks[-1]
        expect(page.locator(".resultBig")).to_contain_text(f"Unit {last['unit']}")
        page.screenshot(path=f"{SHOTS}/p2-placed.png", full_page=True)
        stored = page.evaluate("JSON.parse(localStorage.getItem('attic.srs.v1'))")
        course = stored["course"]
        assert course["placement"]["unit"] == last["unit"] + 1, course["placement"]
        for lid in last["lessons"]:
            assert course["lessons"][lid]["status"] == "skipped", (lid, course["lessons"].get(lid))
        page.goto(f"{FRONT}/course")
        expect(page.locator(".placementHint")).to_have_count(0)
        if last["next_lesson"]:
            expect(page.locator(".continueCard")).to_contain_text(last["next_lesson"].replace(".", "·"))
        else:
            expect(page.locator(".continueCard")).to_have_count(0)
        page.screenshot(path=f"{SHOTS}/p3-home-after.png", full_page=True)
        ctx.close()

        # ---- run 2: miss three in a row
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        page.goto(f"{FRONT}/course/placement?seed={SEED}")
        page.get_by_role("button", name="Start").click()
        b = blocks[0]
        for n, item in enumerate(b["items"]):
            expect(page.locator(".exerciseCount")).to_have_text(f"{n + 1} / {len(b['items'])}")
            wrong_answer(page, item)
            page.locator(".exerciseActions button").click()
        expect(page.locator(".eyebrow")).to_have_text("PLACED")
        expect(page.locator(".resultBig")).to_contain_text("ἄρχου")
        stored = page.evaluate("JSON.parse(localStorage.getItem('attic.srs.v1'))")
        assert stored["course"]["placement"]["unit"] == 0
        assert not any(v["status"] == "skipped" for v in stored["course"]["lessons"].values())
        page.get_by_role("button", name="Open Lesson 0·1").click()
        expect(page).to_have_url(f"{FRONT}/course/lesson/0.1")
        page.screenshot(path=f"{SHOTS}/p4-beginner.png", full_page=True)
        ctx.close()
        browser.close()
    print(f"placement e2e OK · screenshots in {SHOTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
