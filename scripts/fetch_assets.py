#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""دانلود تصاویر و لوگو به پوشهٔ app/public/img/ تا سایت کاملاً از خود هاست سرو شود
(با اینترنت ملی یا قطع اینترنت جهانی هم تصاویر بالا بیایند).

اجرا (یک‌بار، روی سیستمی که به z-cdn.chatglm.cn و daynacode.ir دسترسی دارد؛ در صورت نیاز با VPN):
    python3 scripts/fetch_assets.py
سپس:
    bash scripts/build_host.sh && git add app/public/img host-dist && git commit -m "تصاویر محلی" && git push

گزینه‌ها:  --force (دوباره دانلود)   --cdn <آدرس> (برای تست)
نکته: تا وقتی فایلی دانلود نشده، سایت خودکار به منبع اصلی برمی‌گردد (خراب نمی‌شود).
"""
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'app', 'public', 'img')
CDN = 'https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/'
EXTRA = {'dayna-logo.png': 'https://daynacode.ir/assets/dayna-logo.png'}
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'

force = '--force' in sys.argv
if '--cdn' in sys.argv:
    CDN = sys.argv[sys.argv.index('--cdn') + 1].rstrip('/') + '/'


def collect():
    names = set()
    pat = re.compile(r'\b([0-9a-f]{12}\.(?:jpg|jpeg|png|webp|gif))\b')
    for base in ('app/src', 'backend/shop'):
        for dp, _, files in os.walk(os.path.join(ROOT, base)):
            for f in files:
                if f.endswith(('.js', '.vue', '.py', '.css')):
                    try:
                        names.update(pat.findall(open(os.path.join(dp, f), encoding='utf-8').read()))
                    except OSError:
                        pass
    return sorted(names)


def fetch(url, dest):
    last = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'image/*,*/*'})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            if len(data) < 200:
                raise ValueError(f'پاسخ بسیار کوچک ({len(data)} بایت)')
            tmp = dest + '.part'
            open(tmp, 'wb').write(data)
            os.replace(tmp, dest)
            return len(data)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1 + attempt)
    raise RuntimeError(f'{type(last).__name__}: {last}')


os.makedirs(OUT, exist_ok=True)
items = [(n, CDN + n) for n in collect()] + list(EXTRA.items())
ok = skipped = 0
failed = []
consecutive = 0
for name, url in items:
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 200 and not force:
        skipped += 1
        continue
    try:
        n = fetch(url, dest)
        ok += 1
        consecutive = 0
        print(f'  ✓ {name}  ({n // 1024} KB)')
    except Exception as e:  # noqa: BLE001
        failed.append(name)
        consecutive += 1
        print(f'  ✗ {name}  → {e}')
        if consecutive >= 3:
            print('\n⛔ سه خطای پیاپی؛ منبع از این شبکه در دسترس نیست (VPN/اینترنت را بررسی و دوباره اجرا کنید).')
            break
print(f'\nدانلود شد: {ok} | از قبل بود: {skipped} | ناموفق: {len(failed)} | کل: {len(items)}')
if failed:
    print('ناموفق‌ها را با اینترنت/VPN دوباره امتحان کنید (فایل‌های موجود دوباره دانلود نمی‌شوند).')
sys.exit(1 if failed else 0)
