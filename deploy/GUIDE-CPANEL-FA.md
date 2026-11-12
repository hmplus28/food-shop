# راهنمای کامل استقرار فروشگاه خانم گل روی cPanel

سه بخش دارد: **دیتابیس MySQL**، **بک‌اند Django** و (اختیاری) **فرانت Vue روی خود هاست**.
فرانت اصلی فروشگاه روی GitHub Pages منتشر می‌شود و نیازی به این مراحل ندارد —
بیلدِ commit‌شده در ریشهٔ ریپو همان انتشار است.

## پیکربندی فعلی هاست (مقادیر واقعی)

| مورد | مقدار |
| --- | --- |
| کاربر cPanel | `khanomgo` |
| پوشهٔ برنامهٔ بک‌اند (Application Root) | `/home/khanomgo/public_html/food-shop` |
| محیط مجازی Python | `/home/khanomgo/virtualenv/public_html/food-shop/3.11` |
| نسخهٔ Python | ‏3.11 (برنامهٔ «Setup Python App» ساخته شده) |
| دیتابیس | **MySQL** — ساخته‌شده از cPanel → «MySQL® Databases» |
| آدرس API روی هاست | `https://دامنه-شما/food-shop/api/v1/…` |
| فرانت فروشگاه | `https://hmplus28.github.io/food-shop/` |

> اسکریپت بک‌اند این مسیرها را خودش پیدا می‌کند؛ چون venv سی‌پنل از الگوی
> `~/virtualenv/<مسیر-نسبی-پوشهٔ-برنامه>/<نسخه>` پیروی می‌کند و پوشهٔ برنامه
> `~/public_html/food-shop` است، به‌صورت خودکار شناسایی می‌شود.

---

## گام ۰ — ساخت دیتابیس MySQL (یک‌بار، ۳ دقیقه)

cPanel → **MySQL® Databases**:

1. **Create New Database** → نام: `foodshop`
   (سی‌پنل پیشوند حساب را خودش می‌گذارد → نام کامل: `khanomgo_foodshop`)
2. **MySQL Users → Add New User** → نام: `shop` (کامل: `khanomgo_shop`) + رمز قوی.
   از «Password Generator» سی‌پنل استفاده کنید و رمز را همان لحظه ذخیره کنید.
3. **Add User To Database** → هر دو را انتخاب کنید → تیک **ALL PRIVILEGES** → «Make Changes»
4. پیشنهادی: phpMyAdmin → انتخاب دیتابیس → Operations → Collation:
   `utf8mb4_unicode_ci` (پشتیبانی کامل فارسی)

این سه مقدار را (`DB_NAME`، `DB_USER`، `DB_PASSWORD`) برای گام ۲ نگه دارید.

## گام ۱ — بردن کد بک‌اند به پوشهٔ برنامه

در ترمینال cPanel یا SSH:

```bash
cd ~
# اگر قبلاً کلون شده فقط آپدیت کنید:
if [ -d ~/food-shop-repo/.git ]; then (cd ~/food-shop-repo && git pull); else
  git clone https://github.com/hmplus28/food-shop.git ~/food-shop-repo; fi

# اولین بار — ساخت پوشهٔ برنامه و کپی بک‌اند:
mkdir -p ~/public_html/food-shop
cp -r ~/food-shop-repo/backend/. ~/public_html/food-shop/
```

به‌روزرسانی‌های بعدی (بدون دست زدن به `.env`، استاتیک‌ها و پشتیبان‌ها):

```bash
rsync -a --delete \
  --exclude '.env' --exclude '.env.*' --exclude 'db.sqlite3' \
  --exclude 'staticfiles' --exclude 'backups' --exclude 'logs' --exclude 'tmp' \
  ~/food-shop-repo/backend/ ~/public_html/food-shop/
```

اگر rsync در دسترس نبود، همان `cp -r ~/food-shop-repo/backend/. ~/public_html/food-shop/`
کافی است — فایل `.env` روی هاست بازنویسی نمی‌شود چون در ریپو وجود ندارد.

## گام ۲ — پر کردن `.env`

اگر `.env` هنوز ساخته نشده، گام ۳ خودش آن را با مقادیر امن می‌سازد و در پایان
می‌گوید چه چیزهایی باید پر شود. برای دیتابیس این چهار خط لازم است:

```env
DB_ENGINE=mysql
DB_NAME=khanomgo_foodshop
DB_USER=khanomgo_shop
DB_PASSWORD=رمزی-که-در-گام-۰-ساختید
DB_HOST=localhost
DB_PORT=3306
```

## گام ۳ — اجرای اسکریپت استقرار

```bash
source /home/khanomgo/virtualenv/public_html/food-shop/3.11/bin/activate
cd /home/khanomgo/public_html/food-shop
bash deploy/deploy_cpanel.sh
```

اسکریپت خودکار این کارها را می‌کند:

1. **پایتون ≥۳.۱۰** را پیدا می‌کند (`/opt/alt/python3XX` کلودلینوکس هم چک می‌شود)
2. **venv سی‌پنلِ همین پروژه** را شناسایی می‌کند (`~/virtualenv/public_html/food-shop/3.11`)
3. **وابستگی‌ها** را نصب می‌کند (شامل `PyMySQL` برای MySQL — خالص‌پایتون، بدون کامپایل)
4. **.env**: کلیدهای غایب را با مقادیر امن اضافه می‌کند (`SECRET_KEY` و
   `ADMIN_PASSWORD` تصادفی)؛ مقادیر موجود بازنویسی نمی‌شوند و فایل
   دست‌کاری‌شده پاک‌سازی می‌شود — و **پیکربندی MySQL را کنترل می‌کند**:
   اگر `DB_NAME/DB_USER/DB_PASSWORD` خالی باشد با راهنمای دقیق متوقف می‌شود
5. **مایگریشن‌ها روی MySQL** + درج اولیهٔ محصولات (seed_shop — idempotent) + **collectstatic**
6. **passenger_wsgi.py** مناسب venv سی‌پنل می‌سازد (بدون re-exec — تا خطای ۵۰۳ لودر lswsgi پیش نیاید)
7. **.htaccess امن**: دانلود `.env`، سورس‌ها و لاگ‌ها را از وب می‌بندد
8. **پشتیبان اولیهٔ MySQL** با `mysqldump` در `backups/` + ری‌استارت برنامه

تست محلی بدون MySQL (روی سیستم خودتان): `KHANOMGOL_ALLOW_SQLITE=1 bash deploy/deploy_cpanel.sh`

## گام ۴ — تست سلامت

| آدرس | پاسخ مورد انتظار |
| --- | --- |
| `https://دامنه-شما/` | صفحهٔ فروشگاه (اگر فرانت روی خود هاست منتشر شده باشد — **نه** «It works! Python») |
| `https://دامنه-شما/food-shop/api/v1/health` | `{"ok":true,"sms":{...}}` |
| `https://دامنه-شما/food-shop/dj-admin/` | صفحهٔ ورود ادمین جنگو (با CSS) |

### اگر صفحهٔ «It works! Python 3.11.18» به‌جای فروشگاه دیدید

این صفحهٔ نمایشیِ خودِ «Setup Python App» است — نه خطای بک‌اند. وقتی برنامهٔ
پایتون با **Application URL = `/`** ساخته شود، Passenger **همهٔ درخواست‌های
دامنه را می‌رباید** و به همان اپ نمایشی می‌دهد؛ یعنی فروشگاه استاتیکِ
`public_html` هم زیر این صفحه پنهان می‌شود. (`passenger_wsgi.py` واقعی هم
اگر داخل `backend/` باشد اصلاً خوانده نمی‌شود، چون Passenger فقط ریشهٔ
Application Root را نگاه می‌کند و آنجا نسخهٔ demo سی‌پنل نشسته است.)

رفع در ۳ قدم:

**۱) Application URL را از `/` به `/food-shop` تغییر دهید** — در cPanel →
Setup Python App → روی برنامه **Edit** بزنید → «Application URL» →
`/food-shop` → **Save**. از این پس فقط مسیرهای `/food-shop/…` (بک‌اند) به
Passenger می‌روند و ریشهٔ دامنه به فایل‌های استاتیک فروشگاه.

**۲) فایل `passenger_wsgi.py` درست را در ریشهٔ برنامه بگذارید و وابستگی‌ها را داخل venv سی‌پنل نصب کنید** — هر دو را یک‌جا این‌طور انجام دهید (کد به‌روز + اجرای دوبارهٔ اسکریپت که حالا venv سی‌پنل را خودکار می‌شناسد و Startup File ریشه را خودش می‌نویسد):

```bash
source /home/khanomgo/virtualenv/public_html/food-shop/3.11/bin/activate
# کد به‌روز را بگیرید (یا اگر کلون ندارید بسازید)
if [ -d ~/food-shop-repo/.git ]; then (cd ~/food-shop-repo && git pull); else
  git clone https://github.com/hmplus28/food-shop.git ~/food-shop-repo; fi
# بک‌اند به‌روز را در پوشهٔ برنامهٔ سی‌پنل همگام کنید (بدون دست زدن به .env و استاتیک‌ها)
mkdir -p ~/public_html/food-shop/backend
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude '.env' --exclude '.env.*' --exclude '.venv-host' \
    --exclude 'staticfiles' --exclude 'backups' --exclude 'logs' --exclude 'tmp' \
    ~/food-shop-repo/backend/ ~/public_html/food-shop/backend/
else
  cp -r ~/food-shop-repo/backend/. ~/public_html/food-shop/backend/
fi
# اگر .env فقط داخل کلون بود، یک‌بار به پوشهٔ برنامه بیاورید
[ -f ~/public_html/food-shop/backend/.env ] || \
  cp ~/food-shop-repo/backend/.env ~/public_html/food-shop/backend/.env 2>/dev/null || true
cd ~/public_html/food-shop/backend
KHANOMGOL_APP_ROOT=/home/khanomgo/public_html/food-shop bash deploy/deploy_cpanel.sh
touch ~/public_html/food-shop/tmp/restart.txt
```

اگر اسکریپت برای «پیکربندی دیتابیس MySQL ناقص» توقف کرد، یعنی `.env` این پوشه
رمز دیتابیس را ندارد — همان رمز گام ۰ را در `DB_PASSWORD` بگذارید و دوباره اجرا کنید.

`KHANOMGOL_APP_ROOT` می‌گوید Application Root واقعی سی‌پنل کجاست تا
`passenger_wsgi.py` حتی اگر اسکریپت را از جای دیگری اجرا کنید، دقیقاً در
همان پوشه نوشته شود (نسخهٔ نمایشی سی‌پنل هم خودکار در `passenger_wsgi.py.kg-backup` پشتیبان می‌شود).

**۳) تست:** رفرش `https://دامنه-شما/` باید فروشگاه را نشان دهد و
`/food-shop/api/v1/health` باید JSON بدهد. بعد از هر تغییر در پنل، دکمهٔ
**Restart** را بزنید یا `touch ~/public_html/food-shop/tmp/restart.txt`.

اگر ۵۰۳ گرفتید: cPanel → Setup Python App → دکمهٔ **Restart**؛ و مطمئن شوید
Startup File همان `passenger_wsgi.py` است. پس از هر تغییر `.env`:
`touch ~/public_html/food-shop/tmp/restart.txt`

## گام ۵ — تنظیمات پس از استقرار (۵ دقیقه)

`.env` را ویرایش کنید و سپس `touch tmp/restart.txt` بزنید:

```env
ALLOWED_HOSTS=دامنه-شما.ir
CORS_ORIGINS=https://hmplus28.github.io
ADMIN_PASSWORD=یک-رمز-قوی        # اگر تصادفی ساخته شده، از خروجی اسکریپت کپی کنید
SHOP_NOTIFY_PHONE=0912…          # پیامک «سفارش جدید» به مدیر
SMS_PROVIDER=kavenegar           # یا smsir / ghasedak / melipayamak / console
KAVENEGAR_API_KEY=…
KAVENEGAR_OTP_TEMPLATE=khanomgol-otp
SECURE_SSL_REDIRECT=True         # فقط بعد از فعال‌شدن https
SECURE_HSTS_SECONDS=31536000
```

پس از نصب SSL روی دامنه (cPanel → SSL/TLS Status → AutoSSL) این دو مقدار را
روشن کنید؛ قبل از https فعال‌شان نکنید.

## گام ۶ — اتصال فرانت به بک‌اند

آدرس بک‌اند در **زمان بیلد** داخل باندل فرانت می‌رود (بعد از build تغییر `.env`
بی‌اثر است). پس بعد از بالا آمدن بک‌اند، فرانت را یک‌بار با آدرس هاست بیلد و
انتشار کنید:

```bash
# روی هاست (یا محلی) — ریشهٔ ریپو:
bash deploy/deploy_cpanel.sh --build \
  --api-base https://دامنه-شما/food-shop/api/v1 --api-enabled
```

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

تا بک‌اند در دسترس نباشد، فروشگاه **بی‌صدا** به دادهٔ محلی برمی‌گردد
(هیچ‌وقت صفحهٔ خطا نمی‌بینید).

## گام ۷ — پشتیبان‌گیری دوره‌ای MySQL (Cron)

یک‌بار فایل `~/.my.cnf` بسازید (تا رمز داخل خود دستور cron نباشد):

```
[client]
user=khanomgo_shop
password=رمز-دیتابیس
```

سطح دسترسی: `chmod 600 ~/.my.cnf` — سپس در cPanel → **Cron Jobs**:

```cron
0 3 * * * mysqldump --no-defaults -h localhost khanomgo_foodshop | gzip > ~/public_html/food-shop/backups/db-$(date +\%F).sql.gz && find ~/public_html/food-shop/backups -name 'db-*.sql.gz' -mtime +30 -delete
```

(هر شب ساعت ۳ صبح، پشتیبان فشردهٔ روزانه، نگهداری ۳۰ روز.)

---

## انتشار فرانت روی خود cPanel (اختیاری)

```bash
git clone https://github.com/hmplus28/food-shop.git   # یا git pull برای به‌روزرسانی
cd food-shop
bash deploy/deploy_cpanel.sh --webroot ~/public_html
```

بیلدِ آماده در گیت هست و روی هاست به Node نیازی نیست. اسکریپت فرانت
`.htaccess` ساخته‌شده را طوری می‌نویسد که مسیرهای `/food-shop/…`
(برنامهٔ بک‌اند) به SPA ریدایرکت نشوند — API با رفرش مستقیم هم کار می‌کند.

> نکتهٔ مسیر پایه: بیلدِ commit‌شده برای GitHub Pages با `/food-shop/` بسته شده.
> برای دامنهٔ اختصاصی cPanel یک‌بار با `--build` بگیرید تا با `VITE_BASE=/` بیلد شود.
> و برای اتصال به بک‌اند: `--api-base https://دامنه-شما/food-shop/api/v1 --api-enabled`.

## گزینه‌های اسکریپت

```bash
bash deploy/deploy_cpanel.sh                          # پیش‌فرض: کپی بیلد commit‌شده
bash deploy/deploy_cpanel.sh --webroot ~/public_html  # تعیین ریشهٔ وب مقصد
bash deploy/deploy_cpanel.sh --clean                  # پاک‌سازی کامل ریشهٔ وب قبل از کپی (احتیاط!)
bash deploy/deploy_cpanel.sh --build                  # بیلد روی خود هاست (نیاز به Node ≥18)
bash deploy/deploy_cpanel.sh --build --base /         # بیلد با مسیر پایهٔ دامنهٔ اختصاصی
bash deploy/deploy_cpanel.sh --build --api-base https://دامنه-شما/food-shop/api/v1 --api-enabled
```

اسکریپت بک‌اند:

```bash
bash deploy/deploy_cpanel.sh --venv ~/virtualenv/public_html/food-shop/3.11   # venv مشخص
bash deploy/deploy_cpanel.sh --python /opt/alt/python311/bin/python3.11      # پایتون مشخص
KHANOMGOL_ALLOW_SQLITE=1 bash deploy/deploy_cpanel.sh                        # تست محلی بدون MySQL
KHANOMGOL_APP_ROOT=~/public_html/food-shop bash deploy/deploy_cpanel.sh      # نوشتن Startup File در ریشهٔ برنامهٔ سی‌پنل
```

## راه‌اندازی روی سرور مجازی (VPS)

```bash
cd backend && pip install -r requirements.txt
python manage.py migrate && python manage.py seed_shop && python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8787 --workers 3
```

## عیب‌یابی

| نشانه | علت احتمالی / راه‌حل |
| --- | --- |
| «پیکربندی دیتابیس MySQL ناقص است» | `DB_NAME/DB_USER/DB_PASSWORD` در `.env` خالی است — گام ۰ و گام ۲ را کامل کنید |
| خطای `Access denied for user` (1045) | `DB_USER/DB_PASSWORD` اشتباه است — در cPanel → MySQL® Databases → «Change Password» همان کاربر و آپدیت `.env` + `touch tmp/restart.txt` |
| خطای `Unknown database` | نام دیتابیس را کامل با پیشوند حساب بنویسید: `khanomgo_foodshop` نه `foodshop` |
| خطای `Can't connect to local MySQL server` (2002) | `DB_HOST=localhost` بماند؛ اگر MySQL روی سرور جدا است، آدرس را از هاست بگیرید |
| حروف فارسی به‌صورت `????` ذخیره می‌شود | Collation دیتابیس را `utf8mb4_unicode_ci` کنید (phpMyAdmin → Operations) |
| صفحهٔ سفید، خطای ۴۰۴ برای `/assets/…` در کنسول | بیلد با مسیر پایهٔ `/food-shop/` منتشر شده → `--build` بگیرید |
| رفرش مسیرهای عمیق (`/products`) خطای ۴۰۴ می‌دهد | `.htaccess` ساخته نشده — اسکریپت فرانت را دوباره اجرا کنید؛ اگر Apache اجازهٔ Override نمی‌دهد، از پشتیبانی هاست `AllowOverride All` را بخواهید |
| css/js لود می‌شود ولی داده‌ها از سرور نمی‌آیند | `VITE_API_BASE` placeholder است یا `VITE_API_ENABLED=false` → `--build --api-base … --api-enabled` |
| «Node ≥18 پیدا نشد» هنگام `--build` | در cPanel «Setup Node.js App» برنامه بسازید یا بیلد را محلی بگیرید و commit کنید (پیشنهادی) |
| تغییرات دیده نمی‌شود | کش مرورگر — `index.html` بدون کش منتشر می‌شود؛ با Ctrl+F5 بگیرید |
| خطای ۵۰۰ | مالکیت/سطح دسترسی فایل‌ها را در File Manager چک کنید (۶۴۴ برای فایل‌ها) |
| بک‌اند خطای ۵۰۳ می‌دهد (Passenger) | پس از هر تغییر venv/passenger_wsgi.py ری‌استارت لازم است: `touch tmp/restart.txt` یا دکمهٔ Restart در Setup Python App؛ Startup File باید `passenger_wsgi.py` باشد |
| صفحهٔ «It works! Python 3.11.18» به‌جای فروشگاه | Application URL در Setup Python App روی `/` است → ویرایش به `/food-shop` + Restart (بخش «اگر صفحهٔ It works دیدید» در گام ۴) |
| پنل `dj-admin` بدون CSS است | `FORCE_SCRIPT_NAME` و `STATIC_URL` در `.env` هم‌اهنگ با Application URL نیستند → `FORCE_SCRIPT_NAME=/food-shop` و `STATIC_URL=/food-shop/static/` + `touch tmp/restart.txt` |
| «پایتون ≥3.10 پیدا نشد» در اسکریپت بک‌اند | در cPanel → Setup Python App برنامه با Python 3.11 بسازید (Application root = `public_html/food-shop`) و دوباره اجرا کنید؛ یا مسیر بدهید: `--python /opt/alt/python311/bin/python3.11` |
| `api/v1/health` پاسخ نمی‌دهد | `ALLOWED_HOSTS` در `backend/.env` دامنه را ندارد → ویرایش و `touch tmp/restart.txt`؛ لاگ‌ها در `backend/logs/` |
| فرانت به بک‌اند وصل نمی‌شود (CORS) | `CORS_ORIGINS` در `backend/.env` باید دقیقاً دامنهٔ فرانت باشد (با https و بدون اسلش آخر) |

## امنیت و تست‌ها

- `.htaccess` بک‌اند مسیرهای حساس (`shop/`, `config/`, `deploy/`, `logs/`, `tmp/`, `.git`, `.env`) و فایل‌های پیکربندی را از وب می‌بندد؛ `.htaccess` فرانت هدرهای `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` را فعال می‌کند.
- رمز دیتابیس MySQL فقط در `.env` (محافظت‌شده از وب) و `~/.my.cnf` (سطح دسترسی ۶۰۰) نگه‌داری می‌شود — هرگز داخل کد یا ریپو نیست.
- **تست امنیتی بک‌اند** (۶۹ بررسی: تزریق، JWT، IDOR، throttle OTP، دستکاری مالی): `python scripts/test_backend_security.py` — همه سبز.
- **تست ریسپانسیو موبایل** (۶ دستگاه از ۳۲۰px تا تبلت × ۷ صفحهٔ فروشگاه): ۰ سرریز افقی، ۰ خطای کنسول؛ برای بازبینی، در Chrome DevTools → Device Toolbar عرض‌های ۳۲۰/۳۶۰/۳۹۰/۴۱۴/۷۶۸/۱۰۲۴ را روی صفحات اصلی چک کنید.
- پس از اتصال بک‌اند: `ADMIN_PASSWORD` را عوض کنید و `CORS_ORIGINS` فقط دامنهٔ فرانت باشد.


## استقرار یک‌دستوری (فرانت + بک‌اند) — روش پیشنهادی

روی هاست Node نیست، پس فرانت یک‌بار روی ماشین محلی ساخته و در `host-dist/` commit می‌شود (دامنه به‌صورت جانشین `__SITE_HOST__` است)؛ روی هاست فقط:
```bash
cd ~/public_html/food-shop
git pull
bash deploy.sh --domain دامنه-شما.ir
```
`deploy.sh` دامنه را در فرانت جایگزین می‌کند (canonical، sitemap، آدرس API)، فرانت را در `~/public_html` می‌گذارد، بک‌اند را مستقر می‌کند (pip، migrate، seed، static، Passenger) و در پایان سایت و API را **واقعاً** صدا می‌زند. اگر هر کدام ۵xx بدهد، خودش `diagnose.py` و آخرین خطوط لاگ‌ها را چاپ می‌کند.

- فقط بررسی/عیب‌یابی: `bash deploy.sh --domain دامنه-شما.ir --check`
- فقط یکی از دو بخش: `--skip-front` یا `--skip-back`
- ساخت دوبارهٔ `host-dist` بعد از تغییر کد فرانت (ماشین محلی): `bash scripts/build_host.sh` سپس commit/push.

## خطای ۵۰۰ روی بک‌اند — عیب‌یابی گام‌به‌گام

خطای ۵۰۰ یعنی Django بالا آمده ولی هنگام پردازش درخواست استثنا رخ داده؛ علت واقعی در لاگ است، نه در خود صفحهٔ ۵۰۰.

1. **اسکریپت عیب‌یابی** (در ترمینال cPanel، داخل پوشهٔ `backend`، با پایتون venv برنامه؛ هیچ رمزی چاپ نمی‌کند):
   ```bash
   ~/virtualenv/public_html/food-shop/3.11/bin/python deploy/diagnose.py
   ```
   پایتون/بسته‌ها، خواندن `.env`، اتصال و نسخهٔ دیتابیس، مایگریشن‌های معوق و یک درخواست آزمایشی به `/api/v1/health` و `/api/v1/products` را بررسی و **traceback واقعی** را چاپ می‌کند.
2. **لاگ وب**: هر ۵۰۰ با traceback کامل در `backend/logs/django-error.log` ثبت می‌شود (`tail -50 backend/logs/django-error.log`).
3. علت‌های رایج:

| خطا در لاگ | راه‌حل |
| --- | --- |
| `UnicodeEncodeError: 'ascii' codec can't encode` در `load_dotenv`/`os.environ` | (رفع‌شده در کد) زیر Passenger پایتون با locale ASCII است و مقدار فارسی `.env` (مثل `SHOP_NAME`) را نمی‌توانست در محیط بگذارد؛ `git pull && bash deploy.sh --domain ...` |
| `no such table` / `Table 'khanomgo_foodshop.shop_product' doesn't exist` | مایگریشن اجرا نشده: `python manage.py migrate && python manage.py seed_shop` |
| `MariaDB 10.x or later is required` / `MySQL 8.0.11 or later` | نسخهٔ دیتابیس هاست برای Django 5.2 قدیمی است: `pip install "Django>=5.0,<5.1"` (یا از هاست MariaDB جدیدتر بخواهید) |
| `Access denied for user` (1045) / `Unknown database` (1049) | `DB_USER/DB_PASSWORD/DB_NAME` در `.env` را با cPanel → MySQL® Databases چک کنید و کاربر را به دیتابیس با «ALL PRIVILEGES» وصل کنید |
| `Can't connect to MySQL server` (2002) | `DB_HOST=localhost` و `DB_PORT=3306`؛ اگر باز هم نشد `DB_HOST=127.0.0.1` |
| `No module named 'pymysql'` / `RuntimeError: درایور MySQL` | `pip install -r deploy/requirements-cpanel.txt` با همان venv برنامه |
| `Invalid HTTP_HOST header` (۴۰۰، نه ۵۰۰) | دامنه در `ALLOWED_HOSTS` نیست |
| `Specified key was too long` هنگام migrate | دیتابیس را با collation `utf8mb4_unicode_ci` و موتور InnoDB بسازید |

4. پس از هر تغییر `.env` یا کد: `touch tmp/restart.txt`.
5. اگر `.env` ویرایش دستی شد: رمزهایی که کاراکتر `#` یا فاصله دارند را داخل کوتیشن بگذارید (`DB_PASSWORD="..."`) و فایل باید UTF-8 با پایان‌خط Unix باشد.

## سئو و اتصال به ترب (Torob)

**سئو:** هنگام بیلد (`npm run build`) برای هر صفحهٔ قابل‌ایندکس (خانه، فروشگاه، پیگیری و تک‌تک محصولات) یک `index.html` ایستا با عنوان، توضیح، canonical، Open Graph، توییتر، JSON-LD (Product/BreadcrumbList/ItemList) و متن واقعی ساخته می‌شود، به‌علاوهٔ `sitemap.xml` (با تصاویر) و `robots.txt`. صفحات سبد، تسویه، حساب، مدیریت و ورود `noindex` هستند.
روی **دامنهٔ واقعی** بیلد را با آدرس سایت بگیرید تا canonical و sitemap درست باشند:
```bash
VITE_BASE=/ VITE_SITE_URL=https://shop.example.ir npm run build   # از پوشهٔ app
```
سپس `sitemap.xml` را در Google Search Console ثبت کنید.

**ترب:** دو راه آماده است (آدرس‌ها را در پنل فروشندگان ترب ثبت کنید):
1. **API (پیشنهادی):** `https://دامنه-بک‌اند/api/v1/torob/products?page=1` — خروجی `{count, max_pages, products:[…]}` با فیلدهای `title, page_unique, current_price (تومان), old_price, availability (instock/outofstock), category_name, image_link, page_url, short_desc, spec, date_updated`. هم GET و هم POST با `{"page": n}` پاسخ می‌دهد. `SHOP_URL` در `backend/.env` باید دامنهٔ **فرانت** باشد (برای ساخت `page_url`).
2. **خزش صفحات:** هر صفحهٔ محصول بدون نیاز به JS قیمت (`product:price:amount`، تومان)، موجودی، عنوان و تصویر را در متاتگ‌ها و JSON-LD دارد.
قیمت فید و صفحه همیشه یکی است (هر دو قیمت وزن پیش‌فرض را نشان می‌دهند). قالب دقیق فیلدها را در پنل ترب با نمونهٔ خروجی تأیید کنید.
