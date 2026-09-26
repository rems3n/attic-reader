"""Skills grid and mistakes deck against the fake-voice API.

Start the API and a built frontend first (ports are free to choose):

    E2E_API_PORT=8431 E2E_FRONT=http://localhost:3431 python scripts/e2e/fake_server.py &
    (cd ../frontend && NEXT_DIST_DIR=.next-skills NEXT_PUBLIC_API_BASE_URL=http://localhost:8431 npm run build \
       && NEXT_DIST_DIR=.next-skills npx next start -p 3431) &
    E2E_API=http://localhost:8431 E2E_FRONT=http://localhost:3431 \
    E2E_CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome python scripts/e2e/e2e_skills.py

Walk (phone size):
- progress is seeded with skills at every level and five mistakes: a lesson
  exercise, a lesson id shared by a question and a quiz item (the stored
  answer picks the quiz item), a generated test item, a test reading item
  (shown with its passage) and one that no longer exists;
- course home: the Review card shows the Mistakes count and the Skills link;
- /progress: legend counts, tap a cell → detail (lessons, paradigm,
  Practise), the Weak filter;
- Practise → /practice/review?skills=… answered from the drill response;
- /practice/review?mode=mistakes: the unrebuildable card is removed; round 1
  misses the reading item and gets the rest right, round 2 gets all right
  (four cards leave the deck), round 3 clears the last one.
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import Page, expect, sync_playwright  # noqa: E402

from e2e_course import CHROME, FRONT, SHOTS, answer_item, api  # noqa: E402

DAY = 86400000


def skill_state(results: list[bool], days_back: list[int], now: int) -> dict:
    """Mirror updateSkill in lib/learn.ts over a list of results."""
    s = None
    for r, back in zip(results, days_back):
        at = now - back * DAY
        day = time.strftime("%Y-%m-%d", time.gmtime(at / 1000))
        v = 1 if r else 0
        if s is None:
            s = {"correct": v, "total": 1, "streak": v, "last": at, "ewma": float(v), "days": [day]}
        else:
            s = {"correct": s["correct"] + v, "total": s["total"] + 1, "streak": s["streak"] + 1 if r else 0, "last": at,
                 "ewma": s["ewma"] * 0.8 + v * 0.2, "days": s["days"] + ([day] if day not in s["days"] else [])}
    return s  # type: ignore[return-value]


def seeded_doc(course: dict, now: int) -> dict:
    order = course["lesson_order"]
    done = {lid: {"status": "done", "best": 1, "attempts": 1, "firstDone": now - 5 * DAY, "lastDone": now - 5 * DAY, "updated": now}
            for lid in order[: order.index("2.4") + 1]}
    skills = {
        "noun.decl2.dat.sg": skill_state([False, False, True, False], [3, 3, 1, 1], now),          # weak
        "noun.decl1.gen.sg": skill_state([True, False, True, False, True], [2, 2, 1, 1, 0], now),  # learning
        "art.acc.sg": skill_state([True, True, True, True], [2, 1, 1, 0], now),                     # strong
        "verb.pres.act.ind.3sg": skill_state([True] * 10, [6, 6, 5, 5, 4, 3, 3, 2, 1, 0], now),    # mastered
        "read.comprehension": skill_state([True, False, False, True], [2, 1, 1, 0], now),          # learning
    }
    errors = [
        {"item": "1.1:e999", "lesson": "1.1", "answer": '"a"', "at": now - 9 * 60000},                        # gone
        {"item": "1.1:e1", "lesson": "1.1", "answer": '["ύς","ή","ων","ο"]', "at": now - 8 * 60000},          # lesson exercise
        {"item": "1.1:q1", "lesson": "1.1", "answer": '"d"', "at": now - 7 * 60000},                          # the quiz item (d)
        {"item": "unit-1:formsg3", "lesson": "1.4", "answer": '["x"]', "at": now - 6 * 60000},                # generated
        {"item": "unit-1:reading1", "lesson": "1.4", "answer": '"true"', "at": now - 5 * 60000},              # with passage
    ]
    return {"version": 2, "cards": {}, "settings": {"direction": "both", "cardTypes": [], "sessionSize": 20, "syncCode": "", "autoSpeak": False, "showEnglish": True, "accents": "lenient"}, "log": [],
            "course": {"lessons": done, "tests": {}, "skills": skills, "errors": errors, "rereads": {}, "goal": {"minutesPerDay": 15}, "activity": []}}


def stored(page: Page) -> dict:
    return json.loads(page.evaluate("localStorage.getItem('attic.srs.v1')"))


def uncleared_keys(doc: dict) -> set[str]:
    return {f"{e['lesson']}|{e['item']}" for e in doc["course"]["errors"] if e.get("cleared") is None}


def run_deck(page: Page, items: list[dict], wrong: frozenset[str] = frozenset(), label: str = "") -> None:
    """Answer the deck in display order (the page shows one item per card; an
    id shared by a question and a quiz item comes back twice, so the item on
    screen is found by its prompt). Items whose source is in `wrong` (true /
    false items) are answered wrongly."""
    remaining = list(items)
    total = int(page.locator(".exerciseCount").inner_text().split("/")[1])
    for n in range(total):
        expect(page.locator(".exerciseCount")).to_have_text(f"{n + 1} / {total}")
        text = page.locator(".exercise").inner_text()
        shown = [c for c in remaining if c.get("prompt") and c["prompt"] in text]
        item = (shown or [c for c in remaining if not c.get("prompt")] or remaining)[0]
        if item["source"] in wrong:
            assert item["type"] == "true-false-grc", item
            other = "ἀληθές" if item["answer"] == "false" else "ψευδές"
            page.locator(".exercise .option", has_text=other).click()
            page.get_by_role("button", name="Check").click()
            expect(page.locator(".feedback")).to_contain_text("Not quite")
        else:
            answer_item(page, item)
            page.get_by_role("button", name="Check").click()
            expect(page.locator(".feedback")).to_contain_text("Right")
        page.locator(".exerciseActions button").click()
        remaining = [c for c in remaining if c["source"] != item["source"]]
        print(f"    {label} {n + 1}: {item['id']} ({item['type']}, from {item['origin']['block'] or 'drill'})")


def main() -> int:
    course = api("/api/course")
    now = int(time.time() * 1000)
    doc = seeded_doc(course, now)
    detail = api("/api/course/skill/noun.decl2.dat.sg")
    assert detail["drillable"] and detail["paradigm"]
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        page = ctx.new_page()
        page.on("console", lambda m: print("  [console]", m.text) if m.type == "error" and "CERT" not in m.text else None)
        page.goto(f"{FRONT}/learn")
        page.evaluate("(d) => localStorage.setItem('attic.srs.v1', JSON.stringify(d))", doc)

        # ---- course home: Review card
        page.goto(f"{FRONT}/learn")
        review = page.locator(".reviewCard")
        expect(review.locator("li", has_text="Mistakes")).to_contain_text("5")
        expect(review.get_by_role("link", name="Skills")).to_have_attribute("href", "/progress")
        review.scroll_into_view_if_needed()
        review.screenshot(path=f"{SHOTS}/skills-01-home-review.png")
        print("home review card ok")

        # ---- skills grid
        review.get_by_role("link", name="Skills").click()
        expect(page.locator("h1")).to_have_text("Your skills")
        n_skills = len(course["skills"])
        expect(page.locator("[data-skill]")).to_have_count(n_skills)
        legend = page.get_by_label("Legend")
        expect(legend.locator("li", has_text="Mastered")).to_contain_text("1")
        expect(legend.locator("li", has_text="Weak")).to_contain_text("1")
        expect(legend.locator("li", has_text="Learning")).to_contain_text("2")
        expect(legend.locator("li", has_text="Strong")).to_contain_text("1")
        page.screenshot(path=f"{SHOTS}/skills-02-grid.png")
        cell = page.locator('[data-skill="noun.decl2.dat.sg"]')
        expect(cell).to_have_attribute("aria-label", "2nd declension, dative singular: Weak")
        cell.click()
        panel = page.locator("#skill-detail")
        expect(panel).to_contain_text("1 / 4")
        for lesson in detail["lessons"]:
            expect(panel.locator(f'a[href="/learn/lesson/{lesson["id"]}"]')).to_be_visible()
        expect(panel.get_by_role("link", name="See the paradigm")).to_have_attribute("href", f"/grammar/{detail['paradigm']}")
        panel.scroll_into_view_if_needed()
        page.screenshot(path=f"{SHOTS}/skills-03-detail.png")
        print("skills detail ok")

        # a non-drillable skill has no Practise button
        page.locator('[data-skill="read.comprehension"]').click()
        expect(page.locator("#skill-detail")).to_contain_text("no generated drill")
        expect(page.locator("#skill-detail").get_by_role("link", name="Practise")).to_have_count(0)

        # filters
        page.locator(".chips button", has_text="Weak").click()
        expect(page.locator("[data-skill]")).to_have_count(3)  # weak + two learning
        page.screenshot(path=f"{SHOTS}/skills-04-weak-filter.png", full_page=True)
        page.locator(".chips button", has_text="Met").click()
        expect(page.locator("[data-skill]")).to_have_count(5)

        # ---- Practise
        page.locator('[data-skill="noun.decl2.dat.sg"]').click()
        with page.expect_response(lambda r: "/api/course/drill" in r.url and r.status == 200) as info:
            page.locator("#skill-detail").get_by_role("link", name="Practise").click()
        items = info.value.json()["items"]
        assert items and all(i["skills"] == ["noun.decl2.dat.sg"] for i in items), items
        expect(page.locator("h1")).to_have_text("2nd declension, dative singular")
        page.screenshot(path=f"{SHOTS}/skills-05-practise.png")
        for n, item in enumerate(items):
            expect(page.locator(".exerciseCount")).to_have_text(f"{n + 1} / {len(items)}")
            answer_item(page, item)
            page.get_by_role("button", name="Check").click()
            expect(page.locator(".feedback")).to_contain_text("Right")
            page.locator(".exerciseActions button").click()
        expect(page.locator(".resultBig")).to_have_text("100 %")
        after = stored(page)["course"]["skills"]["noun.decl2.dat.sg"]
        assert after["total"] == 4 + len(items), after
        print(f"practise ok ({len(items)} items)")

        # ---- mistakes deck, round 1
        with page.expect_response(lambda r: "/api/course/items" in r.url) as info:
            page.goto(f"{FRONT}/practice/review?mode=mistakes")
        body = info.value.json()
        assert body["missing"] == ["1.1|1.1:e999"], body["missing"]
        expect(page.get_by_text("can no longer be rebuilt")).to_be_visible()
        expect(page.locator(".exerciseCount")).to_have_text("1 / 4")
        # the passage of the reading item is available above it
        expect(page.locator(".exercise details summary")).to_contain_text("The passage")
        page.locator(".exercise details summary").click()
        page.screenshot(path=f"{SHOTS}/skills-06-mistakes.png", full_page=True)
        page.get_by_role("button", name="Remove it").click()
        expect(page.get_by_text("can no longer be rebuilt")).to_have_count(0)
        # the shared id 1.1:q1 came back twice; the recorded answer "d" picks the quiz item
        assert sorted(i["origin"]["block"] for i in body["items"] if i["id"] == "1.1:q1") == ["questions", "quiz"]
        run_deck(page, body["items"], wrong={"1.4|unit-1:reading1"}, label="round 1")
        expect(page.locator(".resultBig")).to_have_text("75 %")
        doc1 = stored(page)
        assert uncleared_keys(doc1) == {"1.1|1.1:e1", "1.1|1.1:q1", "1.4|unit-1:formsg3", "1.4|unit-1:reading1"}, uncleared_keys(doc1)
        assert sum(1 for e in doc1["course"]["errors"] if e["item"] == "unit-1:reading1") == 2  # the new miss is logged
        print("mistakes round 1 ok")

        # ---- round 2: all right → three leave (the reading item needs one more)
        with page.expect_response(lambda r: "/api/course/items" in r.url) as info:
            page.get_by_role("button", name="Another round").click()
        run_deck(page, info.value.json()["items"], label="round 2")
        expect(page.locator(".stepDone")).to_contain_text("3 left the deck")
        page.screenshot(path=f"{SHOTS}/skills-07-mistakes-round2.png", full_page=True)
        assert uncleared_keys(stored(page)) == {"1.4|unit-1:reading1"}

        # ---- round 3: the last one leaves
        with page.expect_response(lambda r: "/api/course/items" in r.url) as info:
            page.get_by_role("button", name="Another round").click()
        run_deck(page, info.value.json()["items"], label="round 3")
        expect(page.locator(".stepDone")).to_contain_text("The deck is empty")
        assert uncleared_keys(stored(page)) == set()
        page.goto(f"{FRONT}/learn")
        expect(page.locator(".reviewCard li", has_text="Mistakes")).to_contain_text("—")
        page.locator(".reviewCard").screenshot(path=f"{SHOTS}/skills-08-home-after.png")
        print("mistakes deck cleared")
        ctx.close()
        browser.close()
    print(f"skills e2e OK · screenshots in {SHOTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
