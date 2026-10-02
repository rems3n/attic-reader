"""Real API/catalog integration at desktop and phone sizes; no synthesis on open."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
FRONT=os.getenv('E2E_FRONT','http://localhost:3000')
SHOTS=Path(os.getenv('E2E_SHOTS','/tmp/library-shots'));SHOTS.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch()
    for name,width in [('desktop',1280),('phone',390)]:
        page=browser.new_page(viewport={'width':width,'height':900 if width>400 else 844})
        errors=[]; audio=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:audio.append(r.url) if '/api/synthesize' in r.url else None)
        page.goto(FRONT+'/library'); expect(page.locator('.catalogWork').first).to_be_visible()
        assert page.locator('.catalogWork').count()==8
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(SHOTS/f'{name}-library.png'),full_page=True)
        page.get_by_label('Author',exact=True).select_option('Xenophon')
        page.get_by_label('Search texts',exact=True).fill('Oeconomicus')
        expect(page.locator('.catalogWork')).to_have_count(1)
        page.reload();expect(page.get_by_label('Search texts',exact=True)).to_have_value('Oeconomicus')
        page.locator('.catalogWork summary').click()
        page.screenshot(path=str(SHOTS/f'{name}-filtered.png'),full_page=True)
        page.locator('.catalogPassage').first.click()
        expect(page.locator('.originalGreek')).to_be_visible()
        assert len(page.locator('.originalGreek').inner_text())>200
        assert audio==[],audio
        assert page.get_by_role('link',name='Source edition').get_attribute('href').startswith('https://github.com/PerseusDL/')
        page.get_by_role('button',name='Next passage →',exact=True).click()
        expect(page).to_have_url(__import__('re').compile('reading=perseus-0032-003-02'))
        page.screenshot(path=str(SHOTS/f'{name}-reading.png'),full_page=True)
        page.get_by_role('button',name='← Back to library',exact=True).click()
        expect(page.get_by_label('Search texts',exact=True)).to_have_value('Oeconomicus')
        page.get_by_label('Search texts',exact=True).fill('no-such-work-xyz');expect(page.get_by_text('No matching readings',exact=True)).to_be_visible()
        page.get_by_role('button',name='Clear filters',exact=True).first.click()
        page.get_by_role('button',name='Passages',exact=True).click();expect(page.locator('.catalogPassage')).to_have_count(20)
        page.get_by_label('Sort',exact=True).select_option('shortest')
        page.get_by_role('button',name='Next',exact=True).click();expect(page.get_by_text('Page 2 of 17',exact=True)).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.goto(FRONT+'/library?reading=perseus-0032-003-01')
        expect(page.locator('.originalGreek')).to_be_visible()
        page.get_by_role('button',name='Listen to this passage',exact=True).click()
        expect(page.locator('.playerBar')).to_be_visible(timeout=30000)
        expect(page.get_by_role('button',name='Play all',exact=True)).to_be_enabled(timeout=30000)
        assert not errors,errors
        page.close()
    browser.close()
print('PASS: desktop/phone search, filters, sort, pagination, source links, text-first reading, sequence navigation, audio and overflow')
