"""Image catalog: phone/desktop, filtering, real context, export, and dialogs."""
import os
import csv
import io
from pathlib import Path
from app.course.image_catalog import image_catalog
from playwright.sync_api import sync_playwright, expect
from e2e_course import FRONT, CHROME
from e2e_stage2 import route_fonts

SHOTS = Path(os.environ.get('E2E_SHOTS', '../docs/screenshots/f1'))
SHOTS.mkdir(parents=True, exist_ok=True)
catalog = image_catalog()
remaining_story_ids = {i['id'] for i in catalog['images'] if i['status'] == 'remaining' and i['kind'] == 'story'}
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
    for name, size in [('phone', {'width':390, 'height':844}), ('desktop', {'width':1280, 'height':900})]:
        context = browser.new_context(viewport=size, accept_downloads=True)
        route_fonts(context)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(f'{FRONT}/admin/images')
        expect(page.get_by_role('heading', name='Every picture, in context')).to_be_visible()
        expect(page.get_by_role('button', name='633 All images')).to_be_visible()
        search = page.get_by_role('searchbox')
        search.fill('hemera')
        expect(page.get_by_role('status')).to_contain_text('1 matching images')
        page.screenshot(path=str(SHOTS / f'{name}-image-admin.png'), full_page=True)
        page.get_by_role('button', name='View details: hemera').click()
        dialog = page.get_by_role('dialog')
        expect(dialog).to_be_visible()
        expect(dialog).to_contain_text('day')
        expect(dialog.get_by_role('link', name='1.4 · Chrysis at home').first).to_be_visible()
        expect(dialog.locator('img')).to_have_count(1)
        page.wait_for_function("document.querySelector('dialog img').naturalWidth > 0")
        page.screenshot(path=str(SHOTS / f'{name}-image-context.png'), full_page=False)
        page.keyboard.press('Escape')
        expect(dialog).not_to_be_visible()
        page.get_by_role('button', name='Clear filters').click()
        page.get_by_label('Status', exact=True).select_option('remaining')
        page.get_by_label('Purpose', exact=True).select_option('story')
        expect(page.get_by_role('status')).to_contain_text(f'{len(remaining_story_ids)} matching images')
        with page.expect_download() as download_info:
            page.get_by_role('button', name='Export current list').click()
        download = download_info.value
        exported = Path(download.path()).read_text(encoding='utf-8-sig')
        rows = list(csv.reader(io.StringIO(exported)))
        assert {row[0] for row in rows[1:]} == remaining_story_ids
        page.get_by_role('button', name='Clear filters').click()
        search.fill('κυων')
        expect(page.get_by_role('button', name='View details: kyon', exact=True)).to_be_visible()
        search.fill('zzzz-no-such-image')
        expect(page.get_by_role('heading', name='No matching images')).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        assert not errors, errors
        context.close()
    browser.close()
print('Image dashboard passed at phone and desktop sizes.')
