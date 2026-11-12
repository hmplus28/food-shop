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
  t('کارت شانس باز می‌شود', await p.locator('.overlay.open[aria-label="کارت شانس"]').count() === 1);
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
  t('پنل ادمین: تب‌های داشبورد/محصولات/سفارش‌ها/کدهای تخفیف/کاربران/پیامک/ظاهر سایت', ['داشبورد', 'محصولات', 'سفارش‌ها', 'کدهای تخفیف', 'کاربران', 'پنل پیامک', 'ظاهر سایت'].every(x => tabsA.includes(x)), tabsA.join('|'));
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
  const chk = await (await fetch(API + '/coupons/check?code=' + CODE)).json();
  t('کد ساخته‌شده توسط مدیر در سرور معتبر است (۲۵٪)', chk.ok && chk.coupon.val === 25, JSON.stringify(chk));
  const sp = await b.newContext({ viewport: { width: 1280, height: 900 } }); await sp.addInitScript(() => { try { sessionStorage.setItem('asalat_lucky_seen', '1'); localStorage.setItem('asalat_cart', JSON.stringify([{ pid: 1, w: 500, qty: 1 }])); } catch (e) {} });
  const cp = await sp.newPage(); await cp.goto(U + 'cart', { waitUntil: 'networkidle' });
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
