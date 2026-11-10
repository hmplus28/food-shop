# بک‌اند فروشگاه خانم گل (Django + DRF)

REST API کامل فروشگاه: احراز هویت با رمز یا **کد یکبار مصرف پیامکی**، محصولات،
سفارش‌ها (با محاسبهٔ قیمت سمت سرور)، پنل مدیر و **اتصال به پنل پیامکی**
(کاوه‌نگار / SMS.ir / قاصدک / ملی پیامک).

- پایگاه داده: SQLite (بدون نیاز به سرور جدا — برای شروع و فروشگاه‌های متوسط کافی است)
- تنها وابستگی‌ها: Django + DRF + SimpleJWT + cors-headers + whitenoise (همه در `requirements.txt`)

## اجرای سریع محلی

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate     # اختیاری ولی پیشنهادی
pip install -r requirements.txt
cp .env.example .env                # مقادیر را ویرایش کنید (به‌خصوص ADMIN_PASSWORD)
python manage.py migrate
python manage.py seed_shop          # ۲۸ محصول پایه + حساب مدیر
python manage.py runserver          # پیش‌فرض: http://127.0.0.1:8787
```

> اگر `seed_shop` را فراموش کنید هم مشکلی نیست: اولین درخواست به `/api/v1/health`
> یا `/api/v1/products` خودش محصولات و حساب مدیر را می‌سازد.

سرور روی `http://127.0.0.1:8787` بالا می‌آید و پنل ادمین جنگو هم روی
`http://127.0.0.1:8787/dj-admin/` در دسترس است.

## اتصال فرانت (Vue) به این بک‌اند

آدرس بک‌اند در زمان «بیلد» فرانت داخل باندل می‌رود:

```bash
cd app
VITE_API_ENABLED=true VITE_API_BASE=https://آدرس-بک‌اند/api/v1 VITE_BASE=/food-shop/ npm run build
cp -r dist/. ..       # انتشار در ریشهٔ ریپو (GitHub Pages) یا هاست
```

تا وقتی بک‌اند در دسترس نباشد، فروشگاه بی‌صدا به دادهٔ محلی مرورگر برمی‌گردد
(هیچ‌وقت صفحهٔ خطا نمی‌بینید). قرارداد کامل نقاط پایانی در
`app/src/services/api.js` مستند است.

## نقاط پایانی API (پیشوند `/api/v1`)

| نقطهٔ پایانی | متد | دسترسی | توضیح |
| --- | --- | --- | --- |
| `/health` | GET | عمومی | سلامت سرویس + وضعیت پنل پیامک |
| `/auth/register` | POST | عمومی | `{name, phone, password}` → `{ok, user, token}` |
| `/auth/login` | POST | عمومی | `{phone, password}` → `{ok, user, token}` |
| `/auth/otp/request` | POST | عمومی | `{phone}` → ارسال کد پیامکی (فاصلهٔ ارسال + سقف ساعتی دارد) |
| `/auth/otp/verify` | POST | عمومی | `{phone, code}` → ورود/ثبت‌نام خودکار + توکن |
| `/auth/me` | GET | توکن | پروفایل کاربر جاری |
| `/products` | GET | عمومی | فهرست محصولات (`?all=1` فقط مدیر: با پنهان‌ها) |
| `/products` | POST | مدیر | افزودن محصول (شناسه طبق قانون فرانت: max(100)+1) |
| `/products/{id}` | GET/PUT/DELETE | عمومی/مدیر | جزئیات/ویرایش/حذف |
| `/orders` | POST | عمومی | ثبت سفارش — **مبالغ سمت سرور دوباره محاسبه می‌شوند** |
| `/orders` | GET | مدیر | فهرست سفارش‌ها `?status=&phone=&q=&limit=` |
| `/orders/mine` | GET | توکن | سفارش‌های کاربر جاری |
| `/orders/{code}` | GET | عمومی | پیگیری با کد سرور (`KG-…`) یا کد مرورگر (`AS-…`) |
| `/orders/{code}` | PATCH | مدیر | تغییر وضعیت ۰..۳ + **پیامک به مشتری** |
| `/admin/login` | POST | عمومی | ورود مدیر → توکن نقش admin |
| `/admin/stats` | GET | مدیر | آمار فروشگاه + وضعیت پیامک |
| `/admin/sms` | GET | مدیر | گزارش ۵۰ پیامک آخر |
| `/admin/sms/test` | POST | مدیر | ارسال پیامک آزمایشی `{to, text?}` |

خطاهای منطقی با کد ۲۰۰ و `{ok:false, msg:"فارسی"}` برمی‌گردند تا فرانت پیام را
مستقیم نمایش دهد؛ خطاهای ساختاری ۴۰۰ هستند.

## اتصال پنل پیامکی 📩

در `backend/.env` سرویس‌دهنده را انتخاب کنید و کلیدها را بدهید. پیامک‌های
زیر خودکار ارسال می‌شوند:

| رویداد | گیرنده | پیش‌فرض |
| --- | --- | --- |
| کد ورود (OTP) | مشتری | همیشه |
| ثبت سفارش | مشتری + شمارهٔ مدیر | `SMS_ORDER_TO_CUSTOMER=true` + `SHOP_NOTIFY_PHONE` |
| تغییر وضعیت سفارش | مشتری | `SMS_STATUS_TO_CUSTOMER=true` |

### کاوه‌نگار (kavenegar.com)

```env
SMS_PROVIDER=kavenegar
KAVENEGAR_API_KEY=کلید-از-پنل
KAVENEGAR_OTP_TEMPLATE=khanomgol-otp   # نام قالب Verify در پنل (پارامتر {token})
SMS_SENDER=10008663                    # خط خدماتی (اختیاری)
```

قالب را در پنل کاوه‌نگار → «تنظیمات → قالب‌های تایید (Verify)» با متن
مثل «کد ورود شما: %token» بسازید. اگر قالب تعریف نشود، کد به‌صورت پیامک
عادی ارسال می‌شود.

### SMS.ir

```env
SMS_PROVIDER=smsir
SMSIR_API_KEY=کلید-از-پنل
SMSIR_OTP_TEMPLATE_ID=100000           # شناسهٔ عددی قالب (پارامتر قالب باید CODE باشد)
SMSIR_LINE=3000…                       # شماره خط
```

### قاصدک (ghasedak.me)

```env
SMS_PROVIDER=ghasedak
GHASEDAK_API_KEY=کلید-از-پنل
GHASEDAK_OTP_TEMPLATE=khanomgol-otp
GHASEDAK_LINE=5000…
```

### ملی پیامک (payamak-panel.com)

```env
SMS_PROVIDER=melipayamak
MELIPAYAMAK_USERNAME=نام-کاربری-پنل
MELIPAYAMAK_PASSWORD=رمز-پنل
MELIPAYAMAK_FROM=5000…                 # شمارهٔ خط پنل
```

### حالت توسعه (بدون پنل)

`SMS_PROVIDER=console` (پیش‌فرض): پیامک واقعی نمی‌رود؛ کد OTP در پاسخ API
(`dev.code`) و در لاگ سرور می‌آید و همهٔ پیامک‌ها در «پنل پیامک» پنل مدیر
ثبت می‌شوند — برای تست کامل جریان بدون پنل پیامک.

> **تست اتصال:** بعد از تنظیم پنل، در پنل مدیریت فرانت (تب «پنل پیامک»)
> شمارهٔ خودتان را بدهید و «ارسال پیامک تست» بزنید؛ نتیجه در همان جدول ثبت می‌شود.

## استقرار

### سرور مجازی (VPS) با gunicorn

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate && python manage.py seed_shop
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8787 --workers 3
```

با nginx، مسیر `/api/` و `/dj-admin/` را به این سرویس پروکسی کنید. برای
اجر دائمی از `systemd` یا `pm2` (با `--interpreter python3`) استفاده کنید.

### هاست cPanel (Setup Python App)

1. cPanel → **Setup Python App** → نسخهٔ Python ≥ 3.10 → ساخت اپ.
2. فایل‌های پوشهٔ `backend` را روی هاست بگذارید (git clone یا آپلود).
3. «Application startup file» را `passenger_wsgi.py` بگذارید.
4. در ترمینال همان محیط مجازی: `pip install -r requirements.txt` و
   `python manage.py migrate` و `python manage.py seed_shop`.
5. متغیرهای محیطی (`.env` یا از خود رابط cPanel) را تنظیم کنید.
6. دامنهٔ فرانت را در `CORS_ORIGINS` بگذارید.

راهنمای تصویری‌تر و نکات SSL در `deploy/GUIDE-CPANEL-FA.md` هست.

## امنیت — چک‌لیست تولید

- [ ] `ADMIN_PASSWORD` پیش‌فرض (`admin1234`) را عوض کنید.
- [ ] `DEBUG=false` (پیش‌فرض) و `ALLOWED_HOSTS` محدود به دامنهٔ خودتان.
- [ ] `CORS_ORIGINS` فقط دامنهٔ فرانت (به‌جای `*`).
- [ ] `SECRET_KEY` را در `.env` ثابت کنید (در نبودش خودکار ساخته و ذخیره می‌شود).
- [ ] سقف‌های OTP (`OTP_TTL/OTP_COOLDOWN/OTP_HOURLY/OTP_MAX_ATTEMPTS`) را با متن کسب‌وکار تنظیم کنید.
- [ ] پشتیبان‌گیری دوره‌ای از `backend/db.sqlite3`.

## تست

اسکریپت تست انتها-به-انتها (۴۶ بررسی خودکار؛ سرور باید روشن باشد):

```bash
python3 scripts/test_backend_api.py
```

محاسبهٔ قیمت سمت سرور با منطق فرانت «بیت‌به‌بیت» یکی است (همان `priceOf`،
کدهای تخفیف و سقف ارسال رایگان ۱٬۵۰۰٬۰۰۰ تومان) — مجموع، تخفیف و مبلغ
نهایی سفارش همیشه با فاکتور مشتری یکسان است.
