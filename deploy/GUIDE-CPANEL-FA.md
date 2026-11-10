# راهنمای استقرار فروشگاه خانم گل روی هاست اشتراکی cPanel

این راهنما برای انتشار نسخهٔ **Vue 3 + Vite** فروشگاه روی هاست cPanel است
(برای GitHub Pages نیازی به این مراحل نیست — بیلد در ریشهٔ ریپو همان انتشار است).

## خلاصهٔ سریع

```bash
# ── فرانت (روی هاست، ترمینال cPanel یا SSH): ──
git clone https://github.com/hmplus28/food-shop.git   # یا git pull برای به‌روزرسانی
cd food-shop
bash deploy/deploy_cpanel.sh --webroot ~/public_html

# ── بک‌اند (پوشهٔ backend، ترمینال cPanel یا SSH): ──
cd backend
bash deploy/deploy_cpanel.sh
```

فرانت: بیلدِ آماده در گیت هست و روی هاست به Node نیازی نیست.
بک‌اند: اسکریپت خودش پایتون ≥۳.۱۰ را پیدا می‌کند، venv می‌سازد (یا venv سی‌پنل
را شناسایی می‌کند)، وابستگی‌ها را نصب، مایگریشن و seed را اجرا،
`passenger_wsgi.py` و `.htaccess` امن می‌سازد و `SECRET_KEY` و
`ADMIN_PASSWORD` تصادفی تولید می‌کند.

## روش‌های بردن ریپو روی هاست

| روش | مراحل |
| --- | --- |
| **Git_version_control در cPanel** (پیشنهادی) | cPanel → «Git™ Version Control» → Create → آدرس ریپو → Clone |
| SSH | `ssh user@host` سپس `git clone …` |
| آپلود دستی | دانلود ZIP از GitHub → آپلود در File Manager → Extract (به‌روزرسانی‌های بعدی دستی می‌شود) |

> بهتر است ریپو **خارج از ریشهٔ وب** باشد (مثلاً `~/repos/food-shop`) و اسکریپت فقط
> فایل‌های انتشار را به `~/public_html` کپی کند؛ اگر ریپو داخل ریشهٔ وب است نگران
> نباشید — `.htaccess` ساخته‌شده مسیرهای `app/`, `deploy/`, `scripts/`, `download/`,
> `upload/`, `skills/` و `.git` را مسدود می‌کند.

## گزینه‌های اسکریپت

```bash
bash deploy/deploy_cpanel.sh                          # پیش‌فرض: کپی بیلد commit‌شده
bash deploy/deploy_cpanel.sh --webroot ~/public_html  # تعیین ریشهٔ وب مقصد
bash deploy/deploy_cpanel.sh --clean                  # پاک‌سازی کامل ریشهٔ وب قبل از کپی (احتیاط!)
bash deploy/deploy_cpanel.sh --build                  # بیلد روی خود هاست (نیاز به Node ≥18)
bash deploy/deploy_cpanel.sh --build --base /         # بیلد با مسیر پایهٔ دامنهٔ اختصاصی (پیش‌فرض)
bash deploy/deploy_cpanel.sh --build --api-base https://api.example.ir/api/v1 --api-enabled
```

## دو نکتهٔ مهم دربارهٔ مسیر پایه و بک‌اند

### ۱) مسیر پایه (VITE_BASE)

بیلدِ commit‌شده در ریشهٔ ریپو برای **GitHub Pages** با مسیر پایهٔ `/food-shop/`
بسته شده است. اگر دامنهٔ cPanel را مستقیم روی ریشهٔ وب نشانه بروید، css/js لود
نمی‌شود. اسکریپت این را تشخیص می‌دهد و هشدار می‌دهد؛ کافی است یک‌بار بگیرید:

```bash
bash deploy/deploy_cpanel.sh --build        # Vite با VITE_BASE=/ بیلد می‌گیرد
```

### ۲) اتصال به بک‌اند (VITE_API_BASE)

آدرس بک‌اند در **زمان بیلد** داخل باندل می‌رود (بعد از build، تغییر `.env` بی‌اثر است).

```bash
# روی هاست:
bash deploy/deploy_cpanel.sh --build \
  --api-base https://دامنه-بک‌اند/api/v1 --api-enabled
```

یا دستی: `app/.env` را ویرایش کنید (`VITE_API_ENABLED=true` و `VITE_API_BASE=…`)
و `--build` بگیرید. قرارداد کامل نقاط پایانی در `app/.env.example` هست:

| نقطهٔ پایانی | روش | پاسخ |
| --- | --- | --- |
| `{BASE}/health` | GET | `{ok, sms:{provider, configured}}` (تست اتصال) |
| `{BASE}/products` | GET | آرایهٔ محصولات |
| `{BASE}/orders` | POST | `{code, status, total}` |
| `{BASE}/orders/{code}` | GET | `{code, status}` (پیگیری) |
| `{BASE}/orders/{code}` | PATCH | `{code, status}` (تغییر وضعیت مدیر) |
| `{BASE}/auth/register` | POST | `{ok, user?, token?}` |
| `{BASE}/auth/login` | POST | `{ok, user?, token?}` |
| `{BASE}/auth/otp/request` | POST | ارسال کد ورود پیامکی |
| `{BASE}/auth/otp/verify` | POST | `{ok, user?, token?}` |
| `{BASE}/admin/login` | POST | `{ok, token?}` (توکن نقش مدیر) |
| `{BASE}/admin/stats` | GET | آمار فروشگاه (مدیر) |
| `{BASE}/admin/sms` | GET | گزارش پیامک‌ها (مدیر) |

تا بک‌اند در دسترس نباشد یا پاسخ ندهد، فروشگاه **بی‌صدا** به دادهٔ محلی برمی‌گردد
(هیچ‌وقت صفحهٔ خطا نمی‌بینید).

## بک‌اند Django (پوشهٔ `backend`)

بک‌اند کامل فروشگاه با **Django 5 + DRF** در پوشهٔ `backend` قرار دارد:
احراز هویت با رمز یا کد پیامکی (OTP)، محصولات، سفارش‌ها با محاسبهٔ قیمت سمت
سرور، پنل مدیر و اتصال به پنل پیامکی (کاوه‌نگار / SMS.ir / قاصدک / ملی پیامک).
جزئیات کامل و جدول همهٔ نقاط پایانی در `backend/README.md` هست.

### استقرار خودکار با اسکریپت (پیشنهادی)

```bash
cd ~/repos/food-shop/backend     # یا هر مسیری که ریپو را کلون کردید
bash deploy/deploy_cpanel.sh
```

اسکریپت به‌ترتیب این کارها را انجام می‌دهد:

1. **پایتون ≥۳.۱۰** را پیدا می‌کند (`/opt/alt/python3XX` کلودلینوکس هم چک می‌شود)
2. **venv**: اول venv سی‌پنلِ همین پروژه (`~/virtualenv/…` اگر Setup Python App
   ساخته باشید) را شناسایی می‌کند؛ نبود، `.venv-host` می‌سازد
3. **.env**: نبود را با کلیدهای امن می‌سازد — `SECRET_KEY` و `ADMIN_PASSWORD`
   تصادفی؛ مقادیر موجود هرگز بازنویسی نمی‌شوند و فایل دست‌کاری‌شده پاک‌سازی می‌شود
4. **مایگریشن + seed_shop** (۲۸ محصول + حساب مدیر، idempotent) + **collectstatic**
5. **passenger_wsgi.py** را بر اساس نوع venv می‌سازد (سی‌پنل: بدون re-exec؛
   معمولی: با re-exec — تا خطای ۵۰۳ لودر lswsgi پیش نیاید)
6. **.htaccess امن**: دانلود `.env`، دیتابیس، سورس‌ها و لاگ‌ها را از وب می‌بندد
7. **پشتیبان دیتابیس** قبل از هر استقرار در `backups/` و ری‌استارت Passenger

گزینه‌ها:

```bash
bash backend/deploy/deploy_cpanel.sh --venv ~/virtualenv/backend/3.11  # venv مشخص
bash backend/deploy/deploy_cpanel.sh --python /opt/alt/python311/bin/python3.11
```

### بعد از استقرار بک‌اند — ۵ دقیقه تنظیم

1. cPanel → **Setup Python App** → بررسی: Python ‏۳.۱۱+، Application root =
   پوشهٔ `backend`، Startup File = `passenger_wsgi.py`
2. `backend/.env` را ویرایش کنید و سپس `touch backend/tmp/restart.txt`:

```env
ALLOWED_HOSTS=دامنه-بک‌اند.ir
CORS_ORIGINS=https://دامنه-فرانت.ir
SHOP_NOTIFY_PHONE=0912…          # پیامک «سفارش جدید» به مدیر
SMS_PROVIDER=kavenegar           # یا smsir / ghasedak / melipayamak / console
KAVENEGAR_API_KEY=…
KAVENEGAR_OTP_TEMPLATE=khanomgol-otp
SECURE_SSL_REDIRECT=True         # فقط بعد از فعال‌شدن https
SECURE_HSTS_SECONDS=31536000
```

3. تست سلامت: `https://دامنه-بک‌اند/api/v1/health` → باید `{"ok":true,…}` بدهد

### اتصال فرانت به بک‌اند

آدرس بک‌اند در زمان بیلد داخل باندل فرانت می‌رود؛ پس بعد از بالا آمدن بک‌اند
یک‌بار فرانت را با پارامترهای بک‌اند بیلد و استقرار کنید:

```bash
# ریشهٔ ریپو (اسکریپت فرانت):
bash deploy/deploy_cpanel.sh --build \
  --api-base https://دامنه-بک‌اند/api/v1 --api-enabled
```

پیامک‌های خودکار: کد ورود (OTP)، تأیید سفارش به مشتری، اطلاع سفارش جدید به
مدیر و تغییر وضعیت سفارش به مشتری. تست سریع: پنل مدیریت فرانت → تب
«پنل پیامک» → «ارسال پیامک تست». تا وقتی پنل پیامک تنظیم نشده
(`SMS_PROVIDER=console`) همه‌چیز کار می‌کند و پیامک‌ها فقط ثبت می‌شوند.

### راه‌اندازی روی سرور مجازی (VPS)

```bash
cd backend && pip install -r requirements.txt
python manage.py migrate && python manage.py seed_shop && python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8787 --workers 3
```

## SSL و دامنه

1. cPanel → **Domains / Subdomains**: ریشهٔ وب (Document Root) را روی همان مسیری
   بگذارید که به اسکریپت دادید (پیش‌فرض `~/public_html`).
2. cPanel → **SSL/TLS Status** → **AutoSSL** را فعال/اجرا کنید تا https کار کند.
3. بعد از https، آدرس بک‌اند هم باید `https://` باشد (وگرنه مرورگر درخواست mixed-content را می‌بندد).
4. اگر بک‌اند جداگانه است، CORS را تنظیم کنید (مثلاً Django:
   `CORS_ALLOWED_ORIGINS=https://دامنه-فرانت-شما`).

## به‌روزرسانی‌های بعدی

```bash
# روی ماشین محلی (تغییر کد):
cd app && npm run build && cp -r dist/. ..
git add -A && git commit -m "build: …" && git push

# روی هاست:
cd food-shop && git pull && bash deploy/deploy_cpanel.sh
```

## عیب‌یابی

| نشانه | علت احتمالی / راه‌حل |
| --- | --- |
| صفحهٔ سفید، خطای ۴۰۴ برای `/assets/…` در کنسول | بیلد با مسیر پایهٔ `/food-shop/` منتشر شده → `--build` بگیرید |
| رفرش مسیرهای عمیق (`/products`) خطای ۴۰۴ می‌دهد | `.htaccess` ساخته نشده — اسکریپت را دوباره اجرا کنید؛ اگر Apache اجازهٔ Override نمی‌دهد، در cPanel → MultiPHP INI / پشتیبانی هاست `AllowOverride All` را بخواهید |
| css/js لود می‌شود ولی داده‌ها از سرور نمی‌آیند | `VITE_API_BASE` placeholder است یا `VITE_API_ENABLED=false` → `--build --api-base … --api-enabled` |
| «Node ≥18 پیدا نشد» هنگام `--build` | در cPanel «Setup Node.js App» برنامه بسازید یا `--node /opt/alt/alt-nodejs18/bin/node` بدهید؛ یا بیلد را محلی بگیرید و commit کنید (پیشنهادی) |
| تغییرات دیده نمی‌شود | کش مرورگر — `index.html` بدون کش منتشر می‌شود؛ با Ctrl+F5 بگیرید |
| خطای ۵۰۰ | مالکیت/سطح دسترسی فایل‌ها را در File Manager چک کنید (۶۴۴ برای فایل‌ها) |
| بک‌اند خطای ۵۰۳ می‌دهد (Passenger) | بعد از هر تغییر venv/passenger_wsgi.py باید ری‌استارت شود: `touch backend/tmp/restart.txt`؛ اگر venv سی‌پنل است مطمئن شوید Startup File همان `passenger_wsgi.py` است |
| «پایتون ≥3.10 پیدا نشد» در اسکریپت بک‌اند | در cPanel → Setup Python App یک برنامه با Python 3.11 بسازید (Application root = پوشهٔ backend) و اسکریپت را دوباره اجرا کنید؛ یا مسیر بدهید: `--python /opt/alt/python311/bin/python3.11` |
| `api/v1/health` پاسخ نمی‌دهد | `ALLOWED_HOSTS` در `backend/.env` دامنه را ندارد → ویرایش و `touch tmp/restart.txt`؛ لاگ‌ها: `backend/logs/` |
| فرانت به بک‌اند وصل نمی‌شود (CORS) | `CORS_ORIGINS` در `backend/.env` باید دقیقاً دامنهٔ فرانت باشد (با https و بدون اسلش آخر) |

## امنیت و تست‌ها

- `.htaccess` ساخته‌شده مسیرهای حساس ریپو (`app/`, `deploy/`, `scripts/`, `download/`, `upload/`, `skills/`, `.git`, `.env`) و فایل‌های پیکربندی را از وب مسدود می‌کند و هدرهای `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` را فعال می‌سازد.
- **CSP**: بلوک پیشنهادی به‌صورت کامنت در قالب `.htaccess` هست؛ قبل از فعال‌سازی دامنهٔ بک‌اند را در `connect-src` بگذارید.
- تست‌های امنیتی پروژه (بررسی ایستا + پروب XSS پویا + `npm audit`): با `Vite ≥ 6.4.6` الان **۰ آسیب‌پذیری** دارد؛ بعد از تغییر کد `cd app && npm audit` را تکرار کنید.
- **تست امنیتی بک‌اند** (۶۹ بررسی: تزریق، JWT، IDOR، throttle OTP، دستکاری مالی): `python scripts/test_backend_security.py` — همه سبز.
- **تست ریسپانسیو موبایل** (۶ دستگاه از ۳۲۰px تا تبلت × ۷ صفحه): ۰ سرریز افقی، ۰ خطای کنسول؛ اسکریپت: `python scripts/mobile_test.py`.
- پس از اتصال بک‌اند: رمز و نقش مدیر باید سمت سرور بیاید (در دموی فعلی `admin/admin1234` فقط محلی است) و CORS بک‌اند فقط به دامنهٔ فرانت اجازه بدهد.

## چه چیزی به ریشهٔ وب کپی می‌شود؟

- `index.html` (بیلد)
- `assets/` (css/js هش‌شده — کاملاً جایگزین می‌شود)
- `404.html`، `robots.txt`، `sitemap.xml`، `.nojekyll` (محتویات `app/public`)
- `.htaccess` (ساخته/به‌روزرسانی می‌شود — بلوک `KHANOMGOL-SPA`)

سایر فایل‌های ریشهٔ وب دست نمی‌خورند (مگر با `--clean` که همه — جز `cgi-bin` — را پاک می‌کند).
