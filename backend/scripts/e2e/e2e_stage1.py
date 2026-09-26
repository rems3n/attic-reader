"""Stage 1 walk against the fake-voice API: Lesson 6.3 (read, grammar, all
exercises answered from the data) and the reading gate, with every earlier
lesson marked done. Setup as in e2e_course.py."""

import os
import sys
import tempfile
sys.path.insert(0, "scripts/e2e")
from playwright.sync_api import sync_playwright, expect
from e2e_course import CHROME, FRONT, api, run_items
SHOTS = os.environ.get("E2E_SHOTS", tempfile.mkdtemp(prefix="attic-e2e-"))
lesson = api("/api/course/lesson/6.3")
gate = api("/api/course/test/gate-1?seed=1")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    page = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    page.on("console", lambda m: print("  [console]", m.type, m.text) if m.type == "error" and "CERT" not in m.text else None)
    # unlock everything: mark all lessons done via localStorage
    page.goto(f"{FRONT}/course")
    import time
    now = int(time.time()*1000)
    lessons = {lid: {"status": "done", "best": 1, "attempts": 1, "firstDone": now-2*86400000, "lastDone": now-2*86400000, "updated": now} for lid in api("/api/course")["lesson_order"] if lid.split(".")[0] in {"0","1","2","3","4","5","6"}}
    page.evaluate("(doc) => localStorage.setItem('attic.srs.v1', JSON.stringify(doc))", {"version": 2, "cards": {}, "settings": {"direction":"both","cardTypes":[],"sessionSize":20,"syncCode":"","autoSpeak":False,"showEnglish":True,"accents":"lenient"}, "log": [], "course": {"lessons": lessons, "tests": {}, "skills": {}, "errors": [], "rereads": {}, "goal": {"minutesPerDay": 15}, "activity": []}})
    # lesson 6.3: read step renders story + glosses, then exercises
    page.goto(f"{FRONT}/course/lesson/6.3?step=2")
    expect(page.locator(".storyReader, .story, main")).to_be_visible()
    expect(page.locator("main")).to_contain_text("ὑφαίνει")
    page.screenshot(path=f"{SHOTS}/u6-read.png", full_page=True)
    page.goto(f"{FRONT}/course/lesson/6.3?step=5")
    page.screenshot(path=f"{SHOTS}/u6-grammar.png", full_page=True)
    page.goto(f"{FRONT}/course/lesson/6.3?step=6")
    expect(page.locator(".exerciseCount")).to_have_text(f"1 / {len(lesson['exercises'])}", timeout=15000)
    run_items(page, lesson["exercises"], practice=True, label="6.3 exercises")
    page.screenshot(path=f"{SHOTS}/u6-exercises-done.png", full_page=True)
    # reading gate
    page.goto(f"{FRONT}/course/test/gate-1")
    expect(page.locator("h1")).to_contain_text(gate["title_grc"])
    page.get_by_role("button", name="Start").click()
    items = [i for s in gate["sections"] for i in s["items"]]
    run_items(page, items, practice=False, label="gate-1")
    expect(page.locator(".eyebrow")).to_have_text("PASSED")
    page.screenshot(path=f"{SHOTS}/u6-gate-passed.png", full_page=True)
    page.goto(f"{FRONT}/course")
    page.screenshot(path=f"{SHOTS}/u6-home.png", full_page=True)
    b.close()
print("unit 6 e2e OK")
