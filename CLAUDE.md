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
python3 scripts/test_backend_api.py        # باید 60/60 سبز باشد
python3 scripts/test_backend_security.py   # باید 69/69 سبز باشد
node scripts/test_cart_ui.js                # سبد خرید (۲۷ بررسی؛ نیاز به vite preview روی 4173)
```

## قواعد مهم
- **قیمت، تخفیف، ارسال و جمع سفارش همیشه سمت سرور محاسبه می‌شود** (`shop/pricing.py`)؛ مقدار مالی کلاینت هرگز اعتماد نمی‌شود.
- ورود با رمز یا OTP پیامکی؛ سقف ارسال/تلاش OTP با env (`OTP_*`) تنظیم می‌شود. `SMS_PROVIDER=console` در توسعه.
- ارقام فارسی/عربی در شماره موبایل نرمال می‌شوند (`normalize_phone`).
- `backend/.env` و `db.sqlite3` را هرگز کامیت نکنید (در `.gitignore`).
- در تولید: `ADMIN_PASSWORD` پیش‌فرض عوض شود، `CORS_ORIGINS` به دامنهٔ فرانت محدود شود، پس از SSL گزینه‌های `SECURE_*` روشن شوند.
- متن‌ها و کامیت‌ها فارسی هستند؛ UI باید RTL و ریسپانسیو (۳۲۰ تا ۱۴۴۰px بدون سرریز افقی) بماند.

## وضعیت بررسی
بیلد فرانت بازتولیدپذیر؛ `manage.py check` و `makemigrations --check` تمیز؛ ریسپانسیو در عرض‌های ۳۲۰/۳۷۵/۷۶۸/۱۰۲۴/۱۴۴۰ روی تمام مسیرها بدون سرریز و خطا.
