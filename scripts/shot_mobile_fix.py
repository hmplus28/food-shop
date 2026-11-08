import asyncio
from playwright.async_api import async_playwright

FILE = '/home/z/my-project/download/فروشگاه-خانم-گل.html'

CLOSE = """() => {
  document.querySelectorAll('.overlay.open').forEach(o => o.classList.remove('open'));
  document.body.style.overflow = '';
}"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(f'file://{FILE}')
        await page.wait_for_timeout(1300)
        await page.evaluate(CLOSE)
        await page.wait_for_timeout(400)
        await page.screenshot(path='/tmp/verify/mobile_top2.png')
        await page.screenshot(path='/tmp/verify/mobile_full2.png', full_page=True)
        await browser.close()

asyncio.run(main())
