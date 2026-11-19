#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""عیب‌یابی درگاه پرداخت زیبال روی هاست — هیچ رمز/مرچنت کامل چاپ نمی‌شود.

اجرا (ترمینال cPanel، داخل پوشهٔ backend، با پایتون venv برنامه):
    ~/virtualenv/.../bin/python deploy/diagnose_pay.py khanomgol8.ir
یا از ریشهٔ ریپو:  bash deploy.sh --domain khanomgol8.ir --check-pay

بررسی‌ها: .env و مرچنت، callback، اتصال خروجی به زیبال، درخواست آزمایشی واقعی (بدون کسر پول)،
مایگریشن، آخرین تراکنش‌ها و پیام خطای زیبال، پاسخ API عمومی و آیا فرانت مستقرشده نسخهٔ جدید است.
"""
import glob
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
DOMAIN = (sys.argv[1] if len(sys.argv) > 1 else '').replace('https://', '').replace('http://', '').strip('/')

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
bad, hints = [], []
CODES = {
    100: 'موفق', 102: 'merchant پیدا نشد (کد اشتباه)', 103: 'merchant غیرفعال یا قرارداد درگاه امضا نشده',
    104: 'merchant نامعتبر', 105: 'مبلغ کمتر از ۱٬۰۰۰ ریال', 106: 'callbackUrl نامعتبر: دامنه‌اش با وب‌سایت ثبت‌شده برای درگاه در پنل زیبال یکی نیست',
    113: 'مبلغ از سقف بیشتر است', 115: 'IP سرور هاست در پنل زیبال ثبت نشده (درگاه را روی IP محدود کرده‌اید)',
    140: 'callbackUrl ارسال نشده',
}


def line(ok, msg, extra=''):
    print(('  ✓ ' if ok else '  ✗ ') + msg + (f'  → {extra}' if extra else ''))
    if not ok:
        bad.append(msg)


def hint(t):
    hints.append(t)


def section(t):
    print(f'\n== {t} ==')


def mask(v):
    v = v or ''
    return '(خالی)' if not v else (v if v == 'zibal' else f'{v[:3]}…{v[-2:]} (طول {len(v)})')


def post(url, body, timeout=15):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
                               headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or '{}')
        except Exception:                                                  # noqa: BLE001
            return e.code, {}


def get(url, timeout=15, headers=None):
    r = urllib.request.Request(url, headers=headers or {'User-Agent': UA})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


# ───────────────────────────── تنظیمات
section('۱) تنظیمات (.env)')
try:
    import django
    django.setup()
    from django.conf import settings
except Exception as e:                                                      # noqa: BLE001
    print('  ✗ Django بالا نیامد:', repr(e)); print('    ابتدا python deploy/diagnose.py را اجرا کنید.'); sys.exit(2)

M = (settings.ZIBAL_MERCHANT or '').strip()
line(bool(M), 'ZIBAL_MERCHANT تنظیم شده', mask(M))
if not M:
    hint('در backend/.env خط ZIBAL_MERCHANT=کد-درگاه را بنویسید (بدون فاصله/نقل‌قول) و برنامه را ری‌استارت کنید. تا خالی است پرداخت خاموش است و سفارش مستقیم «موفق» می‌شود.')
elif M != 'zibal' and (M != M.strip() or ' ' in M or '"' in M or "'" in M):
    line(False, 'مرچنت فاصله یا نقل‌قول دارد')
    hint('مقدار ZIBAL_MERCHANT نباید نقل‌قول/فاصله داشته باشد.')
env_path = os.path.join(ROOT, '.env')
if os.path.isfile(env_path):
    txt = open(env_path, encoding='utf-8', errors='replace').read()
    n = len(re.findall(r'^\s*ZIBAL_MERCHANT\s*=', txt, re.M))
    line(n == 1, 'خط ZIBAL_MERCHANT در .env دقیقاً یکی است', f'{n} خط')
    if n > 1:
        hint('ZIBAL_MERCHANT چندبار در .env آمده؛ آخری برنده می‌شود — تکراری‌ها را حذف کنید.')
    if n == 0 and M:
        hint('مقدار از متغیر محیطی Setup Python App می‌آید نه .env؛ مطمئن شوید همان‌جا درست است.')
else:
    line(False, 'فایل backend/.env پیدا نشد', env_path)
cb_cfg = (settings.ZIBAL_CALLBACK_URL or '').strip()
shop = (settings.SHOP_URL or '').strip()
print('  SHOP_URL            =', shop)
print('  ZIBAL_CALLBACK_URL  =', cb_cfg or '(خالی → از Origin/SHOP_URL ساخته می‌شود)')
print('  ALLOWED_HOSTS       =', settings.ALLOWED_HOSTS)
print('  CORS_ORIGINS        =', getattr(settings, 'CORS_ALLOWED_ORIGINS', None) or getattr(settings, 'CORS_ORIGINS', None))
front = cb_cfg.rstrip('/') or (shop.rstrip('/') if 'github.io' not in shop else '') or (f'https://{DOMAIN}' if DOMAIN else '')
line(bool(front), 'دامنهٔ فرانت برای callback مشخص است', front or 'نامشخص')
if cb_cfg and DOMAIN and DOMAIN not in cb_cfg:
    line(False, 'ZIBAL_CALLBACK_URL با دامنهٔ سایت یکی نیست', f'{cb_cfg} ≠ {DOMAIN}')
    hint(f'ZIBAL_CALLBACK_URL=https://{DOMAIN} (دامنهٔ فرانت، نه api.…) — باید دقیقاً همان دامنهٔ ثبت‌شده در پنل زیبال باشد.')
if cb_cfg.startswith('http://') or (front and front.startswith('http://')):
    line(False, 'callback باید https باشد (زیبال فقط https می‌پذیرد)', front)
if 'github.io' in shop and not cb_cfg:
    hint(f'SHOP_URL هنوز GitHub Pages است؛ بهتر است ZIBAL_CALLBACK_URL=https://{DOMAIN or "دامنه"} را هم بگذارید.')

# ───────────────────────────── شبکه
section('۲) اتصال خروجی هاست به زیبال')
host = 'gateway.zibal.ir'
try:
    ip = socket.gethostbyname(host)
    line(True, f'DNS {host}', ip)
except Exception as e:                                                      # noqa: BLE001
    line(False, f'DNS {host} حل نشد', repr(e))
    hint('هاست به اینترنت/DNS دسترسی ندارد؛ از پشتیبانی هاست بخواهید خروج به gateway.zibal.ir:443 را باز کنند.')
    ip = None
if ip:
    try:
        s = socket.create_connection((ip, 443), timeout=8); s.close()
        line(True, 'اتصال TCP به پورت ۴۴۳')
    except Exception as e:                                                  # noqa: BLE001
        line(False, 'اتصال TCP به ۴۴۳ برقرار نشد (فایروال هاست؟)', repr(e))
        hint('فایروال هاست خروجی ۴۴۳ به زیبال را بسته؛ به پشتیبانی هاست بگویید.')
    try:
        t0 = time.time(); c = get('https://gateway.zibal.ir/'); line(True, 'HTTPS به زیبال', f'HTTP {c[0]} در {time.time() - t0:.1f}s')
    except ssl.SSLError as e:
        line(False, 'خطای SSL با زیبال (گواهی/ساعت سرور)', repr(e))
    except Exception as e:                                                  # noqa: BLE001
        line(False, 'HTTPS به زیبال ناموفق', repr(e))
try:
    myip = get('https://api.ipify.org', timeout=8)[1].strip()
    print('  IP خروجی هاست (برای لیست IP پنل زیبال):', myip)
except Exception:                                                           # noqa: BLE001
    print('  IP خروجی تشخیص داده نشد')

# ───────────────────────────── درخواست آزمایشی
section('۳) درخواست آزمایشی واقعی به زیبال (فقط ساخت trackId؛ پولی کسر نمی‌شود)')
cb = (front or 'https://example.com') + '/pay?order=DIAG-TEST'
base = settings.ZIBAL_API_BASE
tests = [('merchant آزمایشی «zibal» (بررسی مسیر شبکه/فرمت)', 'zibal')]
if M and M != 'zibal':
    tests.append(('merchant واقعی شما', M))
for label, mer in tests:
    try:
        st, r = post(base + 'request', {'merchant': mer, 'amount': 10000, 'callbackUrl': cb,
                                        'description': 'diagnose', 'orderId': 'DIAG-TEST'})
    except Exception as e:                                                  # noqa: BLE001
        line(False, label, f'اتصال ناموفق: {e}'); continue
    code = r.get('result')
    ok_ = code == 100 and r.get('trackId')
    line(ok_, label, f'HTTP {st} result={code} ({CODES.get(code, r.get("message", "؟"))}) trackId={r.get("trackId", "-")}')
    if mer != 'zibal' and not ok_:
        if code == 106:
            hint(f'کد ۱۰۶: دامنهٔ callback ({cb.split("/pay")[0]}) با «آدرس وب‌سایت» ثبت‌شده برای این درگاه در panel.zibal.ir فرق دارد. '
                 'همان دامنه (با/بدون www) را در پنل درگاه ثبت کنید یا ZIBAL_CALLBACK_URL را دقیقاً مثل آن بگذارید.')
        elif code in (102, 104):
            hint('کد مرچنت اشتباه است؛ از panel.zibal.ir ← درگاه‌ها ← «کد درگاه (merchant)» را کپی کنید، نه شناسهٔ کاربری.')
        elif code == 103:
            hint('درگاه هنوز تأیید/فعال نشده یا قرارداد امضا نشده است؛ تا آن موقع با ZIBAL_MERCHANT=zibal تست کنید.')
        elif code == 115:
            hint('در پنل زیبال درگاه را به IP محدود کرده‌اید؛ IP خروجی چاپ‌شده بالا را اضافه کنید یا محدودیت IP را بردارید.')
    if mer == 'zibal' and not ok_:
        hint('حتی با merchant آزمایشی هم درخواست جواب نداد → مشکل شبکه/فایروال هاست یا اتصال خروجی (بخش ۲).')

# ───────────────────────────── دیتابیس
section('۴) دیتابیس و تراکنش‌ها')
try:
    from django.db import connection
    from shop.models import Order, Payment
    cols = {c.name for c in connection.introspection.get_table_description(connection.cursor(), Order._meta.db_table)}
    line('pay_status' in cols, 'ستون pay_status در جدول سفارش (migrate اجرا شده)')
    if 'pay_status' not in cols:
        hint('ابتدا: python manage.py migrate')
    rows = list(Payment.objects.order_by('-id')[:8])
    print(f'  تعداد کل تراکنش‌ها: {Payment.objects.count()} | آخرین ۸ مورد:')
    for p in rows:
        print(f'    #{p.id} {p.order.code} state={p.state} result={p.result} {CODES.get(p.result, "")} | {p.message[:90]} | {p.created_at:%Y-%m-%d %H:%M}')
    if not rows:
        line(False, 'هیچ تراکنشی ثبت نشده')
        hint('یعنی /pay/start هرگز اجرا نشده: یا فرانت قدیمی است (بخش ۶)، یا ZIBAL_MERCHANT خالی است، یا درخواست به سرور نرسیده (CORS/۴۰۱).')
    elif all(p.state == 'failed' for p in rows[:3]):
        hint('آخرین تلاش‌ها failed هستند؛ پیام/کد ستون بالا علت دقیق را از زیبال نشان می‌دهد.')
    unpaid = Order.objects.exclude(pay_status='paid').order_by('-id')[:3]
    for o in unpaid:
        print(f'    سفارش {o.code} pay_status={o.pay_status} وضعیت={o.status}')
except Exception as e:                                                      # noqa: BLE001
    line(False, 'خواندن دیتابیس', repr(e))

# ───────────────────────────── API عمومی
section('۵) API عمومی روی دامنه')
if DOMAIN:
    cands = [f'https://api.{DOMAIN}/api/v1', f'https://{DOMAIN}/api/v1']
    for api in cands:
        try:
            st, body = get(api + '/pay/config', headers={'User-Agent': UA, 'Origin': f'https://{DOMAIN}', 'Accept': 'application/json'})
            en = None
            try:
                en = json.loads(body).get('enabled')
            except Exception:                                               # noqa: BLE001
                pass
            line(st == 200 and en is not None, f'GET {api}/pay/config', f'HTTP {st} enabled={en} | {body[:80].strip()!r}')
            if st == 200 and en is False:
                line(False, 'API می‌گوید درگاه خاموش است', 'برنامهٔ پایتون هنوز مرچنت را نمی‌بیند')
                hint('برنامهٔ در حال اجرا مرچنت را ندارد: Setup Python App ← Restart بزنید (یا: touch ~/…/backend/tmp/restart.txt).')
            if st == 200 and en is not None:
                break
        except Exception as e:                                              # noqa: BLE001
            line(False, f'{api}/pay/config', repr(e)[:120])
else:
    print('  (دامنه داده نشد؛ مثال: python deploy/diagnose_pay.py khanomgol8.ir)')

# ───────────────────────────── فرانت
section('۶) نسخهٔ فرانت مستقرشده')
if DOMAIN:
    try:
        st, html = get(f'https://{DOMAIN}/')
        js = re.findall(r'src="(/assets/[^"]+\.js)"', html)
        print('  index →', js[:1])
        found = {'pay/config': False, 'pay/start': False}
        for u in (re.findall(r'(?:src|href)="(/assets/[^"]+\.js)"', html) + re.findall(r'(/assets/[A-Za-z]*Checkout[^"\']*\.js)', html))[:6]:
            try:
                code = get(f'https://{DOMAIN}{u}')[1]
                for k in found:
                    found[k] = found[k] or (k in code)
            except Exception:                                               # noqa: BLE001
                pass
        # صفحهٔ Checkout lazy است؛ از فایل‌های روی دیسک هم نگاه می‌کنیم
        for d in glob.glob(os.path.join(ROOT, '..', '*', 'assets')) + glob.glob(os.path.join(ROOT, '..', 'assets')):
            for fp in glob.glob(os.path.join(d, 'Checkout*.js')) + glob.glob(os.path.join(d, 'index-*.js')):
                try:
                    code = open(fp, encoding='utf-8', errors='replace').read()
                    for k in found:
                        found[k] = found[k] or (k in code)
                except OSError:
                    pass
        line(found['pay/config'] and found['pay/start'], 'فرانت مستقرشده کد پرداخت زیبال را دارد', str(found))
        if not (found['pay/config'] and found['pay/start']):
            hint('فرانت روی هاست قدیمی/کش است: git pull ، سپس bash deploy.sh --domain دامنه و در مرورگر Ctrl+Shift+R (یا حذف کش Cloudflare/مرورگر).')
        st, rb = get(f'https://{DOMAIN}/pay')
        line(st == 200, 'مسیر /pay (صفحهٔ بازگشت از درگاه) در SPA باز می‌شود', f'HTTP {st}')
        if st != 200:
            hint('.htaccess (fallback به index.html) برای مسیرهای SPA کار نمی‌کند؛ deploy.sh را دوباره اجرا کنید.')
    except Exception as e:                                                  # noqa: BLE001
        line(False, 'خواندن فرانت', repr(e)[:120])

# ───────────────────────────── لاگ
section('۷) آخرین خطاهای سرور')
lg = os.path.join(ROOT, 'logs', 'django-error.log')
if os.path.isfile(lg):
    tail = open(lg, encoding='utf-8', errors='replace').read().strip().splitlines()[-12:]
    print('\n'.join('    ' + x[:200] for x in tail) or '    (خالی)')
else:
    print('  (لاگی نیست)')

section('نتیجه')
if not bad:
    print('  ✓ همه‌چیز سالم است. اگر هنوز به درگاه نمی‌رود، کش مرورگر را پاک کنید و خطای قرمز مرحلهٔ پرداخت را بفرستید.')
else:
    print(f'  ✗ {len(bad)} مورد مشکل‌دار')
for h in dict.fromkeys(hints):
    print('  ➜', h)
sys.exit(1 if bad else 0)
