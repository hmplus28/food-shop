import asyncio, json
from playwright.async_api import async_playwright

BASE = 'http://localhost:4173/food-shop'
errors = []

async def close_popups(page):
    try:
        await page.evaluate("document.querySelectorAll('.overlay.open').forEach(o=>o.classList.remove('open'));document.body.style.overflow=''")
        await page.wait_for_timeout(200)
    except Exception:
        pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={'width': 1366, 'height': 900})
        page = await ctx.new_page()
        page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
        page.on('console', lambda m: errors.append(f'console.error: {m.text}') if m.type == 'error' else None)

        # ---- Home ----
        await page.goto(BASE + '/', wait_until='networkidle')
        await close_popups(page)
        home = await page.evaluate("""() => ({
            title: document.title,
            h1: document.querySelector('h1')?.textContent.trim(),
            packs: document.querySelectorAll('.pack').length,
            cats: document.querySelectorAll('.cat-card').length,
            amz: document.querySelectorAll('#amazing .p-card').length,
            best: document.querySelectorAll('#best .p-card').length,
            trust: !!document.querySelector('.trust-card'),
            why: document.querySelectorAll('.why-card').length,
            canonical: document.querySelector('link[rel=canonical]')?.href,
        })""")
        print('HOME:', json.dumps(home, ensure_ascii=False))
        await page.screenshot(path='/tmp/verify/vue_home.png')

        # ---- Product detail ----
        await page.goto(BASE + '/product/1', wait_until='networkidle')
        prod = await page.evaluate("""() => ({
            h1: document.querySelector('h1')?.textContent.trim(),
            jsonld: [...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>s.id||'static').join(','),
            price: document.querySelector('.pv')?.textContent,
        })""")
        print('PRODUCT:', json.dumps(prod, ensure_ascii=False))
        # add to cart
        await page.click('.pd-actions .btn-brand')
        await page.wait_for_timeout(400)
        badge = await page.locator('.cart-btn .cart-count').text_content()
        print('CART BADGE:', badge)

        # ---- Products filter ----
        await page.goto(BASE + '/products?cat=pistachio', wait_until='networkidle')
        n = await page.locator('.shop-grid .p-card').count()
        print('FILTER pistachio cards:', n)
        await page.goto(BASE + '/products?q=زعفران', wait_until='networkidle')
        n2 = await page.locator('.shop-grid .p-card').count()
        print('SEARCH زعفران cards:', n2)

        # ---- Cart -> Checkout ----
        await page.goto(BASE + '/cart', wait_until='networkidle')
        await page.screenshot(path='/tmp/verify/vue_cart.png')
        await page.goto(BASE + '/checkout', wait_until='networkidle')
        await page.fill('input[placeholder="مثلاً سارا محمدی"]', 'سارا محمدی')
        await page.fill('input[placeholder="۰۹۱۲۳۴۵۶۷۸۹"]', '09123456789')
        await page.fill('input[placeholder="مثلاً تهران"]', 'تهران')
        await page.fill('textarea', 'خیابان ولیعصر، پلاک ۱۲')
        await page.click('.co-pay-btn')
        await page.wait_for_timeout(300)
        await page.click('.co-pay-btn.btn-brand.btn-lg')  # پرداخت
        await page.wait_for_timeout(2200)
        code = await page.locator('.ord-code').text_content()
        print('ORDER CODE:', code)

        # ---- Track ----
        await page.goto(BASE + '/track?code=' + code.strip(), wait_until='networkidle')
        tl = await page.locator('.tl-item').count()
        print('TRACK timeline items:', tl)

        # ---- Auth -> Account ----
        await page.goto(BASE + '/auth', wait_until='networkidle')
        await page.click('.auth-tabs button:nth-child(2)')
        await page.fill('input[placeholder="مثلاً سارا محمدی"]', 'سارا محمدی')
        await page.fill('input[placeholder="۰۹۱۲۳۴۵۶۷۸۹"]', '09123456789')
        await page.fill('input[placeholder="حداقل ۴ کاراکتر"]', '1234')
        await page.click('.auth-form .btn-gold')
        await page.wait_for_timeout(600)
        acc = page.url
        print('AFTER AUTH URL:', acc)
        stats = await page.locator('.up-stat').count()
        print('ACCOUNT stats:', stats)

        # ---- Admin ----
        await page.goto(BASE + '/admin', wait_until='networkidle')
        await page.fill('input[autocomplete="username"]', 'admin')
        await page.fill('input[autocomplete="current-password"]', 'admin1234')
        await page.click('.admin-login .btn-brand')
        await page.wait_for_timeout(400)
        rows = await page.locator('.tbl tbody tr').count()
        print('ADMIN product rows:', rows)
        await page.screenshot(path='/tmp/verify/vue_admin.png')

        await ctx.close()

        # ---- Mobile visual ----
        ctx2 = await browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, device_scale_factor=2)
        page2 = await ctx2.new_page()
        page2.on('pageerror', lambda e: errors.append(f'M pageerror: {e}'))
        await page2.goto(BASE + '/', wait_until='networkidle')
        await close_popups(page2)
        await page2.screenshot(path='/tmp/verify/vue_mobile.png', full_page=True)
        await ctx2.close()
        await browser.close()
        print('JS ERRORS:', errors if errors else 'NONE')

asyncio.run(main())
