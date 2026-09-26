"""Tracks (Stage 3) and guided reading (Stage 4) against the fake-voice API
(setup as in e2e_course.py; E2E_FRONT / E2E_API pick the ports):

- course home before 9.4: every track card locked; after 9.4: side readings
  open; after 12.4: everything open
- /learn/track/history: the ladder, "make this my track", track words link
- Lesson hist.1, Read step (original panel) and every exercise answered
- the history gate: every item answered, passed
- Reader: a library passage shows its known-word percentage; the coverage
  panel under the text links to a deck of the new words on /words
"""

from __future__ import annotations

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import expect, sync_playwright  # noqa: E402

from e2e_course import CHROME, FRONT, api, run_items  # noqa: E402

SHOTS = os.environ.get("E2E_SHOTS", tempfile.mkdtemp(prefix="attic-e2e-"))


def progress_doc(done: list[str]) -> dict:
    now = int(time.time() * 1000)
    lessons = {lid: {"status": "done", "best": 1, "attempts": 1, "firstDone": now - 3 * 86400000, "lastDone": now - 3 * 86400000, "updated": now} for lid in done}
    return {"version": 2, "cards": {}, "settings": {"direction": "both", "cardTypes": [], "sessionSize": 20, "syncCode": "", "autoSpeak": False, "showEnglish": True, "accents": "lenient"}, "log": [],
            "course": {"lessons": lessons, "tests": {}, "skills": {}, "errors": [], "rereads": {}, "goal": {"minutesPerDay": 15}, "activity": []}}


def main() -> int:
    course = api("/api/course")
    order = course["lesson_order"]
    upto = lambda lid: order[: order.index(lid) + 1]  # noqa: E731
    hist = api("/api/course/track/history")
    assert len([lesson for lesson in hist["lessons"] if lesson["available"]]) == 7
    h1 = api("/api/course/lesson/hist.1")
    gate = api("/api/course/test/gate-hist?seed=1")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        page = ctx.new_page()
        page.on("console", lambda m: print("  [console]", m.text) if m.type == "error" and "CERT" not in m.text else None)
        page.goto(f"{FRONT}/learn")

        def seed(done: list[str]) -> None:
            page.evaluate("(d) => localStorage.setItem('attic.srs.v1', JSON.stringify(d))", progress_doc(done))

        # ---- gating on the course home
        seed(upto("9.3"))
        page.goto(f"{FRONT}/learn")
        cards = page.locator(".trackTile")
        expect(cards).to_have_count(4)
        expect(cards.first).to_contain_text("OPENS AFTER 9.4")
        seed(upto("9.4"))
        page.reload()
        expect(cards.first).to_contain_text("SIDE READINGS OPEN")
        seed(upto("12.4"))
        page.reload()
        expect(page.locator(".trackTile", has_text="Ἱστορία")).to_contain_text("OPEN · 0/7")
        page.locator(".trackTile", has_text="Ἱστορία").scroll_into_view_if_needed()
        page.screenshot(path=f"{SHOTS}/t1-home-tracks.png", full_page=True)
        print("home track cards ok")

        # ---- track page
        page.locator(".trackTile", has_text="Ἱστορία").click()
        expect(page.locator("h1")).to_have_text("Ἱστορία")
        expect(page.locator(".ladderItem")).to_have_count(8)
        page.get_by_role("button", name="Make this my track").click()
        expect(page.get_by_role("button", name="Your track ✓ · unset")).to_be_visible()
        href = page.get_by_role("link", name="Study the track words").get_attribute("href") or ""
        assert href.startswith("/words?words="), href
        page.screenshot(path=f"{SHOTS}/t2-track.png", full_page=True)
        print("track page ok")

        # ---- hist.1: the original panel, then every exercise
        page.goto(f"{FRONT}/learn/lesson/hist.1?step=2")
        expect(page.locator(".lessonCrumbs")).to_contain_text("Ἱστορία")
        toggle = page.locator(".originalToggle")
        expect(toggle).to_contain_text("Thucydides")
        toggle.click()
        expect(page.locator(".originalList > li")).to_have_count(len(h1["original_text"]["sentences"]))
        page.goto(f"{FRONT}/learn/lesson/hist.1?step=6")
        expect(page.locator(".exerciseCount")).to_have_text(f"1 / {len(h1['exercises'])}", timeout=15000)
        run_items(page, h1["exercises"], practice=True, label="hist.1 exercises")

        # ---- the history gate (all lessons done a few days ago → open)
        seed(upto("12.4") + [lesson["id"] for lesson in hist["lessons"]])
        page.goto(f"{FRONT}/learn/track/history")
        expect(page.locator(".ladderItem.gate a")).to_be_visible()
        page.goto(f"{FRONT}/learn/test/gate-hist")
        expect(page.locator(".eyebrow").first).to_contain_text("READING GATE")
        page.get_by_role("button", name="Start").click()
        items = [i for s in gate["sections"] for i in s["items"]]
        run_items(page, items, practice=False, label="gate-hist")
        expect(page.locator(".eyebrow")).to_have_text("PASSED")
        page.screenshot(path=f"{SHOTS}/t3-gate-passed.png", full_page=True)
        print("gate ok")

        # ---- guided reading in the Reader
        page.goto(f"{FRONT}/library")
        expect(page.locator(".readingRef").first).to_contain_text("% known words", timeout=20000)
        page.locator(".reading").first.click()
        expect(page.locator(".coverageStats")).to_be_visible(timeout=20000)
        study = page.locator(".coverage a", has_text="Study the")
        expect(study).to_be_visible()
        page.locator(".coverage").scroll_into_view_if_needed()
        page.screenshot(path=f"{SHOTS}/t4-coverage.png", full_page=False)
        study.click()
        page.wait_for_url("**/words?words=**")
        expect(page.locator(".chip.on", has_text="Words from")).to_be_visible()
        page.screenshot(path=f"{SHOTS}/t5-vocab-words.png", full_page=False)
        print("guided reading ok")
        ctx.close()
        browser.close()
    print(f"tracks e2e OK · screenshots in {SHOTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
