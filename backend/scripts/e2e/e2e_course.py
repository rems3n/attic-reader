"""Headless walk through the course: home → Lesson 1.1 all ten steps, every
exercise answered from the lesson data → lesson marked done → persistence
across reload → Unit 1 test unlocked (progress injected) and passed.

Start the fake-voice API and the built frontend first:

    python scripts/e2e/fake_server.py &                 # port 8000
    (cd ../frontend && npm run build && npm start) &    # port 3000
    pip install playwright
    E2E_CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome python scripts/e2e/e2e_course.py

Screenshots land in $E2E_SHOTS (default: a temp dir).
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import Page, expect, sync_playwright

FRONT = os.environ.get("E2E_FRONT", "http://localhost:3000").rstrip("/")
API = os.environ.get("E2E_API", "http://localhost:8000").rstrip("/")
SHOTS = os.environ.get("E2E_SHOTS", tempfile.mkdtemp(prefix="attic-e2e-"))
CHROME = os.environ.get("E2E_CHROME")  # e.g. /opt/pw-browsers/chromium-1194/chrome-linux/chrome


def api(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=30) as r:
        return json.load(r)


def answer_item(page: Page, item: dict) -> None:
    """Drive the current exercise UI with the correct answer for `item`."""
    t = item["type"]
    ex = page.locator(".exercise")
    if t in {"pick-picture", "listen-pick", "cloze-choice", "true-false-grc", "bank-cloze", "label"} or (t == "answer-grc" and item.get("options")):
        options = item.get("options") or [{"id": "true", "text": "ἀληθές"}, {"id": "false", "text": "ψευδές"}]
        want = next(o for o in options if o["id"] == item["answer"])
        buttons = ex.locator(".option")
        n = buttons.count()
        for i in range(n):
            b = buttons.nth(i)
            if want.get("text") and b.inner_text().strip() == want["text"]:
                b.click()
                return
            if want.get("image") and b.locator(f"[aria-label]").count() and b.locator("[aria-label]").first.get_attribute("aria-label") == image_alt(want["image"]):
                b.click()
                return
        raise AssertionError(f"option not found for {item['id']}: {want}")
    if t in {"cloze-type", "produce-form", "transform", "compose-grc", "dictation", "endings-cloze", "answer-grc"}:
        inputs = ex.locator("input.greekAnswer")
        for i, gap in enumerate(item["gaps"]):
            inputs.nth(i).fill(gap["answers"][0].replace("(ν)", "ν"))
        return
    if t == "parse":
        for g in item["groups"]:
            label = next(o["label"] for o in g["options"] if o["id"] == item["answer"][g["id"]])
            ex.locator(".parseGroup", has_text=g["label"]).locator(".chip", has_text=label).first.click()
        return
    if t == "locate":
        toks = ex.locator(".locateLine .token")
        for i in item["answer"]:
            toks.nth(i).click()
        return
    if t == "reorder":
        for word in item["answers"][0].split():
            ex.locator(".reorderBank .token", has_text=word).first.click()
        return
    if t in {"match", "word-family"}:
        for p in item["pairs"]:
            ex.locator(".matchCol").nth(0).locator(".token", has_text=p["left"]).first.click()
            ex.locator(".matchCol").nth(1).locator(".token", has_text=p["right"]).first.click()
        return
    # self-graded
    ex.get_by_role("button", name="Show the model answer").click()
    ex.get_by_role("button", name="I got it").click()


_images: dict[str, dict] | None = None


def image_alt(image_id: str) -> str:
    global _images
    if _images is None:
        _images = {i["id"]: i for i in api("/api/course/images")["images"]}
    return _images[image_id]["alt_en"]


def run_items(page: Page, items: list[dict], practice: bool = True, label: str = "") -> None:
    for n, item in enumerate(items):
        expect(page.locator(".exerciseCount")).to_have_text(f"{n + 1} / {len(items)}")
        answer_item(page, item)
        if practice:
            if item["type"] in {"translate-en", "describe-picture", "retell", "read-aloud", "continue-story"}:
                page.get_by_role("button", name="Continue").click()
            else:
                page.get_by_role("button", name="Check").click()
                expect(page.locator(".feedback")).to_contain_text("Right")
            page.locator(".exerciseActions button").click()  # Next / Finish
        else:
            page.locator(".exerciseActions button").click()  # Next / Submit
    print(f"  {label}: {len(items)} items answered")


def main() -> int:
    lesson = api("/api/course/lesson/1.1")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        page.on("console", lambda m: print("  [console]", m.type, m.text) if m.type in {"error"} else None)

        # ---- course home
        page.goto(f"{FRONT}/learn")
        expect(page.locator("h1")).to_contain_text("Ἡ ὁδός σου")
        expect(page.locator(".continueCard")).to_contain_text("START HERE")
        page.screenshot(path=f"{SHOTS}/01-home.png", full_page=True)
        print("home ok")

        # ---- lesson 1.1 directly (0.x are open too but the story lesson is the target)
        page.goto(f"{FRONT}/learn/lesson/1.1")
        expect(page.locator(".lessonTitle")).to_have_text(lesson["title_grc"])
        page.screenshot(path=f"{SHOTS}/02-cover.png", full_page=True)
        page.get_by_role("button", name="Begin →").click()
        expect(page.locator(".stepName")).to_contain_text("Ἀκούσατε")
        page.get_by_role("button", name="Now read it →").click()
        expect(page.locator(".stepName")).to_contain_text("Ἀνάγνωσις")
        # play the first sentence; the fake voice returns a sine burst
        page.locator(".sentencePlay").first.click()
        page.wait_for_timeout(1500)
        expect(page.locator(".storyLine").first).to_contain_text("ὁ Ἀρίστων")
        # tap a glossed word → gloss card
        page.locator(".storyWord.glossed").first.click()
        expect(page.locator(".glossCard")).to_be_visible()
        page.screenshot(path=f"{SHOTS}/03-read.png", full_page=True)
        page.get_by_role("button", name="Next →").click()
        expect(page.locator(".stepName")).to_contain_text("Λέξεις")
        expect(page.locator(".vocabTile")).to_have_count(len(lesson["vocab"]))
        page.screenshot(path=f"{SHOTS}/04-vocab.png", full_page=True)
        page.get_by_role("button", name="Next →").click()
        expect(page.locator(".stepName")).to_contain_text("Παρατηρήσατε")
        page.get_by_role("button", name="Explain it →").click()
        expect(page.locator(".stepName")).to_contain_text("Γραμματική")
        expect(page.locator(".mdTable, .md")).to_be_visible()
        page.screenshot(path=f"{SHOTS}/05-grammar.png", full_page=True)
        page.get_by_role("button", name="Practise →").click()
        expect(page.locator(".stepName")).to_contain_text("Μελετήματα")
        run_items(page, lesson["exercises"], label="exercises")
        expect(page.locator(".resultBig")).to_have_text("100 %")
        page.screenshot(path=f"{SHOTS}/06-exercises-done.png", full_page=True)
        page.get_by_role("button", name="Next →").click()
        expect(page.locator(".stepName")).to_contain_text("Ἐρωτήματα")
        run_items(page, lesson["questions"], label="questions")
        expect(page.locator(".stepName")).to_contain_text("Πολιτισμός")
        page.get_by_role("button", name="Lesson check →").click()
        expect(page.locator(".stepName")).to_contain_text("Ἔλεγχος")
        page.screenshot(path=f"{SHOTS}/07-quiz.png", full_page=True)
        run_items(page, lesson["quiz"], label="quiz")
        expect(page.locator(".resultBig")).to_have_text("100 %")
        expect(page.locator(".ok")).to_contain_text("Lesson complete")
        page.screenshot(path=f"{SHOTS}/08-quiz-done.png", full_page=True)

        # ---- persistence
        stored = json.loads(page.evaluate("localStorage.getItem('attic.srs.v1')"))
        assert stored["version"] == 2
        assert stored["course"]["lessons"]["1.1"]["status"] == "done", stored["course"]["lessons"]["1.1"]
        assert stored["course"]["lessons"]["1.1"]["best"] == 1
        assert len(stored["course"]["skills"]) > 10 and stored["course"]["errors"] == []
        assert stored["course"]["activity"][0]["items"] > 30
        print("progress ok:", len(stored["course"]["skills"]), "skills tracked")

        page.goto(f"{FRONT}/learn")
        expect(page.locator(".continueCard")).to_contain_text("1·2")
        expect(page.locator(".statTile").nth(2)).to_contain_text("1")
        page.screenshot(path=f"{SHOTS}/09-home-after.png", full_page=True)
        print("home after ok")

        # ---- unit test: inject completed lessons two days ago, then take it
        two_days_ago = int(time.time() * 1000) - 2 * 86400 * 1000
        page.evaluate(
            """(t) => {
              const p = JSON.parse(localStorage.getItem('attic.srs.v1'));
              for (const id of ['0.1','0.2','0.3','0.4','1.1','1.2','1.3','1.4']) {
                p.course.lessons[id] = { status: 'done', best: 1, attempts: 1, firstDone: t, lastDone: t, updated: t };
              }
              localStorage.setItem('attic.srs.v1', JSON.stringify(p));
            }""",
            two_days_ago,
        )
        page.goto(f"{FRONT}/learn")
        expect(page.locator(".testLink").first).to_contain_text("Take the unit test")
        page.locator(".testLink").first.click()
        expect(page.locator(".testTitle")).to_be_visible()
        test = api("/api/course/test/unit-1?seed=1")
        items = [i for s in test["sections"] for i in s["items"]]
        page.get_by_role("button", name="Start").click()
        expect(page.locator(".passage, .sectionTag").first).to_be_visible()
        run_items(page, items, practice=False, label="unit test")
        expect(page.get_by_text("PASSED", exact=True)).to_be_visible()
        expect(page.locator(".resultBig")).to_have_text("100 %")
        page.screenshot(path=f"{SHOTS}/10-test-passed.png", full_page=True)
        stored = json.loads(page.evaluate("localStorage.getItem('attic.srs.v1')"))
        assert stored["course"]["tests"]["unit-1"]["passedAt"], stored["course"]["tests"]
        print("unit test ok")

        # ---- review quiz page renders generated items
        page.goto(f"{FRONT}/practice/review")
        page.wait_for_timeout(1500)
        assert page.locator(".exercise, .muted").first.is_visible()
        # ---- vocab deck filter by lesson
        page.goto(f"{FRONT}/words")
        chip = page.locator(".chip").filter(has_text=re.compile(r"^1\.1\s")).first
        expect(chip).to_be_visible()
        chip.click()
        expect(page.locator(".badge")).to_contain_text("24 words")
        page.screenshot(path=f"{SHOTS}/11-vocab-lesson-filter.png", full_page=True)
        print("vocab filter ok")

        # ---- desktop viewport smoke
        desk = browser.new_page(viewport={"width": 1280, "height": 900})
        desk.goto(f"{FRONT}/learn")
        expect(desk.locator(".unitTile").first).to_be_visible()
        desk.screenshot(path=f"{SHOTS}/12-home-desktop.png", full_page=True)
        desk.goto(f"{FRONT}/learn/lesson/1.3?step=2")
        expect(desk.locator(".glossMargin").first).to_be_visible()
        desk.screenshot(path=f"{SHOTS}/13-read-desktop.png", full_page=True)
        browser.close()
    print("E2E PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
