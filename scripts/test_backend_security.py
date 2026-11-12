#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تست امنیتی سنگین بک‌اند فروشگاه خانم گل — فقط کتابخانهٔ استاندارد (+PyJWT در صورت وجود)

پیش‌نیازها:
  • سرور Django روشن باشد:  python3 backend/manage.py runserver
  • بهتر است پیش از اجرا سرور ری‌استارت شود تا شمارنده‌های throttle صفر باشند
    (اسکریپت خودش در انتها throttle را عمداً منفجر می‌کند!)

اجرا:
  python3 scripts/test_backend_security.py [آدرس-پایه]
  python3 scripts/test_backend_security.py http://127.0.0.1:8787/api/v1

پوشش:
  A) هدرهای امنیتی و DEBUG        B) تزریق SQL/XSS/ورودی مخرب
  C) احراز هویت، JWT و IDOR       D) امنیت کد یکبار مصرف
  E) منطق مالی (دستکاری قیمت/کوپن)  F) افشای داده
  G) محدودسازی نرخ (Brute-force) — انتهای تست
"""
import base64
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else
        'http://127.0.0.1:8787/api/v1').rstrip('/')
SERVER_ROOT = BASE.split('/api/v1')[0]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FREE_SHIP = 1_500_000

PASS, FAIL, NOTES = [], [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append((name, detail))
    print(('  ✓ ' if cond else '  ✗ ') + name + ('' if cond else f'  → {detail}'))
    return bool(cond)


def note(msg):
    NOTES.append(msg)
    print(f'  ℹ {msg}')


def req_abs(method, url, raw=True):
    """درخواست به URL مطلق (برای ریشهٔ سرور و dj-admin بیرون از BASE)"""
    r = urllib.request.Request(url, method=method)
    r.add_header('Accept', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return resp.status, dict(resp.headers), resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode('utf-8', 'replace')
    except Exception as e:
        return 0, {}, f'{type(e).__name__}: {e}'


def req(method, path, body=None, token=None, headers=None, raw=False, ctype='application/json'):
    r = urllib.request.Request(BASE + path, method=method)
    r.add_header('Accept', 'application/json')
    if body is not None:
        r.add_header('Content-Type', ctype)
        r.data = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
    if token:
        r.add_header('Authorization', token if ' ' in token else 'Bearer ' + token)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            data = resp.read().decode('utf-8', 'replace')
            return resp.status, dict(resp.headers), (data if raw else (json.loads(data) if data else None))
    except urllib.error.HTTPError as e:
        data = e.read().decode('utf-8', 'replace')
        try:
            return e.code, dict(e.headers), (data if raw else json.loads(data))
        except json.JSONDecodeError:
            return e.code, dict(e.headers), {'raw': data}
    except Exception as e:
        return 0, {}, {'exc': f'{type(e).__name__}: {e}'}


def js_round(x):
    return math.floor(x + 0.5)


def unit_price(p, w):
    base = js_round(p['price'] * w / 1000)
    if p.get('disc'):
        base = js_round(base * (100 - p['disc']) / 100 / 1000) * 1000
    return base


# شماره‌های یکتا در هر اجرا
sfx = f'{int(time.time()) % 10**7:07d}'
PH = '0912' + sfx[:7]          # کاربر اصلی تست
PH2 = '0913' + sfx[:7]         # کاربر دوم (IDOR)
PHX = '0935' + sfx[:7]         # OTP
PW = 'sec-' + sfx[-4:] + 'Aa'

print(f'تست امنیتی سنگین بک‌اند خانم گل روی {BASE}')
print('=' * 70)

# ───────────────────────── A) هدرها و DEBUG ─────────────────────────
print('\nA) هدرهای امنیتی و وضعیت DEBUG')
st, hd, _ = req('GET', '/health')
check('A1: X-Frame-Options: DENY', hd.get('X-Frame-Options', '').lower() == 'deny', hd.get('X-Frame-Options'))
check('A2: X-Content-Type-Options: nosniff', hd.get('X-Content-Type-Options', '').lower() == 'nosniff',
      hd.get('X-Content-Type-Options'))
check('A3: Referrer-Policy: same-origin', hd.get('Referrer-Policy', '').lower() == 'same-origin',
      hd.get('Referrer-Policy'))
check('A4: Content-Type پاسخ API: application/json',
      'application/json' in hd.get('Content-Type', ''), hd.get('Content-Type'))
st, hd, body = req('GET', '/definitely-not-exists', raw=True)
check('A5: مسیر ناموجود → ۴۰۴', st == 404, st)
leak = ('Traceback' in body) or ('SECRET' in body) or ('django.db' in body) or ('settings.py' in body)
check('A6: صفحهٔ خطا ردیابی کد/راز افشا نمی‌کند', st == 404 and not leak, body[:120])
st, hd, body = req_abs('GET', SERVER_ROOT + '/')
check('A7: ریشهٔ سرور: JSON معرفی API', st == 200 and 'khanom-gol-api' in body, st)
st, hd, body = req_abs('GET', SERVER_ROOT + '/dj-admin/')
check('A8: پنل ادمین جنگو فقط صفحهٔ ورود', st in (200, 302) and ('csrfmiddlewaretoken' in body or st == 302), st)

# ───────────────────── B) تزریق و ورودی مخرب ─────────────────────
print('\nB) تزریق SQL، XSS و ورودی‌های مخرب')
for i, evil in enumerate(["' OR 1=1 --", "0912'; DROP TABLE shop_shopuser;--", "0912' UNION SELECT password FROM shop_shopuser--"]):
    st, _, r = req('POST', '/auth/login', {'phone': evil, 'password': 'x'})
    check(f'B{i+1}: SQLi در ورود «{evil[:24]}…» → بدون ۵۰۰ و بدون نفوذ',
          st in (200, 400) and (st == 400 or r.get('ok') is False), f'{st} {r}')
st, _, r = req('POST', '/orders', {
    'items': [{'pid': 1, 'w': 500, 'qty': 1}],
    'coupon': "' OR 1=1 --", 'shipType': 'post',
    'addr': {'name': 'تست تزریق', 'phone': PH, 'city': 'تهران', 'addr': 'خیابان تست کامل پستی ۱۲۳'}})
check('B4: SQLi در کد تخفیف → رد با پیام فارسی، بدون ۵۰۰',
      st in (200, 400) and 'کد تخفیف نامعتبر است' in (r.get('msg') or ''), f'{st} {r}')
st, _, r = req('POST', '/orders', {
    'items': [{'pid': 1, 'w': 500, 'qty': 1}], 'shipType': 'post',
    'addr': {'name': 'تست', 'phone': "0912';--", 'city': 'تهران', 'addr': 'خیابان تست کامل پستی ۱۲۳'}})
check('B5: SQLi در شمارهٔ گیرنده → ۴۰۰', st == 400 and r.get('ok') is False, f'{st} {r}')

XSS_NAME = '<script>alert(1)</script>پسته'
XSS_DESC = '<img src=x onerror=alert(2)>'
# برای ساخت محصول، توکن مدیر لازم است
st, _, adm = req('POST', '/admin/login', {'username': 'admin', 'password': 'admin1234'})
ADMIN = adm.get('token')
check('B6: ورود مدیر (کنترل مثبت)', st == 200 and adm.get('ok') and ADMIN, f'{st} {adm}')
st, _, r = req('POST', '/products', {'name': XSS_NAME, 'cat': 'ajil', 'price': 500000, 'weights': [500],
                                     'desc': XSS_DESC}, token=ADMIN)
XID = r.get('product', {}).get('id') if isinstance(r.get('product'), dict) else None
check('B7: محصول XSS-دار ساخته شد (ذخیرهٔ داده خام مجاز در JSON API)', st == 200 and XID, f'{st} {r}')
st, hd, r = req('GET', f'/products/{XID}')
check('B8: خروجی XSS: Content-Type همچنان JSON (مرورگر اجرا نمی‌کند)',
      'application/json' in hd.get('Content-Type', '') and r.get('name') == XSS_NAME, hd.get('Content-Type'))
check('B9: XSS در desc دست‌نخورده به‌عنوان داده برمی‌گردد (فیلتر فرانتِ Vue مسئول نمایش امن است)',
      r.get('desc') == XSS_DESC, r.get('desc'))
req('DELETE', f'/products/{XID}', token=ADMIN)

st, _, r = req('POST', '/products', {'name': 'نام\u0000با NUL', 'cat': 'ajil', 'price': 100000, 'weights': [500]},
               token=ADMIN)
check('B10: کاراکتر NUL در نام محصول → بدون ۵۰۰', st in (200, 400), f'{st} {r}')
if st == 200 and isinstance(r.get('product'), dict):
    req('DELETE', f'/products/{r["product"]["id"]}', token=ADMIN)
st, _, r = req('POST', '/orders', {
    'items': [{'pid': 1, 'w': 500, 'qty': 1}], 'shipType': 'post', 'note': 'a' * 2000,
    'addr': {'name': 'تست حجم', 'phone': PH, 'city': 'تهران', 'addr': 'خیابان تست کامل پستی ۱۲۳'}})
check('B11: توضیح بیش از حد مجاز (۲۰۰۰ کاراکتر) → ۴۰۰', st == 400, f'{st} {r}')
st, _, r = req('POST', '/orders', {
    'items': [{'pid': i % 28 + 1, 'w': 500, 'qty': 1} for i in range(31)], 'shipType': 'post',
    'addr': {'name': 'تست سیل', 'phone': PH, 'city': 'تهران', 'addr': 'خیابان تست کامل پستی ۱۲۳'}})
check('B12: بیش از ۳۰ ردیف سبد → ۴۰۰', st == 400, f'{st} {r}')
st, _, r = req('POST', '/orders', {
    'items': [{'pid': 1, 'w': 500, 'qty': 21}], 'shipType': 'post',
    'addr': {'name': 'تست تعداد', 'phone': PH, 'city': 'تهران', 'addr': 'خیابان تست کامل پستی ۱۲۳'}})
check('B13: تعداد ۲۱ (بیش از سقف) → ۴۰۰', st == 400, f'{st} {r}')
st, _, r = req('POST', '/orders', {
    'items': [{'pid': 1, 'w': 500, 'qty': -3}], 'shipType': 'post',
    'addr': {'name': 'تست منفی', 'phone': PH, 'city': 'تهران', 'addr': 'خیابان تست کامل پستی ۱۲۳'}})
check('B14: تعداد منفی → ۴۰۰', st == 400, f'{st} {r}')
st, _, r = req('POST', '/orders', 'not-a-json-object', ctype='text/plain')
check('B15: بدنهٔ متنی غیر JSON → ۴۰۰/۴۱۵ بدون ۵۰۰', st in (400, 415), f'{st} {r}')
st, _, r = req('GET', '/api/v1/products/../../../../../../etc/passwd'.replace('/api/v1', ''))
check('B16: Path traversal روی مسیر API → ۴۰۴', st == 404, st)
st, _, body = req('GET', '/..%2f..%2fmanage.py', raw=True)
check('B17: Path traversal کدگذاری‌شده → بدون افشای سورس', st in (301, 302, 404) or 'SETTINGS' not in body, st)

# ───────────────────── C) احراز هویت، JWT و IDOR ─────────────────────
print('\nC) توکن، JWT و دسترسی افقی/عمودی')
st, _, r = req('GET', '/auth/me', token='garbage.token.here')
check('C1: توکن آشغال → ۴۰۱', st == 401, st)
st, _, r = req('GET', '/auth/me', token='Bearer')
check('C2: هدر Bearer خالی → ۴۰۱', st == 401, st)
st, _, r = req('GET', '/auth/me', token='Basic YWRtaW46YWRtaW4=')     # admin:admin در Basic
check('C3: Basic auth پذیرفته نمی‌شود → ۴۰۱', st == 401, st)
st, _, r = req('GET', '/auth/me', token='bearer abc.def.ghi')         # بیر سراغ سروِر درست ولی امضای آشغال
check('C4: توکن امضای آشغال → ۴۰۱', st == 401, st)

# ثبت‌نام کاربر عادی + تلاش برای ارتقای نقش (mass assignment)
st, _, r = req('POST', '/auth/register', {'name': 'کاربر امنیتی', 'phone': PH, 'password': PW,
                                          'role': 'admin', 'is_staff': True, 'is_superuser': True})
check('C5: ثبت‌نام با فیلدهای نقش‌محور پذیرفته شد ولی نقش‌ها نادیده گرفته می‌شوند',
      st == 200 and r.get('ok') and set((r.get('user') or {}).keys()) == {'name', 'phone'}, f'{st} {r}')
USER = r.get('token')
st, _, r = req('GET', '/admin/stats', token=USER)
check('C6: کاربر عادی با توکنش → /admin/stats ممنوع (۴۰۳)', st == 403, st)
for ep, method, body in [
    ('/orders', 'GET', None), ('/admin/sms', 'GET', None), ('/admin/sms/test', 'POST', {'to': PH}),
    ('/products', 'POST', {'name': 'x', 'cat': 'ajil', 'price': 1000, 'weights': [500]}),
    ('/products/1', 'DELETE', None),
]:
    st, _, r = req(method, ep, body, token=USER)
    check(f'C7: کاربر عادی → {method} {ep} ممنوع', st in (401, 403), st)
st, _, r = req('PATCH', '/orders/KG-00000', {'status': 3}, token=USER)
check('C8: کاربر عادی → PATCH وضعیت ممنوع', st in (401, 403), st)

for ep in ['/orders', '/admin/stats', '/admin/sms']:
    st, _, r = req('GET', ep)
    check(f'C9: بدون توکن → {ep} ممنوع', st in (401, 403), st)
st, _, r = req('GET', f'/auth/me?token={USER}')
check('C10: توکن در query-string کار نمی‌کند → ۴۰۱', st == 401, st)

# حملات دستی JWT — نیاز به SECRET_KEY و PyJWT
try:
    import jwt as pyjwt
    secret = ''
    envf = os.path.join(ROOT, 'backend', '.env')
    if os.path.exists(envf):
        for line in open(envf, encoding='utf-8'):
            if line.strip().startswith('SECRET_KEY='):
                secret = line.split('=', 1)[1].strip()
    if secret and USER:
        p = pyjwt.decode(USER, secret, algorithms=['HS256'], options={'verify_exp': False})
        uid = p.get('uid')
        now = int(time.time())
        alg_none = pyjwt.encode({'uid': uid, 'exp': now + 3600}, None, algorithm='none')
        st, _, r = req('GET', '/auth/me', token=alg_none)
        check('C11: حملهٔ JWT alg=none → ۴۰۱', st == 401, st)
        expired = pyjwt.encode({'uid': uid, 'exp': now - 3600}, secret, algorithm='HS256')
        st, _, r = req('GET', '/auth/me', token=expired)
        check('C12: توکن منقضی → ۴۰۱', st == 401, st)
        no_uid = pyjwt.encode({'exp': now + 3600}, secret, algorithm='HS256')
        st, _, r = req('GET', '/auth/me', token=no_uid)
        check('C13: توکن بدون uid → ۴۰۱', st == 401, st)
        ghost = pyjwt.encode({'uid': 9999999, 'exp': now + 3600}, secret, algorithm='HS256')
        st, _, r = req('GET', '/auth/me', token=ghost)
        check('C14: توکن کاربر ناموجود → ۴۰۱', st == 401, st)
        uid_admin = None
        st, _, adm2 = req('POST', '/admin/login', {'username': 'admin', 'password': 'admin1234'})
        if st == 200 and adm2.get('token'):
            pp = pyjwt.decode(adm2['token'], secret, algorithms=['HS256'], options={'verify_exp': False})
            uid_admin = pp.get('uid')
            forged = pyjwt.encode({'uid': uid_admin, 'exp': now + 3600, 'token_type': 'access'},
                                  secret + 'x', algorithm='HS256')
            st, _, r = req('GET', '/admin/stats', token=forged)
            check('C15: جعل توکن مدیر با راز اشتباه → ۴۰۱', st == 401, st)
        st, _, r = req('GET', '/admin/stats', token=adm2.get('refresh'))
        check('C16: refresh token به‌جای access → ۴۰۱', st == 401, st)
        note('نکتهٔ طراحی: هرکس SECRET_KEY را بداند می‌تواند توکن معتبر بسازد — راز فقط در backend/.env سرور می‌ماند و در گیت کامیت نمی‌شود.')
    else:
        note('PyJWT یا SECRET_KEY در دسترس نبود — بخش حملات دستی JWT رد شد (C11..C17).')
except ImportError:
    note('PyJWT نصب نیست — بخش حملات دستی JWT رد شد (C11..C17).')

# ثبت‌نام/ورود — اعتبارسنجی
st, _, r = req('POST', '/auth/register', {'name': 'ab', 'phone': '09120000001', 'password': PW})
check('C18: نام خیلی کوتاه → ۴۰۰', st == 400, f'{st} {r}')
st, _, r = req('POST', '/auth/register', {'name': 'کاربر ضعیف', 'phone': '09120000001', 'password': '123'})
check('C19: رمز خیلی کوتاه → ۴۰۰', st == 400, f'{st} {r}')
st, _, r = req('POST', '/auth/register', {'name': 'کاربر فارسی', 'phone': '۰۹۱۴' + sfx[:7], 'password': PW})
check('C20: شماره با ارقام فارسی → نرمال‌سازی و ثبت موفق', st == 200 and r.get('ok')
      and r.get('user', {}).get('phone') == '0914' + sfx[:7], f'{st} {r}')
st, _, r = req('POST', '/auth/register', {'name': 'کاربر فارسی ۹', 'phone': '۰۹۳۹' + sfx[:7], 'password': PW})
check('C21: رقم «۹» فارسی (U+06F9) هم نرمال می‌شود', st == 200 and r.get('ok')
      and r.get('user', {}).get('phone') == '0939' + sfx[:7], f'{st} {r}')

# ───────────────────── D) امنیت OTP ─────────────────────
print('\nD) امنیت کد یکبار مصرف')
st, _, rA = req('POST', '/auth/otp/request', {'phone': PHX})
code_x = (rA.get('dev') or {}).get('code') if isinstance(rA.get('dev'), dict) else None
check('D1: درخواست کد برای شمارهٔ X', rA.get('ok') is True and bool(code_x), rA)
st, _, r = req('POST', '/auth/otp/verify', {'phone': PH2, 'code': code_x or ''})
check('D2: کدِ شمارهٔ X با شمارهٔ دیگر (دومین) → رد', r.get('ok') is False, r)
st, _, r = req('POST', '/auth/otp/verify', {'phone': PHX, 'code': code_x or ''})
check('D3: تأیید درست کد → توکن', r.get('ok') is True and r.get('token'), r)
st, _, r = req('POST', '/auth/otp/verify', {'phone': PHX, 'code': code_x or ''})
check('D4: استفادهٔ دوباره از همان کد (replay) → رد', r.get('ok') is False, r)
st, _, r = req('POST', '/auth/otp/verify', {'phone': PHX, 'code': '٤٤٤٤٤٤'})
check('D5: کد با ارقام فارسی/نامعتبر → رد بدون ۵۰۰', st in (200, 400) and r.get('ok') is False, f'{st} {r}')

# ───────────────────── E) منطق مالی ─────────────────────
print('\nE) دستکاری قیمت، کد تخفیف و سقف‌ها')
st, _, prods = req('GET', '/products')
pmap = {p['id']: p for p in prods}
pid1 = next(p['id'] for p in prods if 500 in p['weights'])
pid2 = next(p['id'] for p in prods if 1000 in p['weights'])
w1, q1, w2, q2 = 500, 2, 1000, 1
sub = unit_price(pmap[pid1], w1) * q1 + unit_price(pmap[pid2], w2) * q2
ship = 0 if sub >= FREE_SHIP else 59000
order = {
    'items': [{'pid': pid1, 'w': w1, 'qty': q1}, {'pid': pid2, 'w': w2, 'qty': q2}],
    'shipType': 'post', 'client_code': 'AS-SEC' + sfx[-5:],
    'addr': {'name': 'گیرندهٔ امنیتی', 'phone': PH, 'prov': 'تهران',
             'city': 'تهران', 'addr': 'خیابان امنیت کامل پستی ۱۲۳'},
}
st, _, r = req('POST', '/orders', {**order, 'total': 0, 'sub': 1, 'off': 999999999,
                                   'unit_price': 1, 'status': 3, 'ship_cost': 0})
total_exp = max(0, sub + ship)
check('E1: تزریق فیلدهای مالی در سفارش → نادیده و بازمحاسبهٔ کامل',
      r.get('total') == total_exp and r.get('sub') == sub and r.get('status') == 0,
      f'got total={r.get("total")} want {total_exp}')
CODE = r.get('code')
# WELCOME10 باید با «شمارهٔ تازهٔ بدون سفارش» و مبلغ ≥ ۵۰۰هزار تومان تست شود
PHW = '0937' + sfx[:7]
cheap = pmap.get(17) or min(pmap.values(), key=lambda p: p['price'])
w_wel = 2000 if 2000 in cheap['weights'] else max(cheap['weights'])
sub_wel = unit_price(cheap, w_wel) * 2   # دو ردیف‌برابر تا حتی با تخفیف محصول از حداقل ۵۰۰هزار عبور کند
st, _, r = req('POST', '/orders', {
    'items': [{'pid': cheap['id'], 'w': w_wel, 'qty': 2}], 'coupon': 'WELCOME10', 'shipType': 'post',
    'addr': {'name': 'خرید اول', 'phone': PHW, 'city': 'تهران', 'addr': 'خیابان تخفیف اول کامل ۱۲۳'}})
check('E2: WELCOME10 خرید اول (مبلغ کافی) → تخفیف ۱۰٪ درست',
      r.get('ok') is not False and r.get('off') == js_round(sub_wel * 10 / 100), f'{st} {r}')
st, _, r = req('POST', '/orders', {
    'items': [{'pid': cheap['id'], 'w': w_wel, 'qty': 2}], 'coupon': 'WELCOME10', 'shipType': 'post',
    'addr': {'name': 'خرید دوم', 'phone': PHW, 'city': 'تهران', 'addr': 'خیابان تخفیف اول کامل ۱۲۳'}})
check('E3: WELCOME10 در خرید دوم همان شماره → رد', r.get('ok') is False
      and 'اولین' in (r.get('msg') or ''), r)
st, _, r = req('POST', '/orders', {
    'items': [{'pid': cheap['id'], 'w': 250, 'qty': 1}], 'coupon': 'CASH50', 'shipType': 'post',
    'addr': {'name': 'تست حداقل مبلغ', 'phone': PH, 'city': 'تهران', 'addr': 'خیابان حداقل مبلغ کامل ۱۲۳'}})
check('E4: CASH50 زیر حداقل مبلغ (۳۰۰هزار) → رد با پیام', r.get('ok') is False
      and 'کافی نیست' in (r.get('msg') or ''), r)
st, _, r = req('POST', '/orders', {**order, 'coupon': 'SHIP0'})
check('E5: SHIP0 → ارسال رایگان', r.get('ok') is not False and r.get('ship_cost') == 0, r)
st, _, r = req('GET', f'/orders/{CODE}')
leaky = any(k in r for k in ('addr', 'a_name', 'a_phone', 'note', 'client_code'))
check('F6: پیگیری عمومی فقط فیلدهای حداقلی را می‌دهد (بدون آدرس/نام/موبایل)',
      st == 200 and not leaky, r.keys() if isinstance(r, dict) else r)

# ───────────────────── F) افشای داده و IDOR ─────────────────────
print('\nF) افشای داده و دسترسی افقی')
st, _, rU = req('POST', '/auth/register', {'name': 'کاربر دوم', 'phone': PH2, 'password': PW})
USER2 = rU.get('token')
st, _, r = req('GET', '/orders/mine', token=USER2)
check('F1: /orders/mine کاربر دوم بدون سفارش → خالی', r.get('count') == 0 and r.get('results') == [], r)
st, _, r = req('GET', '/orders/mine', token=USER)
check('F2: /orders/mine کاربر اول فقط سفارش‌های خودش', r.get('count', 0) >= 1
      and all(x['addr']['phone'] == PH for x in r.get('results', [])), r.get('count'))
st, _, pub = req('GET', '/products?all=1')
check('F3: ?all=1 بدون توکن مدیر → محصولات پنهان هم داده نمی‌شود',
      isinstance(pub, list) and all(p.get('hide') is not True for p in pub), len(pub))
st, _, r = req('GET', '/orders?q=%27%20OR%201%3D1--')
check('F4: q تزریقی بدون توکن مدیر → ممنوع', st in (401, 403), st)

# ───────────────────── G) محدودسازی نرخ (Brute-force) ─────────────────────
print('\nG) محدودسازی نرخ — انتهای تست (شمارنده‌ها را مصرف می‌کند)')
seen429 = 0
for i in range(24):
    st, _, _r = req('POST', '/auth/otp/request', {'phone': f'0936{sfx[:2]}{i:02d}{sfx[4:]}'[:11].ljust(11, '0')})
    if st == 429:
        seen429 += 1
check('G1: انفجار درخواست OTP → پس از سقف، ۴۲۹ می‌دهد (سقف ۲۰/ساعت)', seen429 >= 1, f'429s={seen429}')

seen429 = 0
for i in range(55):
    st, _, _r = req('POST', '/auth/login', {'phone': PH, 'password': 'wrong-guess-' + str(i)})
    if st == 429:
        seen429 += 1
check('G2: انفجار ورود (brute-force رمز) → ۴۲۹ می‌دهد (سقف ۶۰/ساعت)', seen429 >= 1, f'429s={seen429}')

seen429 = 0
for i in range(330):
    st, _, _r = req('GET', '/health')
    if st == 429:
        seen429 += 1
        break
check('G3: انفجار درخواست عمومی → ۴۲۹ می‌دهد (سقف ۳۰۰/ساعت)', seen429 >= 1, f'429s={seen429}')

# ---------------- جمع‌بندی و گزارش ----------------
print('=' * 70)
print(f'نتیجهٔ امنیتی: {len(PASS)} سبز، {len(FAIL)} قرمز از {len(PASS) + len(FAIL)} بررسی')
if FAIL:
    print('بررسی‌های ناموفق:')
    for name, d in FAIL:
        print(f'  ✗ {name} → {d}')
print('\nتوصیه‌های استقرار (خارج از تست):')
print('  • در تولید CORS_ORIGINS را به دامنهٔ فرانت محدود کنید (الان * است چون .env پیش‌فرض توسعه است).')
print('  • پس از نصب SSL: SECURE_SSL_REDIRECT=true و SECURE_HSTS_SECONDS=31536000 در backend/.env')
print('  • ADMIN_PASSWORD پیش‌فرض را عوض کنید؛ روی هاست، فایل .env و db.sqlite3 با .htaccess مسدود می‌شوند.')
print('  • CORS * برای API توکن‌محور (بدون کوکی) خطر CSRF ندارد ولی اصولاً محدودش کنید.')
sys.exit(1 if FAIL else 0)
