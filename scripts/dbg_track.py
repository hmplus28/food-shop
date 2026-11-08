import asyncio
from playwright.async_api import async_playwright

BASE = 'http://localhost:4173/food-shop'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        msgs = []
        page.on('console', lambda m: msgs.append(f'{m.type}: {m.text}'))
        page.on('pageerror', lambda e: msgs.append(f'PAGEERROR: {e}'))
        await page.goto(BASE + '/track', wait_until='networkidle')
        await page.evaluate("""() => {
            localStorage.setItem('asalat_orders', JSON.stringify([{
                code:'AS-1024', ts: Date.now()-9*60000,
                items:[{pid:1,w:500,qty:1}], sub:990000, off:0, coupon:null,
                shipCost:89000, shipType:'peyk', total:1079000,
                addr:{name:'سارا', phone:'09123456789', prov:'تهران', city:'تهران', addr:'ولیعصر'}, status:1
            }]));
        }""")
        await page.goto(BASE + '/track?code=AS-1024', wait_until='networkidle')
        await page.wait_for_timeout(800)
        info = await page.evaluate("""() => {
            const crumbs = document.querySelector('.crumbs')?.innerText;
            const main = document.querySelector('#main');
            return {
                crumbs,
                url: location.href,
                mainLen: main?.innerHTML.length,
                mainHead: main?.innerHTML.slice(0, 600),
            };
        }""")
        for k, v in info.items(): print(k, '=>', str(v)[:300])
        print('CONSOLE:', msgs[:8])
        await browser.close()

asyncio.run(main())
