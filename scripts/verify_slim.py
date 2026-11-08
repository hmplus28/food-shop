import asyncio, json, os
from playwright.async_api import async_playwright

FILE = '/home/z/my-project/download/فروشگاه-خانم-گل.html'
os.makedirs('/tmp/verify', exist_ok=True)

CHECK_JS = """() => {
  const q = s => document.querySelectorAll(s).length;
  const anchors = [...document.querySelectorAll('a[href^="#"], [data-scroll]')]
      .map(a => (a.getAttribute('href') || a.getAttribute('data-scroll')))
      .filter(h => h && h.length > 1 && !h.startsWith('#!'));
  const missing = [...new Set(anchors)].filter(h => { try { return !document.querySelector(h); } catch(e){ return true; } });
  return {
    announce: q('.announce'), services: q('.services'), srv: q('.srv'),
    slides: q('#heroSlides .slide'),
    heroTitle: document.querySelector('#heroSlides .s-title') ? document.querySelector('#heroSlides .s-title').textContent.trim() : null,
    sections: Object.fromEntries(['packs','cats','amazing','best','etemad','consult','why'].map(id => [id, !!document.getElementById(id)])),
    whyCards: q('#why .why-card'),
    missingAnchors: missing,
    bodyH: document.body.scrollHeight
  };
}"""

async def close_popup(page):
    try:
        if await page.locator('.overlay.open').count() > 0:
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(400)
    except Exception:
        pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        errors = []
        # ---- Desktop ----
        ctx = await browser.new_context(viewport={'width': 1366, 'height': 900})
        page = await ctx.new_page()
        page.on('pageerror', lambda e: errors.append(f'D pageerror: {e}'))
        page.on('console', lambda m: errors.append(f'D console.{m.type}: {m.text}') if m.type == 'error' else None)
        await page.goto(f'file://{FILE}')
        await page.wait_for_timeout(1300)
        await close_popup(page)
        info = await page.evaluate(CHECK_JS)
        print('DESKTOP:', json.dumps(info, ensure_ascii=False))
        await page.screenshot(path='/tmp/verify/desktop_top.png')
        await page.screenshot(path='/tmp/verify/desktop_full.png', full_page=True)
        await ctx.close()
        # ---- Mobile ----
        ctx2 = await browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, device_scale_factor=2)
        page2 = await ctx2.new_page()
        page2.on('pageerror', lambda e: errors.append(f'M pageerror: {e}'))
        page2.on('console', lambda m: errors.append(f'M console.{m.type}: {m.text}') if m.type == 'error' else None)
        await page2.goto(f'file://{FILE}')
        await page2.wait_for_timeout(1300)
        await close_popup(page2)
        info2 = await page2.evaluate(CHECK_JS)
        print('MOBILE :', json.dumps(info2, ensure_ascii=False))
        await page2.screenshot(path='/tmp/verify/mobile_top.png')
        await page2.screenshot(path='/tmp/verify/mobile_full.png', full_page=True)
        await ctx2.close()
        await browser.close()
        print('JS ERRORS:', errors if errors else 'NONE')

asyncio.run(main())
