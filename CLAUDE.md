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
python3 scripts/test_backend_api.py        # باید 173/173 سبز باشد (ارسال، محتوا، کارت شانس، مشاوره، کدها، کاربران)
python3 scripts/test_backend_security.py   # باید 71/71 سبز باشد
node scripts/test_cart_ui.js                # سبد خرید (۲۷ بررسی؛ نیاز به vite preview روی 4173)
node scripts/test_seo.js                    # سئو/پیش‌رندر (نیاز به vite preview روی 4173)
python3 scripts/test_ascii_locale.py         # رگرسیون ۵۰۰ هاست (locale ASCII + .env فارسی)
python3 backend/deploy/diagnose.py         # عیب‌یابی خطای ۵۰۰ روی هاست
```

## استقرار روی هاست (cPanel)
- هاست Node ندارد. فرانت با `bash scripts/build_host.sh` (ماشین محلی) در `host-dist/` ساخته و commit می‌شود (جانشین‌ها: `__SITE_HOST__` و `__API_BASE__`؛ فرانت روی `/`؛ API معمولاً روی ساب‌دامین `api.دامنه` که deploy.sh از Setup Python App تشخیص می‌دهد).
- روی هاست: `git pull && bash deploy.sh --domain دامنه` (فرانت + بک‌اند + بررسی نهایی + عیب‌یابی خودکار). `--check` فقط عیب‌یابی.
- بعد از هر تغییر در `app/`، هم `host-dist/` و هم (برای GitHub Pages) خروجی ریشه را دوباره بسازید.

## احراز هویت، مدیر و ظاهر سایت
- ثبت‌نام و ورود فقط با موبایل + رمز؛ ورود با کد پیامکی (OTP) کاملاً حذف شده است (پنل پیامک فقط برای اطلاع‌رسانی سفارش).
- مدیر = کاربر با `role=admin` (ساخت: `manage.py createsuperuser` یا `ADMIN_*` در `.env`). نقش فقط از سرور می‌آید (`/auth/me`)؛ پرچم‌های LocalStorage اعتبار ندارند.
- تم و رنگ برند سراسری است: `GET /settings` (عمومی) و `PUT /admin/settings` (فقط مدیر)؛ UI آن `components/SiteStudio.vue` فقط برای مدیر (و تب «ظاهر سایت» در پنل). بازدیدکننده تم شخصی ندارد.
- پنل مدیر کاملاً سرور-محور است (`views/AdminView.vue`): داشبورد (نمودار ۷ روزه، پرفروش‌ها، کم‌موجودی)، محصولات (پنهان/حذف/ویرایش + تخفیف گروهی)، سفارش‌ها (فیلتر، جزئیات، وضعیت، CSV)، کدهای تخفیف، کاربران (فعال/غیرفعال، نقش، رمز موقت)، پیامک، ظاهر سایت.
- کدهای تخفیف در جدول `Coupon` (مرجع محاسبهٔ سفارش؛ `pricing.coupon_effect`) با سقف استفاده/انقضا/حداقل خرید؛ فرانت با `GET /coupons/check` قاعده را می‌گیرد. ۷ کد پیش‌فرض با migration `0003` ساخته می‌شود.
- مدیر بعد از ورود عادی مستقیم به `/admin` می‌رود؛ سال فوتر شمسی و پویاست.
- آفلاین: فونت‌ها با `@fontsource` داخل بیلد؛ تصاویر در `app/public/img/` (دانلود با `scripts/fetch_assets.py`) با fallback خودکار به منبع اصلی تا زمان دانلود.
- تست‌ها: `scripts/test_ui_admin.js` (نیاز به بک‌اند 8787 و بیلد API-روشن روی 4174، راهنما در سرفایل).

## محتوا، ارسال، کارت شانس و ثبت سفارش (قوانین)
- **ثبت سفارش فقط با حساب**: `POST /orders` احراز هویت می‌خواهد. در تسویه: شمارهٔ موبایل → `POST /auth/phone-check` → اگر حساب هست رمز می‌گیریم و وارد می‌کنیم، وگرنه نام+رمز می‌گیریم و حساب می‌سازیم → ادامهٔ ثبت سفارش. «اولین خرید» و مالکیت کد جایزه روی **حساب** حساب می‌شود، نه شمارهٔ گیرنده.
- **کد تخفیف فقط بعد از ورود**: `GET /coupons/check` احراز هویت می‌خواهد؛ در سبد برای مهمان کادر کد نیست.
- **کارت شانس حساب‌محور**: `POST /lucky/spin` (فقط با حساب، هر `cooldownHours` ساعت یک‌بار، پشت‌سرهم رد می‌شود)؛ جایزه = کد شخصی یک‌بارمصرف `LK-…` (`Coupon.owner`، `max_uses=1`، انقضا). جایزه‌ها/وزن/فاصله از پنل. کدهای همگانیِ قدیمی (LUCK5 …) غیرفعال شدند.
- **ارسال از پنل**: مدل `ShippingMethod` + تنظیم `shipping` (سقف رایگان) در `SiteSetting`؛ `pricing.shipping_options()` مرجع محاسبه است؛ حداقل یک روش فعال می‌ماند.
- **محتوا از پنل**: `GET /site` (اطلاعات تماس/متن‌ها/ارسال/صفحات/کارت شانس) → `stores/shop.js`؛ صفحات `Page` با نمای امن `utils/richtext.js` در `/page/:slug`؛ فرم مشاوره `ConsultRequest`.
- **تاریخ‌ها همه شمسی**: `data/jalali.js` (نمایش با `fa-IR-u-ca-persian`؛ ورودی مدیر `۱۴۰۵/۱۲/۲۹` ↔ ISO). تاریخ میلادی فقط در sitemap و پنل `dj-admin` جنگو.
- اجرای همهٔ تست‌ها: `bash scripts/run_all_tests.sh` (سرور تازه برای هر مجموعه؛ سقف نرخ ورود بین مجموعه‌ها نشت نکند).

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
