"""Navigation, layout and accessibility walk over every route.

For each route at a phone (390×844) and a desktop (1280×900) viewport:

- the primary nav is visible; on the phone it is the bottom tab bar and it
  does not overlap the Reader's player bar or the lesson's step bar;
- no horizontal overflow (scrollWidth <= innerWidth), also at 360 px;
- the first Tab lands on a visible "Skip to content" link that moves focus
  to <main>; the next Tabs show a visible focus ring;
- axe-core (frontend/node_modules/axe-core) finds no serious or critical
  violations.

A keyboard check drives a choice exercise with arrow keys and Space.

Setup as in e2e_course.py (fake-voice API + built frontend). E2E_FRONT /
E2E_API pick the servers, FONTS routes Google Fonts to local copies
(see e2e_stage2.route_fonts), NAV_SHOTS is the screenshot folder,
NAV_LABEL prefixes screenshot names ("before" / "after"), NAV_STRICT=0
reports problems without failing (for a baseline run).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import Page, sync_playwright  # noqa: E402

from e2e_course import API, CHROME, FRONT, api  # noqa: E402
from e2e_stage2 import route_fonts  # noqa: E402

SHOTS = Path(os.environ.get("NAV_SHOTS", tempfile.mkdtemp(prefix="attic-nav-")))
LABEL = os.environ.get("NAV_LABEL", "after")
STRICT = os.environ.get("NAV_STRICT", "1") != "0"
AXE = Path(__file__).resolve().parents[3] / "frontend/node_modules/axe-core/axe.min.js"
VIEWPORTS = {"phone": {"width": 390, "height": 844}, "desktop": {"width": 1280, "height": 900}}

problems: list[str] = []


def problem(msg: str) -> None:
    problems.append(msg)
    print("  !!", msg)


def routes() -> list[tuple[str, str]]:
    course = api("/api/course")
    grammar = api("/api/grammar")
    vocab = api("/api/vocab")
    track = course["tracks"][0]["id"] if course.get("tracks") else None
    test = next((u["test"] for s in course["stages"] for u in s["units"] if u.get("test")), "unit-1")
    word = next((i["id"] for i in vocab["items"] if i["lemma"] == "λόγος"), vocab["items"][0]["id"])
    out = [
        ("home", "/"),
        ("start", "/start"),
        ("help", "/help"),
        ("settings", "/settings"),
        ("practice", "/practice"),
        ("quick", "/practice/quick"),
        ("add-text", "/library/new"),
        ("reader", "/library"),
        ("course", "/learn"),
        ("lesson", "/learn/lesson/1.1"),
        ("lesson-read", "/learn/lesson/1.3?step=2"),
        ("lesson-exercises", "/learn/lesson/1.1?step=6"),
        ("test", f"/learn/test/{test}"),
        ("placement", "/learn/placement?seed=1"),
        ("review", "/practice/review"),
        ("credits", "/learn/credits"),
        ("skills", "/progress"),
        ("vocab", "/words"),
        ("vocab-word", f"/words/{word}"),
        ("grammar", "/grammar"),
        ("grammar-item", f"/grammar/{[i for s in grammar['sections'] for i in s['items']][1]['id']}"),
    ]
    if track:
        out.insert(6, ("track", f"/learn/track/{track}"))
    return out


def rect(page: Page, selector: str) -> dict | None:
    return page.evaluate(
        """(sel) => { const el = [...document.querySelectorAll(sel)].find(e => { const s = getComputedStyle(e); return s.display !== 'none' && s.visibility !== 'hidden' && e.getBoundingClientRect().height > 0; });
             if (!el) return null; const r = el.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, left: r.left, right: r.right, height: r.height}; }""",
        selector,
    )


def overlaps(a: dict, b: dict) -> bool:
    return a["top"] < b["bottom"] - 0.5 and b["top"] < a["bottom"] - 0.5 and a["left"] < b["right"] and b["left"] < a["right"]


def check_nav(page: Page, name: str, vp: str) -> None:
    # a focused text field hides the phone tab bar on purpose (on-screen keyboard)
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.wait_for_timeout(100)
    nav = rect(page, "nav[aria-label='Main'], nav[aria-label='Main mobile']")
    if not nav:
        problem(f"{vp} {name}: primary nav not visible")
        return
    if vp == "phone":
        tabs = rect(page, ".tabBar")
        if not tabs:
            problem(f"{vp} {name}: bottom tab bar not visible")
            return
        vh = page.evaluate("innerHeight")
        if abs(tabs["bottom"] - vh) > 1:
            problem(f"{vp} {name}: tab bar not pinned to the bottom ({tabs['bottom']} vs {vh})")
        for sel in (".playerBar", ".gradeBar", ".lessonFooter"):
            page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
            page.wait_for_timeout(250)
            other = rect(page, sel)
            if other and overlaps(other, tabs):
                problem(f"{vp} {name}: {sel} overlaps the tab bar")
        # the last thing on the page must be reachable above the fixed bars
        page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        page.wait_for_timeout(250)
        last = page.evaluate(
            """() => { const main = document.querySelector('main'); if (!main) return null;
                 const els = [...main.querySelectorAll('*')].filter(e => { const s = getComputedStyle(e); return s.position !== 'fixed' && !e.closest('.playerBar, .gradeBar') && e.getBoundingClientRect().height > 0 && e.children.length === 0; });
                 const el = els[els.length - 1]; if (!el) return null; const r = el.getBoundingClientRect(); return {bottom: r.bottom, text: (el.textContent || el.tagName).slice(0, 40)}; }"""
        )
        covers = [r for r in (rect(page, ".tabBar"), rect(page, ".playerBar"), rect(page, ".gradeBar")) if r]
        top_of_bars = min(r["top"] for r in covers)
        if last and last["bottom"] > top_of_bars + 1:
            problem(f"{vp} {name}: last content ({last['text']!r}) hidden under the fixed bars ({last['bottom']:.0f} > {top_of_bars:.0f})")
    active = page.evaluate("[...document.querySelectorAll('[aria-current=\"page\"]')].map(e => e.textContent.trim())")
    if not active and name not in {"skills"}:
        problem(f"{vp} {name}: no aria-current=page in the nav")


def check_overflow(page: Page, name: str, vp: str) -> None:
    over = page.evaluate("document.documentElement.scrollWidth - innerWidth")
    if over > 0:
        wide = page.evaluate(
            """() => [...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && !e.closest('.tableWrap, .scrollX')).slice(0, 3).map(e => e.tagName + '.' + (e.className && e.className.baseVal === undefined ? e.className : ''))"""
        )
        problem(f"{vp} {name}: horizontal overflow {over}px {wide}")


def check_keyboard(page: Page, name: str, vp: str) -> None:
    page.evaluate("window.scrollTo(0, 0)")
    # reset the sequential-focus starting point to the top of the document
    page.evaluate("(() => { const s = document.createElement('span'); s.tabIndex = -1; document.body.prepend(s); s.focus(); s.blur(); s.remove(); })()")
    page.keyboard.press("Tab")
    first = page.evaluate(
        "(() => { const e = document.activeElement; const r = e.getBoundingClientRect(); return {cls: e.className, text: (e.textContent||'').trim(), href: e.getAttribute('href'), visible: r.width > 0 && r.height > 0 && r.top >= 0}; })()"
    )
    if "skip" not in str(first.get("cls", "")).lower() or not first["visible"]:
        problem(f"{vp} {name}: first Tab is not a visible skip link ({first})")
    else:
        page.keyboard.press("Enter")
        page.wait_for_timeout(100)
        inside = page.evaluate("(() => { const a = document.activeElement; return !!a && (a.id === 'main' || !!a.closest('main') || !!a.closest('#main')); })()")
        if not inside:
            problem(f"{vp} {name}: skip link does not move focus into <main>")
    missing = []
    for _ in range(8):
        page.keyboard.press("Tab")
        info = page.evaluate(
            """(() => { const e = document.activeElement; if (!e || e === document.body) return null; const s = getComputedStyle(e);
                 const ring = (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || (s.boxShadow && s.boxShadow !== 'none');
                 return {tag: e.tagName, cls: String(e.className).slice(0, 40), text: (e.textContent||'').trim().slice(0, 24), ring}; })()"""
        )
        if info and not info["ring"]:
            missing.append(info)
    if missing:
        problem(f"{vp} {name}: focus without a visible ring: {missing[:3]}")


def run_axe(page: Page, name: str, vp: str, report: dict) -> None:
    if not AXE.exists():
        return
    page.add_script_tag(path=str(AXE))
    res = page.evaluate(
        """async () => { const r = await axe.run(document, {resultTypes: ['violations']});
             return r.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length, sample: v.nodes.slice(0, 2).map(n => n.target.join(' '))})); }"""
    )
    report[f"{vp} {name}"] = res
    bad = [v for v in res if v["impact"] in {"serious", "critical"}]
    for v in bad:
        problem(f"{vp} {name}: axe {v['impact']} {v['id']} ×{v['nodes']} ({v['help']}) {v['sample']}")


def prepare_reader(page: Page) -> None:
    """Load a library passage so the player bar is on screen."""
    reading = page.locator("button.reading").first
    if reading.count():
        reading.click()
        page.wait_for_selector(".playerBar", timeout=30000)
        page.wait_for_selector(".sentence:not(.pending)", timeout=30000)


def keyboard_exercise(page: Page) -> None:
    """Arrow keys move between choice options, Space picks one, Enter checks."""
    page.goto(f"{FRONT}/learn/lesson/0.1?step=0")
    page.wait_for_selector(".stepDot", timeout=15000)
    dots = page.locator(".stepDot")
    for i in range(dots.count()):
        # the stepper is operable from the keyboard: focus a step, press Enter
        dots.nth(i).focus()
        page.keyboard.press("Enter")
        page.wait_for_timeout(150)
        if "Μελετήματα" in page.locator(".stepName").inner_text():
            break
    page.wait_for_selector(".exercise", timeout=15000)
    if not page.locator(".option").count():
        print("  (no choice item first in 0.1 exercises; keyboard choice check skipped)")
        return
    page.locator(".option").first.focus()
    page.keyboard.press("ArrowDown")
    moved = page.evaluate("document.activeElement.classList.contains('option') && document.activeElement !== document.querySelector('.option')")
    if not moved:
        problem("keyboard: ArrowDown does not move between choice options")
    page.keyboard.press("Space")
    checked = page.evaluate("document.activeElement.getAttribute('aria-checked')")
    if checked != "true":
        problem(f"keyboard: Space does not select the focused option (aria-checked={checked})")


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    print(f"front {FRONT} · api {API} · shots {SHOTS} · label {LABEL}")
    report: dict = {}
    todo = routes()
    now = int(time.time() * 1000)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        for vp, size in VIEWPORTS.items():
            ctx = browser.new_context(viewport=size, device_scale_factor=2 if vp == "phone" else 1)
            route_fonts(ctx)
            page = ctx.new_page()
            page.on("pageerror", lambda e: problem(f"page error: {e}"))
            # a little progress so the course home shows the review card, a done lesson, a streak
            page.goto(f"{FRONT}/learn")
            page.evaluate(
                """(now) => { const k = 'attic.srs.v1'; const p = JSON.parse(localStorage.getItem(k) || 'null');
                     if (p && p.course) { p.course.lessons['0.1'] = {status: 'done', best: 1, attempts: 1, firstDone: now, lastDone: now, updated: now}; localStorage.setItem(k, JSON.stringify(p)); } }""",
                now,
            )
            for name, path in todo:
                resp = page.goto(f"{FRONT}{path}")
                if resp is not None and resp.status == 404:
                    print(f"  {vp} {name}: 404, skipped")
                    continue
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(400)
                if name == "reader":
                    prepare_reader(page)
                check_nav(page, name, vp)
                check_overflow(page, name, vp)
                page.evaluate("window.scrollTo(0, 0)")
                page.screenshot(path=str(SHOTS / f"{LABEL}-{vp}-{name}.png"), full_page=True)
                if name == "reader" and vp == "phone":
                    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                    page.wait_for_timeout(300)
                    page.screenshot(path=str(SHOTS / f"{LABEL}-{vp}-{name}-bottom.png"))
                check_keyboard(page, name, vp)
                run_axe(page, name, vp, report)
                print(f"  {vp} {name} checked")
            if vp == "phone":
                # 360 px: the narrowest phone we support
                page.set_viewport_size({"width": 360, "height": 740})
                for name, path in todo:
                    resp = page.goto(f"{FRONT}{path}")
                    if resp is not None and resp.status == 404:
                        continue
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(300)
                    check_overflow(page, name, "360px")
                page.set_viewport_size(size)
                keyboard_exercise(page)
            ctx.close()
        browser.close()
    (SHOTS / f"axe-{LABEL}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    counts: dict[str, int] = {}
    for vs in report.values():
        for v in vs:
            counts[f"{v['impact']}:{v['id']}"] = counts.get(f"{v['impact']}:{v['id']}", 0) + 1
    print("axe violations (pages affected):", json.dumps(dict(sorted(counts.items())), ensure_ascii=False))
    print(f"{len(problems)} problems")
    if problems and STRICT:
        print("E2E NAV FAILED")
        return 1
    print("E2E NAV PASSED" if not problems else "E2E NAV (report only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
