# CLAUDE.md — فروشگاه خانم گل (food-shop)

فروشگاه اینترنتی خشکبار، فارسی و راست‌چین. فرانت **Vue 3 + Vite** (SPA)، بک‌اند **Django 5 + DRF + JWT**.

## ساختار
- `app/` — سورس فرانت (Vue 3, Pinia-less stores ساده، vue-router). مسیر پایه `/food-shop/`.
- `index.html`, `assets/`, `404.html`, `sitemap.xml` در ریشه — **خروجی بیلد** برای GitHub Pages (دستی ویرایش نشود).
- `backend/` — Django: `config/` (settings, urls)، `shop/` (models, views, serializers, pricing, sms, seed).
- `scripts/` — تست‌های E2E و امنیتی بک‌اند (`test_backend_api.py` ۶۰ بررسی، `test_backend_security.py` ۶۹ بررسی) و اسکریپت‌های کمکی.
- `deploy/`, `backend/deploy/` — استقرار cPanel (راهنما: `deploy/GUIDE-CPANEL-FA.md`).

## دستورها
```bash
# فرانت
cd app && npm ci && npm run dev        # http://localhost:5173/food-shop/
cd app && npm run build                # خروجی در app/dist ← محتوا را در ریشهٔ ریپو کپی کنید

# بک‌اند
cd backend && pip install -r requirements.txt
cp .env.example .env                   # سپس مقادیر را پر کنید
python manage.py migrate && python manage.py seed_shop
python manage.py runserver 8787

# تست (سرور باید روشن باشد)
python3 scripts/test_backend_api.py        # باید 67/67 سبز باشد (شامل فید ترب)
python3 scripts/test_backend_security.py   # باید 69/69 سبز باشد
node scripts/test_cart_ui.js                # سبد خرید (۲۷ بررسی؛ نیاز به vite preview روی 4173)
node scripts/test_seo.js                    # سئو/پیش‌رندر (نیاز به vite preview روی 4173)
python3 scripts/test_ascii_locale.py         # رگرسیون ۵۰۰ هاست (locale ASCII + .env فارسی)
python3 backend/deploy/diagnose.py         # عیب‌یابی خطای ۵۰۰ روی هاست
```

## استقرار روی هاست (cPanel)
- هاست Node ندارد. فرانت با `bash scripts/build_host.sh` (ماشین محلی) در `host-dist/` ساخته و commit می‌شود (جانشین دامنه: `__SITE_HOST__`؛ فرانت روی `/`، API روی `/food-shop/api/v1`).
- روی هاست: `git pull && bash deploy.sh --domain دامنه` (فرانت + بک‌اند + بررسی نهایی + عیب‌یابی خودکار). `--check` فقط عیب‌یابی.
- بعد از هر تغییر در `app/`، هم `host-dist/` و هم (برای GitHub Pages) خروجی ریشه را دوباره بسازید.

## سئو و ترب
- `npm run build` = `vite build` + `app/scripts/prerender.mjs` (صفحات ایستای سئو، sitemap.xml، robots.txt). روی دامنهٔ واقعی: `VITE_BASE=/ VITE_SITE_URL=https://دامنه npm run build`.
- داده‌های سئوی محصول فقط در `app/src/data/seoProduct.js` ساخته می‌شود (هم صفحهٔ محصول هم پیش‌رندر). JSON-LD امتیاز/نظر ساختگی نداشته باشد.
- فید ترب: `GET|POST /api/v1/torob/products?page=N` (`backend/shop/views.py: TorobProductsView`)؛ قیمت باید با قیمت وزن پیش‌فرض صفحهٔ محصول یکی بماند.
- لاگ ۵۰۰: `backend/logs/django-error.log`؛ راهنما: بخش «خطای ۵۰۰» در `deploy/GUIDE-CPANEL-FA.md`.

## قواعد مهم
- **قیمت، تخفیف، ارسال و جمع سفارش همیشه سمت سرور محاسبه می‌شود** (`shop/pricing.py`)؛ مقدار مالی کلاینت هرگز اعتماد نمی‌شود.
- ورود با رمز یا OTP پیامکی؛ سقف ارسال/تلاش OTP با env (`OTP_*`) تنظیم می‌شود. `SMS_PROVIDER=console` در توسعه.
- ارقام فارسی/عربی در شماره موبایل نرمال می‌شوند (`normalize_phone`).
- `backend/.env` و `db.sqlite3` را هرگز کامیت نکنید (در `.gitignore`).
- در تولید: `ADMIN_PASSWORD` پیش‌فرض عوض شود، `CORS_ORIGINS` به دامنهٔ فرانت محدود شود، پس از SSL گزینه‌های `SECURE_*` روشن شوند.
- متن‌ها و کامیت‌ها فارسی هستند؛ UI باید RTL و ریسپانسیو (۳۲۰ تا ۱۴۴۰px بدون سرریز افقی) بماند.

## وضعیت بررسی
بیلد فرانت بازتولیدپذیر؛ `manage.py check` و `makemigrations --check` تمیز؛ ریسپانسیو در عرض‌های ۳۲۰/۳۷۵/۷۶۸/۱۰۲۴/۱۴۴۰ روی تمام مسیرها بدون سرریز و خطا.
