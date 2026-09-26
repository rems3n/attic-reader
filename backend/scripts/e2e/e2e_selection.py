"""Selection lookup, desktop and touch viewport, using the real dictionary API."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from e2e_course import FRONT, CHROME
from e2e_stage2 import route_fonts

shots = Path(os.environ.get('E2E_SHOTS', '../docs/screenshots/selection'))
shots.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
    for label, width, touch in [('phone', 390, True), ('desktop', 1280, False)]:
        ctx = browser.new_context(viewport={'width': width, 'height': 844 if touch else 900}, has_touch=touch, is_mobile=touch)
        route_fonts(ctx)
        page = ctx.new_page()
        page.goto(FRONT + '/help')
        page.locator('main').evaluate("e => { const p = document.createElement('p'); p.id='selection-fixture'; p.lang='grc'; p.textContent='ἀνθρώπου λόγος ζζζζζ'; e.prepend(p); }")
        def select(start, end):
            page.evaluate("""([start,end]) => {const n=document.querySelector('#selection-fixture').firstChild;const r=document.createRange();r.setStart(n,start);r.setEnd(n,end);const s=window.getSelection();s.removeAllRanges();s.addRange(r);} """, [start,end])
        select(0,8)
        dialog = page.get_by_role('dialog', name='English definition')
        expect(dialog).to_be_visible(timeout=30000)
        expect(dialog.get_by_role('link', name='ἄνθρωπος', exact=True)).to_be_visible(timeout=30000)
        page.screenshot(path=str(shots / f'{label}-definition.png'))
        box=dialog.bounding_box()
        assert box['x'] >= 0 and box['x'] + box['width'] <= width + 1
        page.keyboard.press('Escape')
        expect(dialog).not_to_be_visible()
        select(9,14)
        expect(dialog.get_by_role('link', name='λόγος', exact=True)).to_be_visible(timeout=30000)
        select(15,20)
        expect(dialog.get_by_text('No definition found in the app’s dictionary.')).to_be_visible(timeout=30000)
        select(0,20)
        expect(dialog.get_by_text('This is a word-by-word lookup.', exact=False)).to_be_visible(timeout=30000)
        page.get_by_role('button', name='Close definition').click()
        expect(dialog).not_to_be_visible()
        # The Greek editor also supports selection without interrupting editing.
        page.goto(FRONT + '/library/new')
        editor = page.locator('textarea[lang="grc"]')
        editor.fill('ἀνθρώπου')
        editor.evaluate('e => {e.focus();e.setSelectionRange(0,8);e.dispatchEvent(new Event("select", {bubbles:true}));}')
        expect(dialog.get_by_role('link', name='ἄνθρωπος', exact=True)).to_be_visible(timeout=30000)
        ctx.close()
    browser.close()
print('E2E SELECTION PASSED')
