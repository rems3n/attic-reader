"""Selection lookup, desktop and touch viewport, using the real dictionary API."""
import os
import json
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
        requests = []
        def translate(route):
            payload = route.request.post_data_json
            requests.append(payload)
            route.fulfill(status=200, content_type='application/json', body=json.dumps({'translation': 'Translated selection: ' + payload['text'], 'source': 'ai'}))
        ctx.route('**/api/translate', translate)
        page = ctx.new_page()
        page.goto(FRONT + '/help')
        page.locator('main').evaluate("e => { const p = document.createElement('p'); p.id='selection-fixture'; p.lang='grc'; p.textContent='ἀνθρώπου λόγος ζζζζζ'; e.prepend(p); }")
        def select(start, end):
            page.evaluate("""([start,end]) => {const n=document.querySelector('#selection-fixture').firstChild;const r=document.createRange();r.setStart(n,start);r.setEnd(n,end);const s=window.getSelection();s.removeAllRanges();s.addRange(r);} """, [start,end])
        select(0,8)
        dialog = page.get_by_role('dialog', name='English translation')
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
        expect(dialog.get_by_text('Translated selection: ἀνθρώπου λόγος ζζζζζ', exact=True)).to_be_visible(timeout=30000)
        expect(dialog.get_by_role('heading', name='Word definitions')).to_be_visible()
        translation_box = dialog.get_by_label('Translation', exact=True).bounding_box()
        definitions_box = dialog.get_by_role('heading', name='Word definitions').bounding_box()
        assert translation_box['y'] < definitions_box['y']
        assert requests[-1]['text'] == 'ἀνθρώπου λόγος ζζζζζ'
        assert requests[-1]['context'] == 'ἀνθρώπου λόγος ζζζζζ'
        page.get_by_role('button', name='Close translation').click()
        expect(dialog).not_to_be_visible()
        # The Greek editor also supports selection without interrupting editing.
        page.goto(FRONT + '/library/new')
        editor = page.locator('textarea[lang="grc"]')
        editor.fill('ἀνθρώπου')
        editor.evaluate('e => {e.focus();e.setSelectionRange(0,8);e.dispatchEvent(new Event("select", {bubbles:true}));}')
        expect(dialog.get_by_role('link', name='ἄνθρωπος', exact=True)).to_be_visible(timeout=30000)
        # Provider failure keeps dictionary definitions usable and offers retry.
        ctx.unroute('**/api/translate')
        ctx.route('**/api/translate', lambda route: route.fulfill(status=503, content_type='application/json', body=json.dumps({'detail': 'Translation unavailable.'})))
        editor.fill('λόγος')
        editor.evaluate('e => {e.focus();e.setSelectionRange(0,5);e.dispatchEvent(new Event("select", {bubbles:true}));}')
        expect(dialog.get_by_text('Translation unavailable.', exact=True)).to_be_visible(timeout=30000)
        expect(dialog.get_by_role('link', name='λόγος', exact=True)).to_be_visible()
        expect(dialog.get_by_role('button', name='Retry translation')).to_be_visible()
        ctx.close()
    browser.close()
print('E2E SELECTION PASSED')
