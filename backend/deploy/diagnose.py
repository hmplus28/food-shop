#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""عیب‌یابی خطای ۵۰۰ روی هاست — بدون چاپ هیچ رمز یا کلید.

اجرا (در ترمینال cPanel، داخل پوشهٔ backend، با پایتون venv برنامه):
    ~/virtualenv/public_html/food-shop/3.11/bin/python deploy/diagnose.py
یا:  python3 deploy/diagnose.py [دامنه-برای-تست-داخلی]

سپس خروجی را (می‌توانید کامل بفرستید؛ رمزی در آن نیست) بررسی کنید.
"""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

bad = []


def line(ok, msg, extra=''):
    print(('  ✓ ' if ok else '  ✗ ') + msg + (f'  → {extra}' if extra else ''))
    if not ok:
        bad.append(msg)


def section(t):
    print(f'\n== {t} ==')


section('پایتون و بسته‌ها')
print('  python:', sys.version.split()[0], '|', sys.executable)
line(sys.version_info >= (3, 10), 'پایتون ≥ 3.10', str(sys.version_info[:3]))
for mod in ('django', 'rest_framework', 'rest_framework_simplejwt', 'corsheaders', 'dotenv', 'whitenoise'):
    try:
        m = __import__(mod)
        print(f'  ✓ {mod} {getattr(m, "__version__", getattr(m, "VERSION", ""))}')
    except Exception as e:  # noqa: BLE001
        line(False, f'ماژول {mod} نصب نیست', repr(e))

section('فایل .env')
env_path = os.path.join(ROOT, '.env')
line(os.path.isfile(env_path), '.env وجود دارد', env_path)
if os.path.isfile(env_path):
    try:
        raw = open(env_path, encoding='utf-8').read()
        line(True, '.env با UTF-8 خوانده شد')
        keys = [l.split('=', 1)[0] for l in raw.splitlines() if '=' in l and not l.lstrip().startswith('#')]
        dup = sorted({k for k in keys if keys.count(k) > 1})
        line(not dup, 'کلید تکراری در .env ندارد', ', '.join(dup))
        if any('\r' in l for l in raw.splitlines(True)[:1]) or '\r\n' in raw:
            line(False, '.env پایان‌خط ویندوز (CRLF) دارد — مقادیر با \\r خوانده می‌شوند', 'dos2unix .env')
    except UnicodeDecodeError as e:
        line(False, '.env UTF-8 نیست', repr(e))

section('بارگذاری تنظیمات جنگو')
try:
    import django
    django.setup()
    from django.conf import settings
    line(True, 'settings بارگذاری شد')
except Exception:  # noqa: BLE001
    line(False, 'settings بارگذاری نشد')
    traceback.print_exc()
    sys.exit(1)

print('  DEBUG =', settings.DEBUG, '| ALLOWED_HOSTS =', settings.ALLOWED_HOSTS)
print('  FORCE_SCRIPT_NAME =', settings.FORCE_SCRIPT_NAME, '| STATIC_URL =', settings.STATIC_URL)
print('  CORS =', getattr(settings, 'CORS_ALLOWED_ORIGINS', 'ALL'))
d = settings.DATABASES['default']
print('  DB:', d['ENGINE'].split('.')[-1], '| name=', d.get('NAME'), '| user=', d.get('USER'),
      '| host=', d.get('HOST'), '| password set =', bool(d.get('PASSWORD')))
if settings.FORCE_SCRIPT_NAME and not settings.STATIC_URL.startswith(settings.FORCE_SCRIPT_NAME):
    line(False, 'STATIC_URL با FORCE_SCRIPT_NAME هم‌پیشوند نیست')

section('دیتابیس')
try:
    from django.db import connection
    connection.ensure_connection()
    line(True, 'اتصال به دیتابیس برقرار شد')
    if connection.vendor == 'mysql':
        print('  نسخهٔ سرور:', connection.mysql_server_info, '| mariadb =', connection.mysql_is_mariadb)
        try:
            import django as dj
            print('  Django', dj.get_version(), '(نیازمند MySQL≥8.0.11 یا MariaDB≥10.5/10.6 بسته به نسخه)')
            connection.features.minimum_database_version  # noqa: B018
            connection.check_database_version_supported()
            line(True, 'نسخهٔ دیتابیس با این Django سازگار است')
        except Exception as e:  # noqa: BLE001
            line(False, 'نسخهٔ دیتابیس برای این Django قدیمی است',
                 f'{e} — راه‌حل: MariaDB 10.4 → pip install "Django>=5.0,<5.1" ؛ MariaDB 10.5+ → هر 5.x ؛ یا از هاست نسخهٔ جدیدتر بخواهید')
        with connection.cursor() as c:
            c.execute('SELECT @@character_set_database, @@collation_database')
            print('  charset/collation:', c.fetchone())
except Exception:  # noqa: BLE001
    line(False, 'اتصال به دیتابیس ناموفق')
    traceback.print_exc()

section('مایگریشن‌ها و داده')
try:
    from django.db.migrations.executor import MigrationExecutor
    from django.db import connection
    ex = MigrationExecutor(connection)
    pending = ex.migration_plan(ex.loader.graph.leaf_nodes())
    line(not pending, 'همهٔ مایگریشن‌ها اعمال شده‌اند', f'{len(pending)} مایگریشن معوق → python manage.py migrate')
    from shop.models import Product, ShopUser
    print('  محصولات:', Product.objects.count(), '| کاربران:', ShopUser.objects.count(),
          '| مدیر:', ShopUser.objects.filter(role='admin').exists())
except Exception:  # noqa: BLE001
    line(False, 'خواندن جداول ناموفق (احتمالاً migrate اجرا نشده)')
    traceback.print_exc()

section('فایل‌ها')
line(os.path.exists(os.path.join(ROOT, 'passenger_wsgi.py')), 'passenger_wsgi.py وجود دارد')
for p, why in (('staticfiles', 'بدون آن CSS پنل dj-admin نمی‌آید: python manage.py collectstatic'),
               ('tmp', 'فقط روی cPanel لازم است (tmp/restart.txt برای ری‌استارت)')):
    print(('  ✓ ' if os.path.exists(os.path.join(ROOT, p)) else '  ! هشدار: ') + p + ('' if os.path.exists(os.path.join(ROOT, p)) else ' → ' + why))

section('درخواست‌های آزمایشی (همان مسیری که 500 می‌دهد)')
host = sys.argv[1] if len(sys.argv) > 1 else (
    next((h for h in settings.ALLOWED_HOSTS if h not in ('*',) and not h.startswith('.')), 'localhost'))
try:
    from django.test import Client
    cl = Client(raise_request_exception=False, SCRIPT_NAME=settings.FORCE_SCRIPT_NAME or '')
    for path in ('/', '/api/v1/health', '/api/v1/products', '/dj-admin/login/'):
        r = cl.get(path, HTTP_HOST=host, secure=True)
        ok = r.status_code < 500
        line(ok, f'GET {path} → {r.status_code}')
        if r.status_code >= 500 and getattr(r, 'exc_info', None) is None:
            pass
except Exception:  # noqa: BLE001
    line(False, 'اجرای درخواست آزمایشی خطا داد')
    traceback.print_exc()

print('\nنتیجه:', 'همه‌چیز سالم است ✅' if not bad else f'{len(bad)} مشکل پیدا شد ❌')
print('لاگ خطاهای وب: backend/logs/django-error.log')
sys.exit(1 if bad else 0)
