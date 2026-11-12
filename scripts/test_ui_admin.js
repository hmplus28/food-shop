// تست رابط با بک‌اند واقعی: سوپریوزر/تم سراسری، ورود بدون کد، پنل ادمین، فلش‌ها، نوار سبد موبایل، فونت آفلاین، کردیت دایناکد
// پیش‌نیاز: بک‌اند روی 8787 (migrate+seed) و سایت ساخته‌شده با API روشن روی 4174:
//   cd app && VITE_BASE=/ VITE_API_ENABLED=true VITE_API_BASE=http://127.0.0.1:8787/api/v1 npx vite build --outDir /tmp/ui-dist && npx vite preview --outDir /tmp/ui-dist --port 4174
// اجرا:  ADMIN_PASSWORD=... node scripts/test_ui_admin.js
const { chromium } = require('playwright');
const U = process.env.UI_URL || 'http://localhost:4174/';
const API = process.env.API_URL || 'http://127.0.0.1:8787/api/v1';
const ADMIN_PHONE = process.env.ADMIN_PHONE || '09120000000';
const ADMIN_PASS = process.env.ADMIN_PASSWORD || 'admin1234';
let bad = 0;
const t = (n, c, d = '') => { if (!c) bad++; console.log((c ? '✓ ' : '✗ ') + n + (c ? '' : '  → ' + d)); };
const suffix = String(Date.now()).slice(-7);

(async () => {
  const b = await chromium.launch();
  // ---------- ناشناس ----------
  const anon = await b.newContext({ viewport: { width: 1280, height: 900 } });
  const reqs = [];
  anon.on('request', r => reqs.push(r.url()));
  const p = await anon.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(U, { waitUntil: 'networkidle' });
  await p.waitForTimeout(2200);                                     // کارت شانس بعد از ~۱٫۶ ثانیه
  t('کارت شانس برای مهمان خودکار باز نمی‌شود (فقط با دکمه)', await p.locator('.overlay.open[aria-label="کارت شانس"]').count() === 0);
  await p.locator('.fab.gold').click(); await p.waitForTimeout(500);
  t('کارت شانس با دکمه باز می‌شود', await p.locator('.overlay.open[aria-label="کارت شانس"]').count() === 1);
  t('کارت شانس دکمهٔ × دارد', await p.locator('.lucky-x').count() === 1);
  await p.locator('.lucky-x').click(); await p.waitForTimeout(300);
  t('دکمهٔ × کارت شانس را می‌بندد', await p.locator('.overlay.open[aria-label="کارت شانس"]').count() === 0);
  t('بازدیدکنندهٔ عادی دکمهٔ تنظیم قالب/رنگ ندارد', await p.locator('.ss-btn, .theme-btn').count() === 0);
  const home = await p.locator('body').innerText();
  t('متن «غیرخوراکی» از صفحه حذف شده', !home.includes('غیرخوراکی') && !home.includes('چرا غیر'));
  const link = p.locator('a.f-dayna');
  t('فوتر: توسعه توسط تیم دایناکد + لینک daynacode.ir', (await link.getAttribute('href')) === 'https://daynacode.ir' && (await link.innerText()).includes('دایناکد'));
  t('فوتر: لوگوی دایناکد اول از مسیر محلی /img/ خواسته می‌شود (و در نبود فایل به منبع اصلی برمی‌گردد)', reqs.some(u => u.endsWith('/img/dayna-logo.png')));
  t('هیچ درخواستی به Google Fonts نرفت (فونت روی خود سایت)', !reqs.some(u => /fonts\.(googleapis|gstatic)\.com/.test(u)), reqs.filter(u => /fonts\./.test(u)).join(','));
  const faces = await p.evaluate(async () => { await document.fonts.ready; return [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/["']/g, '')); });
  t('فونت متن (Vazirmatn Variable) واقعاً بارگذاری و استفاده شد', faces.includes('Vazirmatn Variable'), faces.join(','));
  t('فونت تیترها (Lalezar) واقعاً بارگذاری و استفاده شد', faces.includes('Lalezar'), faces.join(','));
  t('فونت body همان فونت بارگذاری‌شده است', (await p.evaluate(() => getComputedStyle(document.body).fontFamily)).startsWith('"Vazirmatn Variable"'));

  // ---------- صفحهٔ ورود ----------
  await p.goto(U + 'auth', { waitUntil: 'networkidle' });
  const tabs = await p.locator('.auth-tabs button').allInnerTexts();
  t('ورود: فقط دو تب «ورود» و «ثبت‌نام» (بدون کد پیامکی)', JSON.stringify(tabs) === JSON.stringify(['ورود', 'ثبت‌نام']), tabs.join('|'));
  const authText = await p.locator('.auth-card').innerText();
  t('ورود: متن‌های اضافه (بک‌اند/سرور/مرورگر) حذف شده', !/بک‌اند|اتصال بک|کد ورود پیامکی|ذخیره می‌شود/.test(authText), authText.slice(0, 120));
  // ثبت‌نام کاربر عادی
  await p.locator('.auth-tabs button', { hasText: 'ثبت‌نام' }).click();
  await p.fill('.auth-form input[type=text]', 'کاربر تست');
  await p.fill('.auth-form input[type=tel]', '0911' + suffix);
  await p.fill('.auth-form input[type=password]', 'pass-1234');
  await p.click('.auth-form button[type=submit]'); await p.waitForURL(/account/, { timeout: 8000 }).catch(() => {});
  t('ثبت‌نام با موبایل و رمز → پنل کاربری', /account/.test(p.url()), p.url());
  await p.goto(U, { waitUntil: 'networkidle' });
  t('کاربر عادی هم دکمهٔ تنظیم قالب/رنگ ندارد', await p.locator('.ss-btn').count() === 0);
  await p.goto(U + 'admin', { waitUntil: 'networkidle' });
  t('کاربر عادی در /admin فرم ورود مدیر می‌بیند (نه پنل)', await p.locator('.admin-login').count() === 1);

  // ---------- سوپریوزر ----------
  const adm = await b.newContext({ viewport: { width: 1280, height: 900 } });
  await adm.addInitScript(() => { try { sessionStorage.setItem('asalat_lucky_seen', '1'); } catch (e) {} });
  const a = await adm.newPage(); a.on('pageerror', e => errs.push(e.message));
  await a.goto(U + 'admin', { waitUntil: 'networkidle' });
  await a.fill('.admin-login input[type=text]', ADMIN_PHONE);
  await a.fill('.admin-login input[type=password]', ADMIN_PASS);
  await a.click('.admin-login button[type=submit]'); await a.waitForTimeout(1200);
  t('ورود مدیر با موبایل+رمز موفق', await a.locator('.admin-tabs').count() === 1);
  const tabsA = await a.locator('.admin-tabs button').allInnerTexts();
  t('پنل ادمین: ۱۱ تب (داشبورد، محصولات، سفارش‌ها، کدها، کارت شانس، ارسال، محتوا، مشاوره، کاربران، پیامک، ظاهر)', ['داشبورد', 'محصولات', 'سفارش‌ها', 'کدهای تخفیف', 'کارت شانس', 'هزینه ارسال', 'محتوای سایت', 'مشاوره‌ها', 'کاربران', 'پنل پیامک', 'ظاهر سایت'].every(x => tabsA.includes(x)), tabsA.join('|'));
  t('پنل ادمین: تب پیش‌فرض داشبورد با نمودار ۷ روزه', await a.locator('.bar-col').count() === 7, await a.locator('.bar-col').count());
  await a.locator('.admin-tabs button', { hasText: 'محصولات' }).click(); await a.waitForTimeout(300);
  t('پنل ادمین: ۲۸ محصول از سرور', await a.locator('.tbl tbody tr').count() >= 28, await a.locator('.tbl tbody tr').count());
  await a.locator('.admin-tabs button', { hasText: 'کاربران' }).click(); await a.waitForTimeout(500);
  t('پنل ادمین: تب کاربران کاربر ثبت‌نام‌شده را نشان می‌دهد', (await a.locator('.tbl').innerText()).includes('0911' + suffix) || (await a.locator('.tbl').innerText()).includes('کاربر تست'));
  await a.locator('.admin-tabs button', { hasText: 'سفارش‌ها' }).click(); await a.waitForTimeout(400);
  t('پنل ادمین: تب سفارش‌ها با فیلتر وضعیت', await a.locator('select.fld option').count() >= 5);
  // پنهان‌کردن محصول و برگشت
  await a.locator('.admin-tabs button', { hasText: 'محصولات' }).click(); await a.waitForTimeout(300);
  const before = (await (await fetch(API + '/products')).json()).length;
  await a.locator('.tbl tbody tr').first().locator('button', { hasText: 'پنهان' }).click(); await a.waitForTimeout(900);
  const hidden = (await (await fetch(API + '/products')).json()).length;
  t('پنهان‌کردن محصول از فروشگاه عمومی', hidden === before - 1, `${before}→${hidden}`);
  t('محصول پنهان در پنل مدیر هنوز دیده می‌شود (با نشان «پنهان»)', await a.locator('.badge-hide').count() === 1);
  await a.locator('.tbl tbody tr').first().locator('button', { hasText: 'نمایش' }).click(); await a.waitForTimeout(900);
  t('نمایش دوبارهٔ محصول', (await (await fetch(API + '/products')).json()).length === before);


  // ---------- مدیریت کاربران از پنل ----------
  await a.locator('.admin-tabs button', { hasText: 'کاربران' }).click(); await a.waitForTimeout(300);
  const row = a.locator('.tbl tbody tr', { hasText: 'کاربر تست' }).first();
  await row.locator('button', { hasText: 'غیرفعال' }).click(); await a.waitForTimeout(800);
  const lr = await fetch(API + '/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: '0911' + suffix, password: 'pass-1234' }) });
  t('غیرفعال‌کردن کاربر از پنل: ورودش رد می‌شود', (await lr.json()).ok === false);
  await a.locator('.tbl tbody tr', { hasText: 'کاربر تست' }).first().locator('button', { hasText: 'فعال' }).click(); await a.waitForTimeout(800);
  const lr2 = await fetch(API + '/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: '0911' + suffix, password: 'pass-1234' }) });
  t('فعال‌سازی دوباره: ورود برقرار می‌شود', (await lr2.json()).ok === true);

  // ---------- کد تخفیف از پنل → استفاده در سبد ----------
  await a.locator('.admin-tabs button', { hasText: 'کدهای تخفیف' }).click(); await a.waitForTimeout(400);
  t('تب کدها: ۷ کد پیش‌فرض نمایش داده می‌شود', await a.locator('.tbl tbody tr').count() >= 7, await a.locator('.tbl tbody tr').count());
  await a.locator('button', { hasText: 'کد تخفیف جدید' }).click();
  await a.fill('.modal input[maxlength="30"]', 'ui' + suffix.slice(0, 4));
  await a.fill('.modal input[type=number]', '25');
  await a.locator('.modal button', { hasText: 'ذخیره کد تخفیف' }).click(); await a.waitForTimeout(900);
  const CODE = ('ui' + suffix.slice(0, 4)).toUpperCase();
  t('ساخت کد تخفیف از پنل: در جدول دیده می‌شود', (await a.locator('.tbl').innerText()).includes(CODE));
  const tokA0 = await a.evaluate(() => JSON.parse(localStorage.getItem('asalat_apiToken')));
  const chk = await (await fetch(API + '/coupons/check?code=' + CODE, { headers: { Authorization: 'Bearer ' + tokA0 } })).json();
  t('کد ساخته‌شده توسط مدیر در سرور معتبر است (۲۵٪)', chk.ok && chk.coupon.val === 25, JSON.stringify(chk));
  const ulog = await (await fetch(API + '/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: '0911' + suffix, password: 'pass-1234' }) })).json();
  const guestCtx = await b.newContext({ viewport: { width: 1280, height: 900 } });
  await guestCtx.addInitScript(() => { try { sessionStorage.setItem('asalat_lucky_seen', '1'); localStorage.setItem('asalat_cart', JSON.stringify([{ pid: 1, w: 500, qty: 1 }])); } catch (e) {} });
  const gp = await guestCtx.newPage(); await gp.goto(U + 'cart', { waitUntil: 'networkidle' });
  t('مهمان در سبد کادر کد تخفیف ندارد و پیام «ابتدا وارد شوید» می‌بیند', await gp.locator('#main .coupon-row').count() === 0 && (await gp.locator('#main .coupon-login').innerText()).includes('وارد حساب'));
  const sp = await b.newContext({ viewport: { width: 1280, height: 900 } }); await sp.addInitScript(([tk, us]) => { try { sessionStorage.setItem('asalat_lucky_seen', '1'); localStorage.setItem('asalat_cart', JSON.stringify([{ pid: 1, w: 500, qty: 1 }])); localStorage.setItem('asalat_apiToken', JSON.stringify(tk)); localStorage.setItem('asalat_user', JSON.stringify(us)); } catch (e) {} }, [ulog.token, ulog.user]);
  const cp = await sp.newPage(); await cp.goto(U + 'cart', { waitUntil: 'networkidle' }); await cp.waitForTimeout(500);
  await cp.fill('#main .coupon-row input', CODE); await cp.click('#main .coupon-row button'); await cp.waitForTimeout(900);
  const offTxt = await cp.locator('#main .t-row').nth(1).innerText();
  t('کد مدیر در سبد مشتری اعمال می‌شود (تخفیف ≠ صفر)', !/^تخفیف کدها\s*۰ تومان/.test(offTxt.replace(/\n/g, ' ').trim()) && /−/.test(offTxt), offTxt);
  await cp.fill('#main .coupon-row input', 'NOPE12345'); await cp.click('#main .coupon-row button'); await cp.waitForTimeout(600);
  t('کد نامعتبر در سبد رد می‌شود', (await cp.locator('.toasts, [class*=toast]').allInnerTexts()).join(' ').includes('نامعتبر'));
  await a.locator('.tbl tbody tr', { hasText: CODE }).locator('button', { hasText: 'حذف' }).click().catch(() => {});

  // ---------- تخفیف گروهی ----------
  await a.locator('.admin-tabs button', { hasText: 'محصولات' }).click(); await a.waitForTimeout(300);
  await a.locator('button', { hasText: 'تخفیف گروهی' }).first().click();
  await a.selectOption('.modal select', { label: 'دمنوش و محصولات طبیعی' });
  await a.fill('.modal input[type=number]', '15');
  await a.locator('.modal button', { hasText: 'اعمال تخفیف' }).click(); await a.waitForTimeout(2500);
  const teas = (await (await fetch(API + '/products')).json()).filter(p => p.cat === 'tea');
  t('تخفیف گروهی: همهٔ محصولات دستهٔ دمنوش ۱۵٪ شدند', teas.length > 0 && teas.every(p => p.disc === 15), teas.map(p => p.disc).join(','));

  // دکمهٔ قالب/رنگ فقط برای مدیر
  await a.goto(U, { waitUntil: 'networkidle' });
  t('سوپریوزر دکمهٔ 🎨 تنظیم قالب و رنگ را می‌بیند', await a.locator('.ss-btn').count() === 1);
  await a.locator('.ss-btn').click();
  await a.locator('.ss-dot[title="اناری"]').click();
  t('پیش‌نمایش تم برای مدیر اعمال شد', await a.evaluate(() => document.documentElement.dataset.theme) === 'anari');
  t('تا ذخیره نشده، بازدیدکنندهٔ دیگر تغییر را نمی‌بیند', (await (await fetch(API + '/settings')).json()).theme === 'default');
  await a.locator('.ss-save').click(); await a.waitForTimeout(900);
  t('ذخیره برای کل سایت: سرور تم را نگه می‌دارد', (await (await fetch(API + '/settings')).json()).theme === 'anari');
  const v = await b.newContext(); const vp = await v.newPage();
  await vp.goto(U, { waitUntil: 'networkidle' }); await vp.waitForTimeout(500);
  t('بازدیدکنندهٔ تازه همان تم اناری را می‌بیند (اعمال در کل سایت)', await vp.evaluate(() => document.documentElement.dataset.theme) === 'anari');
  t('بازدیدکنندهٔ تازه دکمهٔ تنظیم ندارد', await vp.locator('.ss-btn').count() === 0);
  // رنگ برند دستی
  await a.locator('.ss-btn').click();
  await a.locator('.ss-row button', { hasText: 'روشن‌تر' }).click();
  await a.locator('.ss-save').click(); await a.waitForTimeout(900);
  const look = await (await fetch(API + '/settings')).json();
  t('رنگ برند دستی ذخیره و در سرور نگه‌داری می‌شود', Array.isArray(look.tune) && look.tune.length === 4, JSON.stringify(look));
  await vp.reload({ waitUntil: 'networkidle' }); await vp.waitForTimeout(400);
  t('رنگ ذخیره‌شده روی --brand بازدیدکننده اعمال شد', await vp.evaluate(() => document.documentElement.style.getPropertyValue('--brand')) === look.tune[0]);
  // بازگشت به پیش‌فرض (پاک‌سازی)
  const tok = await a.evaluate(() => JSON.parse(localStorage.getItem('asalat_apiToken')));
  await fetch(API + '/admin/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tok }, body: JSON.stringify({ theme: 'default', tune: null }) });
  // دست‌کاری LocalStorage نباید مدیر بسازد
  const hack = await b.newContext(); await hack.addInitScript(() => { localStorage.setItem('asalat_admin', 'true'); });
  const hp = await hack.newPage(); await hp.goto(U + 'admin', { waitUntil: 'networkidle' });
  t('جعل پرچم admin در LocalStorage پنل را باز نمی‌کند', await hp.locator('.admin-login').count() === 1);

  // ---------- تاریخ شمسی ----------
  await a.goto(U + 'admin', { waitUntil: 'networkidle' }); await a.waitForTimeout(900);
  await a.locator('.admin-tabs button', { hasText: 'سفارش‌ها' }).click(); await a.waitForTimeout(600);
  const od = await a.locator('.tbl tbody tr').first().locator('td').nth(1).innerText().catch(() => '');
  t('پنل مدیر: تاریخ سفارش شمسی (۱۴۰۵/…)', /^۱۴۰[۵-۹]\//.test(od.trim()) || od === '', od);
  await a.locator('.admin-tabs button', { hasText: 'کدهای تخفیف' }).click(); await a.waitForTimeout(400);
  await a.locator('button', { hasText: 'کد تخفیف جدید' }).click();
  await a.fill('.modal input[maxlength="30"]', 'JL' + suffix.slice(0, 4));
  await a.fill('.modal input[inputmode=numeric]', 'نه-تاریخ');
  await a.locator('.modal button', { hasText: 'ذخیره کد تخفیف' }).click(); await a.waitForTimeout(500);
  t('انقضای کد: تاریخ غیرشمسی/نامعتبر رد می‌شود', await a.locator('.modal input[maxlength="30"]').count() === 1);
  await a.fill('.modal input[inputmode=numeric]', '۱۴۰۵/۱۲/۳۰');
  await a.locator('.modal button', { hasText: 'ذخیره کد تخفیف' }).click(); await a.waitForTimeout(500);
  t('انقضای کد: ۱۴۰۵/۱۲/۳۰ (سال کبیسه نیست) رد می‌شود', await a.locator('.modal input[maxlength="30"]').count() === 1);
  await a.fill('.modal input[inputmode=numeric]', '۱۴۰۵/۱۲/۲۹');
  await a.locator('.modal button', { hasText: 'ذخیره کد تخفیف' }).click(); await a.waitForTimeout(900);
  t('انقضای شمسی ۱۴۰۵/۱۲/۲۹ ذخیره و در جدول شمسی نمایش داده می‌شود', (await a.locator('.tbl').innerText()).includes('۱۴۰۵/۱۲/۲۹'));

  // ---------- تسویه: شمارهٔ موبایل → ثبت‌نام (حساب جدید) ----------
  const NEWP = '0917' + suffix;
  const mkCtx = async (extra = {}) => { const c = await b.newContext({ viewport: { width: 1280, height: 900 } });
    await c.addInitScript(([x]) => { try { if (!x.noLuckySeen) sessionStorage.setItem('asalat_lucky_seen', '1'); if (x.cart) localStorage.setItem('asalat_cart', JSON.stringify([{ pid: 1, w: 500, qty: 1 }])); } catch (e) {} }, [extra]); return c; };
  const co = await mkCtx({ cart: true }); const cop = await co.newPage(); cop.on('pageerror', e => errs.push(e.message));
  await cop.goto(U + 'checkout', { waitUntil: 'networkidle' });
  t('تسویهٔ مهمان: اول مرحلهٔ «ورود / ثبت‌نام» با شمارهٔ موبایل', (await cop.locator('.co-step.on').innerText()).includes('ورود'), await cop.locator('.co-step.on').innerText());
  await cop.fill('.auth-form input[type=tel]', NEWP); await cop.click('.auth-form button[type=submit]'); await cop.waitForTimeout(900);
  t('شمارهٔ جدید: فرم ساخت حساب (نام + رمز) نمایش داده می‌شود', (await cop.locator('.id-note').innerText()).includes('پیدا نشد') && await cop.locator('input[autocomplete=name]').count() === 1);
  await cop.fill('input[autocomplete=name]', 'خریدار جدید'); await cop.fill('.auth-form input[type=password]', 'checkout-1');
  await cop.click('.auth-form button[type=submit]'); await cop.waitForTimeout(1200);
  t('ساخت حساب حین خرید → ادامه به اطلاعات ارسال', (await cop.locator('.co-step.on').innerText()).includes('اطلاعات ارسال'));
  t('روش‌های ارسال از سرور (≥۲ روش)', await cop.locator('.ship-opt').count() >= 2, await cop.locator('.ship-opt').count());
  await cop.fill('input[placeholder="مثلاً تهران"]', 'تهران'); await cop.fill('textarea[placeholder^="خیابان"]', 'خیابان آزمایشی، پلاک ۱، واحد ۲');
  await cop.locator('button', { hasText: 'ادامه و مشاهده فاکتور' }).click(); await cop.waitForTimeout(500);
  t('فاکتور: کادر کد تخفیف (بعد از ورود) وجود دارد', await cop.locator('#main .coupon-row').count() === 1);
  await cop.locator('button', { hasText: 'ثبت نهایی سفارش' }).click(); await cop.waitForTimeout(1800);
  const ordCode = (await cop.locator('.ord-code').innerText().catch(() => '')).trim();
  t('ثبت سفارش با حساب تازه‌ساخته: کد KG- نمایش داده می‌شود', /^KG-\d+/.test(ordCode), ordCode);
  const nl = await (await fetch(API + '/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: NEWP, password: 'checkout-1' }) })).json();
  const mine = await (await fetch(API + '/orders/mine', { headers: { Authorization: 'Bearer ' + nl.token } })).json();
  t('سفارش روی حساب همین شماره در سرور ثبت شده است', (mine.results || []).some(o => o.code === ordCode), JSON.stringify(mine).slice(0, 120));

  // ---------- تسویه: شمارهٔ موجود → رمز → ادامه ----------
  const co2 = await mkCtx({ cart: true }); const c2 = await co2.newPage(); c2.on('pageerror', e => errs.push(e.message));
  await c2.goto(U + 'checkout', { waitUntil: 'networkidle' });
  await c2.fill('.auth-form input[type=tel]', NEWP); await c2.click('.auth-form button[type=submit]'); await c2.waitForTimeout(900);
  t('شمارهٔ موجود: فقط رمز عبور پرسیده می‌شود (بدون فیلد نام)', (await c2.locator('.id-note').innerText()).includes('حسابی با این شماره دارید') && await c2.locator('input[autocomplete=name]').count() === 0);
  await c2.fill('.auth-form input[type=password]', 'wrong-pass'); await c2.click('.auth-form button[type=submit]'); await c2.waitForTimeout(900);
  t('رمز غلط: وارد نمی‌شود', (await c2.locator('.co-step.on').innerText()).includes('ورود'));
  await c2.fill('.auth-form input[type=password]', 'checkout-1'); await c2.click('.auth-form button[type=submit]'); await c2.waitForTimeout(1200);
  t('رمز درست: ادامهٔ ثبت سفارش (مرحلهٔ ارسال)', (await c2.locator('.co-step.on').innerText()).includes('اطلاعات ارسال'));

  // ---------- کارت شانس حساب‌محور ----------
  const gl = await mkCtx({ noLuckySeen: true }); const glp = await gl.newPage();
  await glp.goto(U, { waitUntil: 'networkidle' }); await glp.waitForTimeout(2300);
  t('کارت شانس برای مهمان خودکار باز نمی‌شود', await glp.locator('.overlay.open[aria-label="کارت شانس"]').count() === 0);
  await glp.locator('.fab.gold').click(); await glp.waitForTimeout(500);
  t('مهمان: کارت قفل است و دکمهٔ ورود/ثبت‌نام دارد', await glp.locator('.lc-inner.locked').count() === 1 && await glp.locator('.lucky-foot button', { hasText: 'ورود / ثبت‌نام' }).count() === 1);
  const lreg = await (await fetch(API + '/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'شانس ازما', phone: '0918' + suffix, password: 'lucky-1234' }) })).json();
  const lc = await b.newContext({ viewport: { width: 1280, height: 900 } });
  await lc.addInitScript(([tk, us]) => { try { localStorage.setItem('asalat_apiToken', JSON.stringify(tk)); localStorage.setItem('asalat_user', JSON.stringify(us)); } catch (e) {} }, [lreg.token, lreg.user]);
  const lp = await lc.newPage(); lp.on('pageerror', e => errs.push(e.message));
  await lp.goto(U, { waitUntil: 'networkidle' }); await lp.waitForTimeout(2600);
  t('کاربر واردشده: کارت شانس خودکار باز می‌شود', await lp.locator('.overlay.open[aria-label="کارت شانس"]').count() === 1);
  await lp.locator('.lc-inner').click(); await lp.waitForTimeout(1500);
  const lcode = (await lp.locator('.lc-code').innerText().catch(() => '')).trim();
  t('چرخش کارت: کد شخصی LK- از سرور', /^LK-[A-Z0-9]{8}$/.test(lcode), lcode);
  await lp.locator('.lucky-x').click(); await lp.waitForTimeout(300);
  await lp.locator('.fab.gold').click(); await lp.waitForTimeout(600);
  t('چرخش دوباره پشت‌سرهم: کارت قفل و زمان بعدی شمسی نمایش داده می‌شود', await lp.locator('.lc-inner.locked').count() === 1 && /۱۴۰[۵-۹]\//.test(await lp.locator('.lucky-head').innerText()), await lp.locator('.lucky-head').innerText());
  const spin2 = await (await fetch(API + '/lucky/spin', { method: 'POST', headers: { Authorization: 'Bearer ' + lreg.token } })).json();
  t('سرور هم چرخش دوم را رد می‌کند', spin2.ok === false);
  await lp.goto(U + 'account?tab=codes', { waitUntil: 'networkidle' }); await lp.waitForTimeout(800);
  t('پنل کاربری ← کدهای من: کد جایزه ثبت است', (await lp.locator('.up-frame').innerText()).includes(lcode));

  // ---------- صفحات راهنما ----------
  const pg = await mkCtx(); const pgp = await pg.newPage(); pgp.on('pageerror', e => errs.push(e.message));
  await pgp.goto(U + 'page/faq', { waitUntil: 'networkidle' });
  t('صفحهٔ سوالات متداول: ≥۸ سوال و جواب', await pgp.locator('.faq-item').count() >= 8, await pgp.locator('.faq-item').count());
  await pgp.locator('.faq-item summary').first().click();
  t('سوال باز می‌شود و پاسخ دیده می‌شود', await pgp.locator('.faq-item[open] p').count() === 1);
  await pgp.goto(U + 'page/how-to-order', { waitUntil: 'networkidle' });
  t('صفحهٔ نحوه ثبت سفارش: متن ساخت‌یافته (عنوان و مراحل)', await pgp.locator('.rich h2').count() >= 1 && await pgp.locator('.rich ol li').count() >= 5);
  await pgp.goto(U + 'page/shipping-info', { waitUntil: 'networkidle' });
  t('صفحهٔ ارسال: جدول زندهٔ هزینه‌ها از سرور', await pgp.locator('.ship-table tbody tr').count() >= 2);
  await pgp.goto(U + 'page/contact', { waitUntil: 'networkidle' });
  t('صفحهٔ تماس: کارت‌های اطلاعات تماس', await pgp.locator('.c-card').count() >= 3);
  await pgp.goto(U + 'page/nope-zzz', { waitUntil: 'networkidle' });
  t('صفحهٔ ناموجود: پیام «پیدا نشد»', (await pgp.locator('#main .up-empty').innerText()).includes('پیدا نشد'));
  await pgp.goto(U, { waitUntil: 'networkidle' }); await pgp.waitForTimeout(500);
  const foot = await pgp.locator('footer').innerText();
  t('فوتر: لینک‌های راهنمای خرید پیاده‌سازی شده (نحوه ثبت سفارش، سوالات متداول، مرجوعی، ارسال)', ['نحوه ثبت سفارش', 'سوالات متداول', 'شرایط مرجوعی کالا', 'شیوه‌های ارسال و هزینه‌ها'].every(x => foot.includes(x)));
  t('فوتر: لینک‌های درباره ما، حریم خصوصی و قوانین', ['حریم خصوصی', 'قوانین و مقررات'].every(x => foot.includes(x)));
  await pgp.locator('footer a', { hasText: 'سوالات متداول' }).click(); await pgp.waitForURL(/page\/faq/, { timeout: 5000 }).catch(() => {});
  t('لینک فوتر به صفحه می‌رود (نه فقط پیام)', /page\/faq/.test(pgp.url()), pgp.url());

  // ---------- مدیر: ارسال، محتوا، مشاوره ----------
  await a.locator('.admin-tabs button', { hasText: 'هزینه ارسال' }).click(); await a.waitForTimeout(700);
  await a.locator('.tbl tbody tr').first().locator('button', { hasText: 'ویرایش' }).click();
  await a.locator('.modal input[type=number]').first().fill('77000');
  await a.locator('.modal button', { hasText: /^ذخیره$/ }).last().click(); await a.waitForTimeout(1000);
  const site1 = await (await fetch(API + '/site')).json();
  t('مدیر: هزینهٔ اولین روش ارسال از پنل تغییر کرد (۷۷٬۰۰۰)', site1.shipping.methods[0].cost === 77000, JSON.stringify(site1.shipping.methods[0]));
  const sc = await b.newContext({ viewport: { width: 1280, height: 900 } });
  await sc.addInitScript(([tk, us]) => { try { sessionStorage.setItem('asalat_lucky_seen', '1'); localStorage.setItem('asalat_cart', JSON.stringify([{ pid: 1, w: 500, qty: 1 }])); localStorage.setItem('asalat_apiToken', JSON.stringify(tk)); localStorage.setItem('asalat_user', JSON.stringify(us)); } catch (e) {} }, [ulog.token, ulog.user]);
  const scp = await sc.newPage(); await scp.goto(U + 'checkout', { waitUntil: 'networkidle' }); await scp.waitForTimeout(700);
  t('مشتری: هزینهٔ جدید ارسال در تسویه دیده می‌شود (۷۷٬۰۰۰)', (await scp.locator('.ship-opts').innerText()).includes('۷۷٬۰۰۰'), (await scp.locator('.ship-opts').innerText()).slice(0, 80));
  const tokA = await a.evaluate(() => JSON.parse(localStorage.getItem('asalat_apiToken')));
  await fetch(API + '/admin/shipping', { headers: { Authorization: 'Bearer ' + tokA } }).then(r => r.json()).then(async r => { const m = r.methods[0]; await fetch(API + '/admin/shipping/' + m.id, { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tokA }, body: JSON.stringify({ cost: 89000 }) }); });
  await a.locator('.admin-tabs button', { hasText: 'محتوای سایت' }).click(); await a.waitForTimeout(700);
  await a.locator('.fld:has-text("تلفن (نمایشی") input').fill('۰۲۱-۵۵۵۵۵۵۵۵');
  await a.locator('button', { hasText: 'ذخیرهٔ اطلاعات و متن‌ها' }).click(); await a.waitForTimeout(900);
  const pv = await mkCtx(); const pvp = await pv.newPage(); await pvp.goto(U, { waitUntil: 'networkidle' }); await pvp.waitForTimeout(500);
  t('مدیر: تلفن تغییر کرد → بالای سایت و فوتر برای همه عوض شد', (await pvp.locator('.topbar').innerText()).includes('۵۵۵۵۵۵۵۵') && (await pvp.locator('footer').innerText()).includes('۵۵۵۵۵۵۵۵'));
  await a.locator('.fld:has-text("تلفن (نمایشی") input').fill('۰۲۱-۹۱۰۹۲۰۰۰');
  await a.locator('button', { hasText: 'ذخیرهٔ اطلاعات و متن‌ها' }).click(); await a.waitForTimeout(700);
  await a.locator('.subtabs button', { hasText: 'صفحات راهنما' }).click(); await a.waitForTimeout(500);
  await a.locator('button', { hasText: 'صفحهٔ جدید' }).click();
  const NPG = 'ui' + suffix.slice(0, 4);
  await a.locator('.fld:has-text("عنوان صفحه") input').fill('صفحهٔ تازهٔ مدیر');
  await a.locator('.fld:has-text("نشانی (انگلیسی)") input').fill(NPG);
  await a.locator('.fld:has-text("متن صفحه") textarea').fill('## تیتر تست\n\n- مورد یک\n- مورد دو\n\n<script>alert(1)</script>');
  await a.locator('button', { hasText: 'ذخیرهٔ صفحه' }).click(); await a.waitForTimeout(1000);
  await pgp.goto(U + 'page/' + NPG, { waitUntil: 'networkidle' });
  t('مدیر: صفحهٔ جدید ساخت و برای همه نمایش داده می‌شود', (await pgp.locator('.page-title').innerText()) === 'صفحهٔ تازهٔ مدیر' && await pgp.locator('.rich ul li').count() === 2);
  t('امنیت: HTML/اسکریپت داخل متن صفحه اجرا نمی‌شود (escape)', await pgp.locator('.rich script').count() === 0 && (await pgp.locator('.rich').innerText()).includes('<script>'));
  await pgp.goto(U, { waitUntil: 'networkidle' }); await pgp.waitForTimeout(500);
  await pgp.locator('.cons-form input[type=text]').fill('مشتری مشاوره'); await pgp.locator('.cons-form input[type=tel]').fill('09141234567');
  await pgp.locator('.cons-form button[type=submit]').click(); await pgp.waitForTimeout(900);
  await a.locator('.admin-tabs button', { hasText: 'مشاوره‌ها' }).click(); await a.waitForTimeout(800);
  t('فرم مشاورهٔ صفحهٔ اصلی واقعاً ذخیره می‌شود و مدیر می‌بیند', (await a.locator('.tbl').innerText()).includes('مشتری مشاوره'));
  await a.locator('.admin-tabs button', { hasText: 'کارت شانس' }).click(); await a.waitForTimeout(800);
  t('مدیر: تب کارت شانس (جایزه‌ها + برنده‌ها)', await a.locator('.tbl').count() >= 2 && (await a.locator('.admin-card').first().innerText()).includes('جایزه'));

  // ---------- ورود مدیر از صفحهٔ ورود عادی ----------
  const sa = await b.newContext({ viewport: { width: 1280, height: 900 } }); await sa.addInitScript(() => { try { sessionStorage.setItem('asalat_lucky_seen', '1'); } catch (e) {} });
  const sp2 = await sa.newPage(); await sp2.goto(U + 'auth', { waitUntil: 'networkidle' });
  await sp2.fill('.auth-form input[type=tel]', ADMIN_PHONE); await sp2.fill('.auth-form input[type=password]', ADMIN_PASS);
  await sp2.click('.auth-form button[type=submit]'); await sp2.waitForURL(/admin/, { timeout: 8000 }).catch(() => {});
  t('مدیر با ورود عادی مستقیم به پنل مدیریت می‌رود (نه پنل کاربری)', /\/admin/.test(sp2.url()), sp2.url());
  await sp2.waitForTimeout(800);
  t('پنل مدیریت برای او باز است', await sp2.locator('.admin-tabs').count() === 1);
  t('دکمهٔ هدر برای مدیر «پنل مدیریت» است', (await sp2.locator('.login-btn').innerText()).includes('پنل مدیریت'));
  t('فوتر: سال شمسی ۱۴۰۵', (await sp2.locator('.f-bottom').innerText()).includes('۱۴۰۵'), (await sp2.locator('.f-bottom').innerText()).slice(0, 40));

  // ---------- موبایل ----------
  const mob = await b.newContext({ viewport: { width: 375, height: 700 } });
  await mob.addInitScript(() => { try { sessionStorage.setItem('asalat_lucky_seen', '1'); } catch (e) {} });
  const m = await mob.newPage(); m.on('pageerror', e => errs.push(e.message));
  await m.goto(U, { waitUntil: 'networkidle' });
  await m.locator('[aria-label="باز کردن منو"], .menu-btn, [aria-label*="منو"]').first().click().catch(() => {});
  await m.waitForTimeout(400);
  const chevClosed = await m.locator('.acc > button .chev').first().evaluate(e => getComputedStyle(e).transform);
  await m.locator('.acc > button').first().click(); await m.waitForTimeout(900);   // پایان انیمیشن چرخش
  const chevOpen = await m.locator('.acc.open > button .chev').first().evaluate(e => getComputedStyle(e).transform);
  const ang = tr => { const mm = tr.match(/matrix\(([^)]+)\)/); if (!mm) return null; const [a1, b1] = mm[1].split(',').map(Number); return Math.round(Math.atan2(b1, a1) * 180 / Math.PI); };
  t('منوی موبایل: فلش بسته رو به چپ است (۱۸۰°)', Math.abs(ang(chevClosed)) === 180, chevClosed);
  t('منوی موبایل: فلش باز رو به پایین است (۹۰°)', ang(chevOpen) === 90, chevOpen);
  await m.locator('.drawer-head button').click(); await m.waitForTimeout(300);
  await m.evaluate(() => localStorage.setItem('asalat_cart', JSON.stringify([{ pid: 1, w: 500, qty: 1 }])));
  await m.reload({ waitUntil: 'networkidle' }); await m.waitForTimeout(500);
  t('نوار سبد موبایل نمایش داده می‌شود', await m.locator('.m-cart-bar.show').count() === 1);
  const pad = await m.evaluate(() => parseFloat(getComputedStyle(document.body).paddingBottom));
  t('فضای انتهای صفحه برای نوار سبد رزرو شده (فوتر دیده می‌شود)', pad >= 80, pad);
  await m.evaluate(() => window.scrollTo(0, document.body.scrollHeight)); await m.waitForTimeout(500);
  const last = await m.evaluate(() => { const f = document.querySelector('.f-bottom').getBoundingClientRect(); const bar = document.querySelector('.m-cart-bar').getBoundingClientRect(); return { fb: f.bottom, barTop: bar.top }; });
  t('پایین فوتر زیر نوار سبد نمی‌ماند', last.fb <= last.barTop + 1, JSON.stringify(last));
  const fabIcon = m.locator('.fab[aria-label="بازگشت به بالا"] svg');
  t('دکمهٔ بازگشت به بالا: فلش رو به بالا (−۹۰°)', (await fabIcon.getAttribute('style')).includes('rotate(-90deg)'));

  t('هیچ خطای JS', errs.length === 0, [...new Set(errs)].join(' ; '));
  console.log(`\nنتیجه: ${bad ? bad + ' ناموفق' : 'همه موفق'}`);
  await b.close(); process.exit(bad ? 1 : 0);
})();
