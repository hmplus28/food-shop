#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تست رگرسیون ۵۰۰ هاست: Passenger پایتون را با locale ASCII اجرا می‌کند و .env حاوی فارسی
(مثل SHOP_NAME) نباید باعث UnicodeEncodeError شود.   اجرا: python3 scripts/test_ascii_locale.py"""
import os, subprocess, sys, tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
code = r'''
import os, sys
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
assert sys.getfilesystemencoding().lower() in ("ascii", "ansi_x3.4-1968"), sys.getfilesystemencoding()
import django; django.setup()
from config.wsgi import application
from django.conf import settings
assert settings.SHOP_NAME == "فروشگاه خانم گل", repr(settings.SHOP_NAME)
from io import BytesIO
out = {}
body = b"".join(application({"REQUEST_METHOD": "GET", "PATH_INFO": "/api/v1/health", "SERVER_NAME": "x", "SERVER_PORT": "80",
    "wsgi.url_scheme": "http", "wsgi.input": BytesIO(b""), "HTTP_HOST": "localhost"}, lambda s, h, e=None: out.update(s=s)))
print("STATUS", out["s"])
'''
with tempfile.TemporaryDirectory() as d:
    envf = os.path.join(d, '.env')
    open(envf, 'w', encoding='utf-8').write('SECRET_KEY=t' * 10 + '\nDB_ENGINE=sqlite3\nSHOP_NAME=فروشگاه خانم گل\nALLOWED_HOSTS=*\n')
    e = {'PATH': os.environ.get('PATH', ''), 'HOME': d, 'PYTHONPATH': os.path.abspath(ROOT), 'LC_ALL': 'C', 'LANG': 'C', 'PYTHONUTF8': '0',
         'PYTHONCOERCECLOCALE': '0', 'KHANOMGOL_ENV_FILE': envf}
    script = os.path.join(d, 'probe.py')
    open(script, 'w', encoding='utf-8').write(code)
    r = subprocess.run([sys.executable, '-W', 'ignore', script], cwd=ROOT, env=e, capture_output=True, text=True)
ok = r.returncode == 0 and 'STATUS' in r.stdout
print(('✓ ' if ok else '✗ ') + 'با locale ASCII و .env فارسی، اپ بالا می‌آید و /health پاسخ می‌دهد')
if not ok:
    print(r.stdout[-400:], r.stderr[-800:])
sys.exit(0 if ok else 1)
