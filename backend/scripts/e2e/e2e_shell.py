"""F1 shell regression: new/returning guests, onboarding, routes, settings and summary.
Uses the fake voice server and built frontend. Saves screenshots at both required sizes.
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from e2e_course import FRONT, CHROME, api
from e2e_stage2 import route_fonts

SHOTS = Path(os.environ.get("E2E_SHOTS", "../docs/screenshots/f1"))
SHOTS.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
    for label, size in [("phone", {"width":390,"height":844}), ("desktop", {"width":1280,"height":900})]:
        ctx = browser.new_context(viewport=size)
        route_fonts(ctx)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(FRONT)
        expect(page.get_by_role("heading", name="Learn to read Ancient Greek.")).to_be_visible()
        page.screenshot(path=str(SHOTS / f"{label}-home.png"), full_page=True)
        if label == "phone":
            expect(page.locator(".mobileTabs")).to_be_visible()
            page.get_by_role("button", name="More", exact=True).click()
            expect(page.get_by_role("dialog")).to_be_visible()
            page.keyboard.press("Escape")
            expect(page.get_by_role("dialog")).not_to_be_visible()
        else:
            expect(page.locator(".sidebar")).to_be_visible()
        page.get_by_role("link", name="Start learning", exact=True).click()
        page.screenshot(path=str(SHOTS / f"{label}-start.png"), full_page=True)
        page.get_by_role("link", name="Continue", exact=True).click()
        expect(page).to_have_url(FRONT + "/learn/lesson/0.1")
        expect(page.get_by_role("complementary", name="App tour")).to_be_visible()
        page.get_by_role("button", name="Next", exact=True).click()
        page.get_by_role("button", name="Next", exact=True).click()
        page.get_by_role("button", name="Finish tour").click()
        page.wait_for_selector(".stepDot")
        page.goto(FRONT)
        expect(page.get_by_role("heading", name="Continue learning", exact=True)).to_be_visible()
        expect(page.get_by_role("link", name="Resume lesson")).to_be_visible()
        page.screenshot(path=str(SHOTS / f"{label}-dashboard.png"), full_page=True)
        for name, path in [("help","/help"),("settings","/settings"),("practice","/practice"),("quick","/practice/quick"),("library","/library"),("add-text","/library/new"),("progress","/progress")]:
            page.goto(FRONT + path)
            page.wait_for_load_state("networkidle")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), path
            page.screenshot(path=str(SHOTS / f"{label}-{name}.png"), full_page=True)
        page.goto(FRONT + "/settings")
        page.get_by_label("Daily course goal").fill("20")
        page.reload()
        expect(page.get_by_label("Daily course goal")).to_have_value("20")
        for old, new in [("/course?x=1","/learn?x=1"),("/course/review?mode=mistakes","/practice/review?mode=mistakes"),("/course/skills","/progress"),("/vocab","/words")]:
            page.goto(FRONT + old)
            expect(page).to_have_url(FRONT + new)
        # A one-card Quick session starts immediately and ends in the shared summary.
        word = api("/api/vocab")["items"][0]["id"]
        page.evaluate("""() => { const p = JSON.parse(localStorage.getItem('attic.srs.v1')); p.settings.direction = 'grc-en'; p.settings.cardTypes = []; localStorage.setItem('attic.srs.v1', JSON.stringify(p)); }""")
        page.goto(FRONT + f"/words?words={word}&quick=1")
        expect(page.locator(".flashcard")).to_be_visible(timeout=30000)
        expect(page.locator(".quickTimer")).to_be_visible()
        page.get_by_role("button", name="Show answer", exact=True).click()
        page.get_by_role("button", name="Easy", exact=True).click()
        expect(page.locator(".sessionSummary")).to_be_visible()
        page.screenshot(path=str(SHOTS / f"{label}-session-summary.png"), full_page=True)
        reading = api("/api/library")["items"][0]["id"]
        page.goto(FRONT + f"/?reading={reading}&sentence=0")
        expect(page).to_have_url(FRONT + f"/library?reading={reading}&sentence=0")
        page.goto(FRONT + "/start")
        page.get_by_role("radio", name="Read and listen").check()
        page.get_by_role("link", name="Continue", exact=True).click()
        expect(page).to_have_url(FRONT + "/library")
        page.get_by_role("button", name="Dismiss tour").click()
        page.goto(FRONT + "/start")
        page.get_by_role("radio", name="Return to Greek").check()
        page.get_by_role("radio", name="I can read the alphabet").check()
        page.get_by_role("button", name="Take a 6-question check").click()
        expect(page.locator(".exercise")).to_be_visible(timeout=30000)
        page.screenshot(path=str(SHOTS / f"{label}-starting-check.png"), full_page=True)
        assert not errors, errors
        ctx.close()
    browser.close()
print("E2E SHELL PASSED")
