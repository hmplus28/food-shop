#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تست انتها-به-انتهای بک‌اند فروشگاه خانم گل — فقط کتابخانهٔ استاندارد

پیش‌نیاز: سرور Django روشن باشد (python3 backend/manage.py runserver)
اجرا:  python3 scripts/test_backend_api.py  [آدرس-پایه]
مثال:  python3 scripts/test_backend_api.py http://127.0.0.1:8787/api/v1

خروجی: فهرست بررسی‌ها با ✓/✗، جمع نهایی و کد خروج (۰ = همه سبز)
"""
import json
import math
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else
        'http://127.0.0.1:8787/api/v1').rstrip('/')
FREE_SHIP = 1_500_000
SHIP = {'peyk': 89_000, 'post': 59_000, 'tipax': 99_000}

PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append((name, detail))
    print(('  ✓ ' if cond else '  ✗ ') + name + ('' if cond else f'  → {detail}'))
    return cond


ORDER_TOK = None     # توکن کاربر تست؛ ثبت سفارش فقط با حساب ممکن است


def req(method, path, body=None, token=None, raw=False, anon=False):
    if token is None and not anon and method == 'POST' and path == '/orders':
        token = ORDER_TOK
    r = urllib.request.Request(BASE + path, method=method)
    r.add_header('Accept', 'application/json')
    if body is not None:
        r.add_header('Content-Type', 'application/json')
        r.data = json.dumps(body).encode('utf-8')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            data = resp.read().decode('utf-8', 'replace')
            return resp.status, (data if raw else (json.loads(data) if data else None))
    except urllib.error.HTTPError as e:
        data = e.read().decode('utf-8', 'replace')
        try:
            return e.code, (data if raw else json.loads(data))
        except json.JSONDecodeError:
            return e.code, {'raw': data}
    except Exception as e:
        return 0, {'exc': f'{type(e).__name__}: {e}'}


def js_round(x):
    return math.floor(x + 0.5)


def unit_price(p, w):
    base = js_round(p['price'] * w / 1000)
    if p.get('disc'):
        base = js_round(base * (100 - p['disc']) / 100 / 1000) * 1000
    return base


# شماره‌های یکتا در هر اجرا تا تداخلی با دادهٔ قبلی نباشد
suffix = f'{int(time.time()) % 10**7:07d}'
PH_USER = '0912' + suffix[:7]
PH_OTP_A = '0913' + suffix[:7]
PH_OTP_B = '0935' + suffix[:7]
CLIENT_CODE = 'AS-T' + suffix[-5:]

print(f'شروع تست بک‌اند خانم گل روی {BASE}')
print('=' * 64)

# ---------------- ۱) سلامت ----------------
st, h = req('GET', '/health')
check('health: کد ۲۰۰ و ok=true', st == 200 and h.get('ok') is True, f'{st} {h}')
check('health: نام سرویس و وضعیت پیامک', h.get('name') == 'khanom-gol-api'
      and isinstance(h.get('sms'), dict) and 'provider' in h['sms'], h.get('sms'))

# ---------------- ۲) محصولات ----------------
st, prods = req('GET', '/products')
check('products: کد ۲۰۰ و آرایه', st == 200 and isinstance(prods, list), st)
check('products: حداقل ۲۸ محصول', isinstance(prods, list) and len(prods) >= 28,
      len(prods) if isinstance(prods, list) else prods)
p0 = prods[0] if prods else {}
check('products: ساختار فیلدها (id/name/price/weights)',
      all(k in p0 for k in ('id', 'name', 'price', 'weights')), p0)
pmap = {p['id']: p for p in prods}
pid1 = next((p['id'] for p in prods if 500 in p['weights']), p0['id'])
pid2 = next((p['id'] for p in prods if 1000 in p['weights'] and p['id'] != pid1), pid1)
st, pd = req('GET', f'/products/{pid1}')
check('products/{id}: جزئیات درست', st == 200 and pd.get('id') == pid1, st)

# ---------------- ۲-ب) فید ترب ----------------
st, tb = req('GET', '/torob/products?page=1')
check('torob: کد ۲۰۰ و ساختار count/max_pages/products',
      st == 200 and isinstance(tb, dict) and all(k in tb for k in ('count', 'max_pages', 'products')), st)
tp = tb.get('products', []) if isinstance(tb, dict) else []
check('torob: تعداد = محصولات نمایان', len(tp) == len(prods) and tb.get('count') == len(prods), (len(tp), len(prods)))
need = ('title', 'page_unique', 'current_price', 'availability', 'category_name', 'image_link', 'page_url')
check('torob: فیلدهای ضروری هر محصول', all(all(k in x for k in need) for x in tp))
check('torob: قیمت فید = قیمت وزن پیش‌فرض صفحهٔ محصول (وزن دوم)',
      all(x['current_price'] == unit_price(pmap[int(x['page_unique'])],
          pmap[int(x['page_unique'])]['weights'][min(1, len(pmap[int(x['page_unique'])]['weights']) - 1)]) for x in tp))
check('torob: availability فقط instock/outofstock', all(x['availability'] in ('instock', 'outofstock') for x in tp))
check('torob: آدرس صفحه https و شناسهٔ یکتا',
      all(x['page_url'].startswith('http') and '/product/' in x['page_url'] for x in tp)
      and len({x['page_unique'] for x in tp}) == len(tp))
st, tb2 = req('POST', '/torob/products', {'page': 2})
check('torob: صفحهٔ خارج از محدوده → لیست خالی (POST)', st == 200 and tb2.get('products') == [], st)


# ---------------- ۳) ثبت‌نام و ورود با رمز ----------------
PASSW = 't3st-' + suffix[-4:]
st, r = req('POST', '/auth/register', {'name': 'کاربر تستی', 'phone': PH_USER, 'password': PASSW})
check('register: ok=true و توکن', st == 200 and r.get('ok') and r.get('token'), f'{st} {r}')
check('register: کاربر با شمارهٔ نرمال', r.get('user', {}).get('phone') == PH_USER, r.get('user'))
USER_TOKEN = r.get('token')
ORDER_TOK = USER_TOKEN
st, r = req('POST', '/auth/register', {'name': 'کاربر تستی', 'phone': PH_USER, 'password': PASSW})
check('register تکراری: ok=false با پیام فارسی', st == 200 and r.get('ok') is False and r.get('msg'), r)
st, r = req('POST', '/auth/register', {'name': 'کاربر تستی', 'phone': '12345', 'password': PASSW})
check('register شمارهٔ نامعتبر: کد ۴۰۰', st == 400 and r.get('ok') is False, f'{st} {r}')
st, r = req('POST', '/auth/login', {'phone': PH_USER, 'password': 'wrong-pass'})
check('login رمز غلط: ok=false', st == 200 and r.get('ok') is False, r)
st, r = req('POST', '/auth/login', {'phone': PH_USER, 'password': PASSW})
check('login درست: ok=true و توکن', st == 200 and r.get('ok') and r.get('token'), f'{st} {r}')
st, r = req('GET', '/auth/me', token=USER_TOKEN)
check('me با توکن: شماره درست', st == 200 and r.get('user', {}).get('phone') == PH_USER, f'{st} {r}')
st, r = req('GET', '/auth/me')
check('me بدون توکن: ۴۰۱/۴۰۳', st in (401, 403), st)

# ---------------- ۴) ورود با کد پیامکی حذف شده ----------------
for ep in ('/auth/otp/request', '/auth/otp/verify'):
    st, r = req('POST', ep, {'phone': PH_OTP_A, 'code': '123456'})
    check(f'{ep}: حذف شده (۴۰۴)', st == 404, st)
st, r = req('POST', '/auth/register', {'name': 'کاربر تست دو', 'phone': PH_OTP_B, 'password': 'pass-1234'})
check('register: پاسخ شامل نقش user (بدون امتیاز مدیر)', r.get('ok') and r.get('user', {}).get('role') == 'user', r)

# ---------------- ۵) ثبت سفارش (قیمت سمت سرور) ----------------
st, r = req('POST', '/admin/login', {'username': 'admin', 'password': 'admin1234'})
EARLY_ADMIN = r.get('token')
C5 = 'F' + suffix[:6]
st, r = req('POST', '/admin/coupons', {'code': C5, 'type': 'pct', 'val': 5, 'label': 'تست ۵٪'}, token=EARLY_ADMIN)
check('ساخت کد ۵٪ آزمایشی توسط مدیر', st == 200 and r.get('ok'), f'{st} {r}')
st, r = req('POST', '/orders', {'items': [{'pid': 1, 'w': 500, 'qty': 1}], 'shipType': 'post',
                                'addr': {'name': 'مهمان', 'phone': PH_USER, 'city': 'تهران', 'addr': 'خیابان آزمایشی، پلاک ۱۲، واحد ۳'}}, anon=True)
check('orders POST بدون ورود: ممنوع (۴۰۱) — ثبت سفارش فقط با حساب', st in (401, 403), st)
w1, q1, w2, q2 = 500, 2, 1000, 1
p1, p2 = pmap.get(pid1, {}), pmap.get(pid2, {})
sub_exp = unit_price(p1, w1) * q1 + unit_price(p2, w2) * q2
off_exp = js_round(sub_exp * 5 / 100)          # کد ۵٪ مدیر
ship_exp = 0 if sub_exp >= FREE_SHIP else SHIP['post']
total_exp = max(0, sub_exp - off_exp + ship_exp)
order_body = {
    'items': [{'pid': pid1, 'w': w1, 'qty': q1}, {'pid': pid2, 'w': w2, 'qty': q2}],
    'coupon': C5.lower(), 'shipType': 'post', 'client_code': CLIENT_CODE, 'note': 'تست خودکار',
    'addr': {'name': 'گیرندهٔ تست', 'phone': PH_USER, 'prov': 'تهران',
             'city': 'تهران', 'addr': 'خیابان آزمایشی، پلاک ۱۲، واحد ۳'},
}
st, r = req('POST', '/orders', order_body)
check('orders POST: ok=true و کد KG-', st == 200 and r.get('ok') and str(r.get('code', '')).startswith('KG-'), f'{st} {r}')
check('orders POST: جمع اقلام درست', r.get('sub') == sub_exp, f'got {r.get("sub")} want {sub_exp}')
check('orders POST: تخفیف کد ۵٪ درست', r.get('off') == off_exp, f'got {r.get("off")} want {off_exp}')
check('orders POST: هزینهٔ ارسال درست', r.get('ship_cost') == ship_exp, f'got {r.get("ship_cost")} want {ship_exp}')
check('orders POST: مبلغ نهایی درست', r.get('total') == total_exp, f'got {r.get("total")} want {total_exp}')
ORDER_CODE = r.get('code')
st, r = req('POST', '/orders', {**order_body, 'items': [{'pid': 999999, 'w': 500, 'qty': 1}]})
check('orders POST محصول ناموجود: ok=false', r.get('ok') is False and 'یافت نشد' in (r.get('msg') or ''), r)
st, r = req('POST', '/orders', {**order_body, 'items': [{'pid': pid1, 'w': 333, 'qty': 1}]})
check('orders POST وزن غیرمجاز: ok=false', r.get('ok') is False and 'وزن' in (r.get('msg') or ''), r)
st, r = req('POST', '/orders', {**order_body, 'coupon': 'NOPE123'})
check('orders POST کد تخفیف نامعتبر: پیام فارسی', r.get('ok') is False
      and 'کد تخفیف نامعتبر است' in (r.get('msg') or ''), r)
st, r = req('POST', '/orders', {**order_body, 'shipType': 'drone'})
check('orders POST ارسال نامعتبر: پیام فارسی', r.get('ok') is False
      and 'ارسال' in (r.get('msg') or ''), r)
st, r = req('POST', '/orders', {**order_body, 'addr': {**order_body['addr'], 'addr': 'کوتاه'}})
check('orders POST آدرس ناقص: کد ۴۰۰', st == 400 and r.get('ok') is False, f'{st} {r}')

# ---------------- ۶) پیگیری عمومی ----------------
st, r = req('GET', f'/orders/{ORDER_CODE}')
check('track با کد سرور: ok و اقلام', st == 200 and r.get('code') == ORDER_CODE
      and len(r.get('items', [])) == 2, f'{st} {r}')
st, r = req('GET', f'/orders/{CLIENT_CODE}')
check('track با کد مرورگر: همان سفارش', st == 200 and r.get('code') == ORDER_CODE, f'{st} {r}')
st, r = req('GET', '/orders/KG-00000')
check('track کد ناموجود: ۴۰۴', st == 404 and r.get('ok') is False, f'{st} {r}')

# ---------------- ۷) پنل مدیر ----------------
st, r = req('GET', '/orders')
check('orders GET بدون توکن: ۴۰۱/۴۰۳', st in (401, 403), st)
st, r = req('POST', '/admin/login', {'username': 'admin', 'password': 'nope'})
check('admin/login رمز غلط: ok=false', st == 200 and r.get('ok') is False, r)
st, r = req('POST', '/admin/login', {'username': 'admin', 'password': 'admin1234'})
check('admin/login درست: توکن', st == 200 and r.get('ok') and r.get('token'), f'{st} {r}')
ADMIN_TOKEN = r.get('token')

# ---------------- ۷-الف) مشتریان (پنل مدیر) ----------------
st, r = req('GET', '/admin/users')
check('admin/users بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('GET', '/admin/users', token=ADMIN_TOKEN)
check('admin/users: فهرست مشتریان با شمارندهٔ سفارش', st == 200 and r.get('ok') and isinstance(r.get('users'), list) and r['users']
      and all(k in r['users'][0] for k in ('name', 'phone', 'role', 'orders', 'spent')), f'{st} {str(r)[:200]}')
check('admin/users: رمز یا هش رمز در پاسخ نیست', 'password' not in str(r).lower())
st, r = req('GET', '/admin/users?q=' + PH_USER, token=ADMIN_TOKEN)
check('admin/users: جست‌وجو با موبایل', st == 200 and any(u['phone'] == PH_USER for u in r.get('users', [])), r)

# ---------------- ۷-ب) ظاهر سایت (تم/رنگ) سراسری ----------------
st, r = req('GET', '/settings')
check('settings: عمومی و دارای theme', st == 200 and r.get('ok') and r.get('theme') in ('default','anari','zeitoni','gahvei','tousi','banafsh','abi'), r)
st, r = req('PUT', '/admin/settings', {'theme': 'anari', 'tune': None})
check('admin/settings بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('PUT', '/admin/settings', {'theme': 'anari', 'tune': None}, token=ADMIN_TOKEN)
check('admin/settings با مدیر: ذخیره شد', st == 200 and r.get('ok') and r.get('theme') == 'anari', f'{st} {r}')
st, r = req('GET', '/settings')
check('settings: تم ذخیره‌شده برای همه (بدون توکن) دیده می‌شود', r.get('theme') == 'anari', r)
st, r = req('PUT', '/admin/settings', {'theme': '<script>', 'tune': None}, token=ADMIN_TOKEN)
check('admin/settings: تم نامعتبر رد می‌شود', st == 400, st)
st, r = req('PUT', '/admin/settings', {'theme': 'default', 'tune': ['#48b500', '#3f9d00', 'red;}', '#2f7600']}, token=ADMIN_TOKEN)
check('admin/settings: رنگ تزریقی (CSS) رد می‌شود', st == 400, st)
st, r = req('PUT', '/admin/settings', {'theme': 'default', 'tune': ['#48b500', '#3f9d00', '#378800', '#2f7600']}, token=ADMIN_TOKEN)
check('admin/settings: ۴ رنگ معتبر ذخیره', st == 200 and r.get('tune') == ['#48b500', '#3f9d00', '#378800', '#2f7600'], r)
req('PUT', '/admin/settings', {'theme': 'default', 'tune': None}, token=ADMIN_TOKEN)

st, r = req('GET', '/orders', token=ADMIN_TOKEN)
check('orders GET مدیر: ok و count', st == 200 and r.get('ok') and r.get('count', 0) >= 1, f'{st} {r}')
check('orders GET مدیر: اقلام در نتایج', bool(r.get('results'))
      and isinstance(r['results'][0].get('items'), list), (r.get('results') or [{}])[0])
st, r = req('GET', '/orders?status=0', token=ADMIN_TOKEN)
check('orders فیلتر وضعیت: همه ۰', r.get('ok') and all(x['status'] == 0 for x in r.get('results', [])), r.get('count'))
st, r = req('GET', f'/orders?phone={PH_USER}', token=ADMIN_TOKEN)
check('orders فیلتر شماره: همهٔ نتایج همان شماره', r.get('ok') and r.get('count', 0) >= 1
      and all(x['addr']['phone'] == PH_USER for x in r.get('results', [])), r.get('count'))
st, r = req('PATCH', f'/orders/{ORDER_CODE}', {'status': 1})
check('PATCH وضعیت بدون توکن: ۴۰۱/۴۰۳', st in (401, 403), st)
st, r = req('PATCH', f'/orders/{ORDER_CODE}', {'status': 1}, token=ADMIN_TOKEN)
check('PATCH وضعیت ۱: برچسب فارسی', st == 200 and r.get('ok') and r.get('status') == 1
      and r.get('status_label') == 'در حال آماده‌سازی', f'{st} {r}')
st, r = req('PATCH', f'/orders/{ORDER_CODE}', {'status': 9}, token=ADMIN_TOKEN)
check('PATCH وضعیت ۹: کد ۴۰۰', st == 400 and r.get('ok') is False, f'{st} {r}')
st, r = req('GET', '/orders/mine', token=USER_TOKEN)
check('orders/mine کاربر: سفارشش هست', st == 200 and r.get('ok') and r.get('count', 0) >= 1, f'{st} {r}')

# ---------------- ۸) آمار و گزارش پیامک ----------------
time.sleep(2)   # پیامک‌های پس‌زمینه ثبت شوند
st, r = req('GET', '/admin/stats', token=ADMIN_TOKEN)
check('admin/stats: ok و شمارنده‌ها', st == 200 and r.get('ok') and r.get('products', 0) >= 28
      and r.get('orders', 0) >= 1 and r.get('revenue', 0) >= total_exp, f'{st} {r}')
check('admin/stats: بلوک وضعیت پیامک', isinstance(r.get('sms'), dict) and 'sent' in r['sms'], r.get('sms'))
st, r = req('GET', '/admin/sms?limit=20', token=ADMIN_TOKEN)
check('admin/sms: گزارش پر است', st == 200 and r.get('ok') and len(r.get('results', [])) >= 1,
      len(r.get('results', [])) if isinstance(r, dict) else r)
check('admin/sms: فیلدهای ردیف', bool(r.get('results')) and
      all(k in r['results'][0] for k in ('ts', 'provider', 'to', 'text', 'tag', 'ok')), (r.get('results') or [{}])[0])
st, r = req('POST', '/admin/sms/test', {'to': PH_USER}, token=ADMIN_TOKEN)
check('admin/sms/test: ارسال آزمایشی (console)', st == 200 and r.get('ok') is True and r.get('sent') is True,
      f'{st} {r}')

# ---------------- ۹) CRUD محصول مدیر ----------------
newp = {'name': 'محصول تستی پسته', 'cat': 'ajil', 'img': '', 'price': 990000, 'weights': [250, 500],
        'stock': 15, 'disc': 10, 'grade': 'درجه یک', 'rate': 4.8, 'sold': 0, 'tags': ['تستی'],
        'sec': [], 'desc': 'محصول ساخته‌شده توسط تست خودکار', 'hide': False}
st, r = req('POST', '/products', newp)
check('products POST بدون توکن: ۴۰۱/۴۰۳', st in (401, 403), st)
st, r = req('POST', '/products', newp, token=ADMIN_TOKEN)
NEW_ID = r.get('product', {}).get('id') if isinstance(r.get('product'), dict) else None
check('products POST مدیر: ok و شناسهٔ ≥۱۰۱', st == 200 and r.get('ok') and (NEW_ID or 0) >= 101, f'{st} {r}')
st, r = req('PUT', f'/products/{NEW_ID}', {'price': 1230000}, token=ADMIN_TOKEN)
check('products PUT مدیر: قیمت به‌روز', st == 200 and r.get('ok')
      and r.get('product', {}).get('price') == 1230000, f'{st} {r}')
st, r = req('PUT', f'/products/{NEW_ID}', {'hide': True}, token=ADMIN_TOKEN)
check('products PUT مخفی‌سازی: ok', r.get('ok') is True, f'{st} {r}')
st, pub = req('GET', '/products')
check('محصول مخفی در فهرست عمومی نیست', all(p['id'] != NEW_ID for p in pub), NEW_ID)
st, r = req('GET', '/products?all=1', token=ADMIN_TOKEN)
check('محصول مخفی با ?all=1 برای مدیر هست', any(p['id'] == NEW_ID for p in r), NEW_ID)
st, r = req('POST', '/products', {**newp, 'price': 0}, token=ADMIN_TOKEN)
check('products POST قیمت نامعتبر: کد ۴۰۰', st == 400 and r.get('ok') is False, f'{st} {r}')
st, r = req('DELETE', f'/products/{NEW_ID}', token=ADMIN_TOKEN)
check('products DELETE مدیر: ok و deleted', st == 200 and r.get('ok') and r.get('deleted') == NEW_ID, f'{st} {r}')
st, r = req('GET', f'/products/{NEW_ID}')
check('محصول حذف‌شده: ۴۰۴', st == 404, st)


# ---------------- ۱۰) کدهای تخفیف (مدیریت از پنل) ----------------
st, r = req('GET', '/coupons/check?code=WELCOME10')
check('coupons/check بدون ورود: ممنوع (کد تخفیف فقط بعد از ورود)', st in (401, 403), st)
st, r = req('GET', '/coupons/check?code=WELCOME10', token=USER_TOKEN)
check('coupons/check: کد پیش‌فرض WELCOME10 معتبر و قاعده‌اش برمی‌گردد', st == 200 and r.get('ok') and r['coupon']['type'] == 'pct' and r['coupon']['val'] == 10, r)
st, r = req('GET', '/coupons/check?code=NOPE123', token=USER_TOKEN)
check('coupons/check: کد ناموجود → پیام فارسی', r.get('ok') is False and 'نامعتبر' in (r.get('msg') or ''), r)
st, r = req('GET', '/admin/coupons')
check('admin/coupons بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('GET', '/admin/coupons', token=ADMIN_TOKEN)
check('admin/coupons: فهرست شامل ۷ کد پیش‌فرض', st == 200 and len(r.get('coupons', [])) >= 7 and any(c['code'] == 'WELCOME10' for c in r['coupons']), f'{st}')
TC = 'T' + suffix[:6]
st, r = req('POST', '/admin/coupons', {'code': TC.lower(), 'type': 'pct', 'val': 10, 'min': 0, 'maxUses': 1, 'label': 'تست'}, token=ADMIN_TOKEN)
check('admin/coupons POST: ساخت (کد به حروف بزرگ)', st == 200 and r.get('ok') and r['coupon']['code'] == TC, f'{st} {r}')
TCID = r.get('coupon', {}).get('id')
st, r = req('POST', '/admin/coupons', {'code': TC, 'type': 'pct', 'val': 10}, token=ADMIN_TOKEN)
check('admin/coupons POST: کد تکراری رد می‌شود', st == 400, st)
for bad in ({'code': 'ab', 'type': 'pct', 'val': 5}, {'code': 'BADPCT1', 'type': 'pct', 'val': 150},
            {'code': 'BADTYPE', 'type': 'evil', 'val': 5}, {'code': 'BAD CODE', 'type': 'pct', 'val': 5},
            {'code': 'NEGMIN1', 'type': 'cash', 'val': 1000, 'min': -5}):
    st, r = req('POST', '/admin/coupons', bad, token=ADMIN_TOKEN)
    check(f'admin/coupons POST ورودی نامعتبر {bad["code"]}: ۴۰۰', st == 400, f'{st} {r}')
st, r = req('GET', f'/coupons/check?code={TC}', token=USER_TOKEN)
check('coupons/check: کد تازه ساخته‌شده قابل استفاده', r.get('ok') and r['coupon']['val'] == 10, r)
st, r = req('POST', '/orders', {**order_body, 'coupon': TC})
check('orders با کد مدیر: تخفیف ۱۰٪ درست', r.get('ok') and r.get('off') == round(r['sub'] * 0.10), r)
st, r = req('GET', '/admin/coupons', token=ADMIN_TOKEN)
mine = next((c for c in r.get('coupons', []) if c['code'] == TC), {})
check('شمارندهٔ استفادهٔ کد بعد از سفارش ۱ شد', mine.get('used') == 1, mine)
st, r = req('POST', '/orders', {**order_body, 'coupon': TC})
check('ظرفیت کد (maxUses=۱) تمام: سفارش دوم رد می‌شود', r.get('ok') is False and 'ظرفیت' in (r.get('msg') or ''), r)
st, r = req('GET', f'/coupons/check?code={TC}', token=USER_TOKEN)
check('coupons/check: کد پرشده دیگر معتبر نیست', r.get('ok') is False, r)
st, r = req('PUT', f'/admin/coupons/{TCID}', {'maxUses': 0, 'active': False}, token=ADMIN_TOKEN)
check('admin/coupons PUT: غیرفعال‌سازی', st == 200 and r['coupon']['active'] is False, f'{st} {r}')
st, r = req('POST', '/orders', {**order_body, 'coupon': TC})
check('کد غیرفعال در سفارش رد می‌شود', r.get('ok') is False, r)
st, r = req('PUT', f'/admin/coupons/{TCID}', {'active': True, 'expiresAt': '2020-01-01'}, token=ADMIN_TOKEN)
check('admin/coupons PUT: انقضای گذشته (فقط تاریخ) پذیرفته و وضعیت «مهلت» می‌شود', st == 200 and 'مهلت' in r['coupon']['status'], f'{st} {r}')
st, r = req('PUT', f'/admin/coupons/{TCID}', {'expiresAt': 'نه-تاریخ'}, token=ADMIN_TOKEN)
check('admin/coupons PUT: تاریخ نامعتبر → ۴۰۰ (نه ۵۰۰)', st == 400, st)
st, r = req('POST', '/orders', {**order_body, 'coupon': TC})
check('کد منقضی رد می‌شود', r.get('ok') is False and 'مهلت' in (r.get('msg') or ''), r)
st, r = req('DELETE', f'/admin/coupons/{TCID}', token=ADMIN_TOKEN)
check('admin/coupons DELETE', st == 200 and r.get('deleted') is True, f'{st} {r}')

# ---------------- ۱۱) مدیریت کاربران و داشبورد ----------------
st, r = req('GET', '/admin/users?q=' + PH_OTP_B, token=ADMIN_TOKEN)
uid = (r.get('users') or [{}])[0].get('id')
st, r = req('PATCH', f'/admin/users/{uid}', {'active': False})
check('admin/users PATCH بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('PATCH', f'/admin/users/{uid}', {'active': False}, token=ADMIN_TOKEN)
check('admin/users PATCH: غیرفعال‌سازی کاربر', st == 200 and r['user']['active'] is False, f'{st} {r}')
st, r = req('POST', '/auth/login', {'phone': PH_OTP_B, 'password': 'pass-1234'})
check('کاربر غیرفعال نمی‌تواند وارد شود', r.get('ok') is False, r)
st, r = req('PATCH', f'/admin/users/{uid}', {'active': True, 'password': 'new-pass-9'}, token=ADMIN_TOKEN)
check('admin/users PATCH: فعال‌سازی + رمز موقت', st == 200 and r['user']['active'] is True, f'{st} {r}')
st, r = req('POST', '/auth/login', {'phone': PH_OTP_B, 'password': 'new-pass-9'})
check('ورود با رمز تعیین‌شده توسط مدیر', r.get('ok') is True, r)
st, r = req('PATCH', f'/admin/users/{uid}', {'password': 'ab'}, token=ADMIN_TOKEN)
check('رمز کوتاه رد می‌شود', st == 400, st)
st, r = req('PATCH', f'/admin/users/{uid}', {'role': 'superman'}, token=ADMIN_TOKEN)
check('نقش نامعتبر رد می‌شود', st == 400, st)
st, r = req('PATCH', f'/admin/users/{uid}', {'role': 'admin'}, token=ADMIN_TOKEN)
check('ارتقا به مدیر', st == 200 and r['user']['role'] == 'admin', f'{st} {r}')
st, r = req('PATCH', f'/admin/users/{uid}', {'role': 'user'}, token=ADMIN_TOKEN)
check('بازگرداندن به کاربر عادی', st == 200 and r['user']['role'] == 'user', f'{st} {r}')
st, r = req('GET', '/admin/stats', token=ADMIN_TOKEN)
check('stats: نمودار ۷ روز، پرفروش‌ها و وضعیت سفارش‌ها', st == 200 and len(r.get('daily', [])) == 7 and isinstance(r.get('top'), list)
      and isinstance(r.get('byStatus'), dict) and 'lowStockItems' in r, str(r)[:200])
st, me = req('GET', '/auth/me', token=ADMIN_TOKEN)
st, r = req('GET', '/admin/users?q=' + (me.get('user', {}).get('phone') or '0912'), token=ADMIN_TOKEN)
selfid = next((u['id'] for u in r.get('users', []) if u['phone'] == me.get('user', {}).get('phone')), None)
st, r = req('PATCH', f'/admin/users/{selfid}', {'role': 'user'}, token=ADMIN_TOKEN)
check('مدیر نمی‌تواند نقش خودش را پایین بیاورد', st == 400, f'{st} {r}')


# ---------------- ۱۲) مرحلهٔ شمارهٔ موبایل در تکمیل خرید ----------------
st, r = req('POST', '/auth/phone-check', {'phone': PH_USER})
check('phone-check: شمارهٔ موجود → exists=true', st == 200 and r.get('exists') is True, r)
st, r = req('POST', '/auth/phone-check', {'phone': '0919' + suffix[:7]})
check('phone-check: شمارهٔ جدید → exists=false', st == 200 and r.get('exists') is False, r)
st, r = req('POST', '/auth/phone-check', {'phone': '123'})
check('phone-check: شمارهٔ نامعتبر → ۴۰۰', st == 400, st)

# ---------------- ۱۳) هزینه‌های ارسال (مدیریت از پنل) ----------------
st, r = req('GET', '/site')
check('site: اطلاعات/ارسال/صفحات/کارت‌شانس در یک درخواست', st == 200 and all(k in r for k in ('info', 'shipping', 'pages', 'lucky')), list(r)[:6])
check('site: ۳ روش ارسال پیش‌فرض و سقف رایگان', len(r['shipping']['methods']) == 3 and r['shipping']['freeFrom'] == 1_500_000, r['shipping'])
st, r = req('GET', '/admin/shipping')
check('admin/shipping بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('POST', '/admin/shipping', {'type': 'bike' + suffix[:3], 'label': 'پیک موتوری', 'cost': 45000, 'days': 'امروز'}, token=ADMIN_TOKEN)
check('admin/shipping POST: روش جدید', st == 200 and r['method']['cost'] == 45000, f'{st} {r}')
SMID = r.get('method', {}).get('id'); SMKEY = r.get('method', {}).get('type')
for bad in ({'type': 'x', 'label': 'کوتاه کلید', 'cost': 1}, {'type': 'okkey', 'label': 'منفی', 'cost': -5}, {'type': 'okkey2', 'label': 'ع', 'cost': 5}):
    st, r = req('POST', '/admin/shipping', bad, token=ADMIN_TOKEN)
    check(f'admin/shipping POST ورودی نامعتبر {bad["type"]}: ۴۰۰', st == 400, f'{st} {r}')
st, r = req('PUT', f'/admin/shipping/{SMID}', {'cost': 70000}, token=ADMIN_TOKEN)
check('admin/shipping PUT: تغییر هزینه', st == 200 and r['method']['cost'] == 70000, f'{st} {r}')
small = {'items': [{'pid': pid1, 'w': 250, 'qty': 1}], 'shipType': SMKEY,
         'addr': {'name': 'گیرنده', 'phone': PH_USER, 'city': 'تهران', 'addr': 'خیابان ارسال آزمایشی کامل ۱۲۳'}}
st, r = req('POST', '/orders', small)
check('سفارش با روش ارسال جدید: هزینهٔ تعیین‌شده توسط مدیر اعمال می‌شود', r.get('ok') and r.get('ship_cost') == 70000, r)
st, r = req('PUT', '/admin/shipping/settings', {'freeFrom': 10000, 'freeEnabled': True}, token=ADMIN_TOKEN)
check('admin/shipping/settings: سقف ارسال رایگان ۱۰٬۰۰۰', st == 200 and r['freeFrom'] == 10000, f'{st} {r}')
st, r = req('POST', '/orders', small)
check('سقف ارسال رایگان قابل تنظیم: ارسال رایگان می‌شود', r.get('ok') and r.get('ship_cost') == 0, r)
st, r = req('PUT', '/admin/shipping/settings', {'freeFrom': 10000, 'freeEnabled': False}, token=ADMIN_TOKEN)
st, r = req('POST', '/orders', small)
check('ارسال رایگان خاموش: هزینه دوباره اعمال می‌شود', r.get('ok') and r.get('ship_cost') == 70000, r)
st, r = req('PUT', '/admin/shipping/settings', {'freeFrom': -5}, token=ADMIN_TOKEN)
check('سقف منفی رد می‌شود', st == 400, st)
st, r = req('PUT', '/admin/shipping/settings', {'freeFrom': 1500000, 'freeEnabled': True}, token=ADMIN_TOKEN)
st, r = req('PUT', f'/admin/shipping/{SMID}', {'active': False}, token=ADMIN_TOKEN)
st, r = req('POST', '/orders', small)
check('روش غیرفعال در سفارش رد می‌شود', r.get('ok') is False and 'ارسال' in (r.get('msg') or ''), r)
st, r = req('GET', '/admin/shipping', token=ADMIN_TOKEN)
others = [m for m in r['methods'] if m['active'] and m['id'] != SMID]
for m in others[:-1]:
    req('PUT', f'/admin/shipping/{m["id"]}', {'active': False}, token=ADMIN_TOKEN)
st, r = req('DELETE', f'/admin/shipping/{others[-1]["id"]}', token=ADMIN_TOKEN)
check('حذف آخرین روش فعال ممنوع است', st == 400, f'{st} {r}')
for m in others[:-1]:
    req('PUT', f'/admin/shipping/{m["id"]}', {'active': True}, token=ADMIN_TOKEN)
st, r = req('DELETE', f'/admin/shipping/{SMID}', token=ADMIN_TOKEN)
check('admin/shipping DELETE', st == 200, f'{st} {r}')

# ---------------- ۱۴) محتوای سایت: اطلاعات و صفحات ----------------
st, r = req('GET', '/site')
slugs = [p['slug'] for p in r['pages']]
check('صفحات پیش‌فرض راهنما: ثبت سفارش/ارسال/مرجوعی/سوالات متداول/درباره/تماس/حریم/قوانین',
      all(x in slugs for x in ('how-to-order', 'shipping-info', 'returns', 'faq', 'about', 'contact', 'privacy', 'terms')), slugs)
st, r = req('GET', '/pages/faq')
check('pages/faq: ۸ سوال و جواب', st == 200 and len(r['page']['items']) >= 8 and r['page']['items'][0]['q'], f'{st}')
st, r = req('GET', '/pages/how-to-order')
check('pages/how-to-order: متن راهنما موجود', st == 200 and 'ثبت سفارش' in r['page']['body'], f'{st}')
st, r = req('GET', '/pages/nope-page')
check('pages: صفحهٔ ناموجود ۴۰۴', st == 404, st)
st, r = req('PUT', '/admin/info', {'phone': '۰۲۱-۱۲۳۴۵۶۷۸'})
check('admin/info بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('PUT', '/admin/info', {'phone': '۰۲۱-۱۲۳۴۵۶۷۸', 'phoneTel': '02112345678', 'instagram': 'https://instagram.com/test'}, token=ADMIN_TOKEN)
check('admin/info: ذخیرهٔ اطلاعات تماس', st == 200 and r['info']['phone'] == '۰۲۱-۱۲۳۴۵۶۷۸', f'{st} {r}')
st, r = req('GET', '/site')
check('site: اطلاعات ویرایش‌شده برای همه دیده می‌شود', r['info']['phoneTel'] == '02112345678', r['info'])
for bad in ({'instagram': 'javascript:alert(1)'}, {'phoneTel': 'abc'}, {'address': 'x' * 400}):
    st, r = req('PUT', '/admin/info', bad, token=ADMIN_TOKEN)
    check(f'admin/info ورودی نامعتبر {list(bad)[0]}: ۴۰۰', st == 400, f'{st} {r}')
req('PUT', '/admin/info', {'phone': '۰۲۱-۹۱۰۹۲۰۰۰', 'phoneTel': '02191092000', 'instagram': ''}, token=ADMIN_TOKEN)
PG = 'g' + suffix[:5]
st, r = req('POST', '/admin/pages', {'slug': PG, 'title': 'صفحهٔ تست', 'kind': 'text', 'group': 'guide', 'body': '## سلام\n\n- مورد ۱'}, token=ADMIN_TOKEN)
check('admin/pages POST: صفحهٔ جدید', st == 200 and r['page']['slug'] == PG, f'{st} {r}')
PGID = r.get('page', {}).get('id')
st, r = req('GET', f'/pages/{PG}')
check('صفحهٔ ساخته‌شده عمومی است', st == 200 and r['page']['title'] == 'صفحهٔ تست', st)
st, r = req('PUT', f'/admin/pages/{PGID}', {'active': False}, token=ADMIN_TOKEN)
st, r = req('GET', f'/pages/{PG}')
check('صفحهٔ غیرفعال عمومی نیست', st == 404, st)
for bad in ({'slug': 'Bad Slug', 'title': 'x'}, {'slug': 'ok-slug', 'title': ''}, {'slug': 'ok-slug2', 'title': 'ت', 'kind': 'evil'},
            {'slug': 'ok-slug3', 'title': 'ت', 'kind': 'faq', 'items': [{'q': 'فقط سوال', 'a': ''}]}):
    st, r = req('POST', '/admin/pages', bad, token=ADMIN_TOKEN)
    check(f'admin/pages ورودی نامعتبر: ۴۰۰', st == 400, f'{st} {r}')
st, r = req('POST', '/admin/pages', {'slug': 'faq', 'title': 'تکراری'}, token=ADMIN_TOKEN)
check('admin/pages: نشانی تکراری رد می‌شود', st == 400, st)
st, r = req('DELETE', f'/admin/pages/{PGID}', token=ADMIN_TOKEN)
check('admin/pages DELETE', st == 200, st)

# ---------------- ۱۵) درخواست مشاوره ----------------
st, r = req('POST', '/consult', {'name': 'مشتری مشاوره', 'phone': '0914' + suffix[:7], 'topic': 'خرید عمده'})
check('consult: ثبت درخواست مشاوره', st == 200 and r.get('ok'), f'{st} {r}')
st, r = req('POST', '/consult', {'name': 'ن', 'phone': '0914' + suffix[:7]})
check('consult: نام کوتاه رد می‌شود', st == 400, st)
st, r = req('POST', '/consult', {'name': 'مشتری', 'phone': '55'})
check('consult: شمارهٔ نامعتبر رد می‌شود', st == 400, st)
st, r = req('GET', '/admin/consults')
check('admin/consults بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('GET', '/admin/consults', token=ADMIN_TOKEN)
mine = next((c for c in r.get('consults', []) if c['phone'] == '0914' + suffix[:7]), {})
check('admin/consults: درخواست ثبت‌شده در فهرست مدیر', bool(mine) and mine['done'] is False, r)
st, r = req('PATCH', f'/admin/consults/{mine.get("id")}', {'done': True}, token=ADMIN_TOKEN)
check('admin/consults PATCH: علامت‌گذاری پیگیری‌شده', st == 200, st)

# ---------------- ۱۶) کارت شانس (روی حساب، سمت سرور) ----------------
st, r = req('POST', '/lucky/spin')
check('lucky/spin بدون ورود: ممنوع', st in (401, 403), st)
st, r = req('GET', '/lucky/status')
check('lucky/status مهمان: نیاز به ورود (canSpin=false)', r.get('canSpin') is False and r.get('loggedIn') is False, r)
st, r = req('POST', '/auth/register', {'name': 'شانس‌آزما یک', 'phone': '0915' + suffix[:7], 'password': 'pass-1234'})
LT1 = r.get('token')
st, r = req('POST', '/auth/register', {'name': 'شانس‌آزما دو', 'phone': '0916' + suffix[:7], 'password': 'pass-1234'})
LT2 = r.get('token')
st, r = req('GET', '/lucky/status', token=LT1)
check('lucky/status کاربر تازه: می‌تواند بچرخاند', r.get('canSpin') is True, r)
st, r = req('POST', '/lucky/spin', token=LT1)
check('lucky/spin: جایزه + کد شخصی LK-', st == 200 and r.get('ok') and str(r.get('code', '')).startswith('LK-') and r['prize']['title'], f'{st} {r}')
LCODE = r.get('code')
st, r = req('POST', '/lucky/spin', token=LT1)
check('lucky/spin پشت‌سرهم: رد می‌شود (محدودیت زمانی) و زمان بعدی می‌آید', r.get('ok') is False and r.get('nextAt'), f'{st} {r}')
st, r = req('GET', '/lucky/status', token=LT1)
check('lucky/status بعد از چرخش: canSpin=false', r.get('canSpin') is False and r.get('nextAt'), r)
st, r = req('GET', '/lucky/mine', token=LT1)
check('lucky/mine: جایزه روی حساب ثبت شده', st == 200 and any(w['code'] == LCODE and w['used'] is False for w in r['wins']), r)
st, r = req('GET', '/lucky/mine', token=LT2)
check('lucky/mine: جایزهٔ حساب دیگر دیده نمی‌شود', r.get('wins') == [], r)
st, r = req('GET', f'/coupons/check?code={LCODE}', token=LT2)
check('کد جایزه روی حساب دیگر رد می‌شود (متعلق به حساب دیگری)', r.get('ok') is False and 'حساب دیگری' in (r.get('msg') or ''), r)
st, r = req('POST', '/orders', {**small, 'shipType': 'post', 'items': [{'pid': pid1, 'w': 1000, 'qty': 2}], 'coupon': LCODE}, token=LT2)
check('سفارش با کد جایزهٔ دیگری رد می‌شود', r.get('ok') is False and 'حساب دیگری' in (r.get('msg') or ''), r)
st, r = req('GET', f'/coupons/check?code={LCODE}', token=LT1)
check('کد جایزه برای صاحبش معتبر است', r.get('ok') is True, r)
rule = r.get('coupon', {})
big = {**small, 'shipType': 'post', 'items': [{'pid': pid1, 'w': 2000, 'qty': 5}], 'coupon': LCODE}
st, r = req('POST', '/orders', big, token=LT1)
check('سفارش با کد جایزه توسط صاحبش', r.get('ok') is True or 'کافی نیست' in (r.get('msg') or ''), r)
if r.get('ok'):
    st, r2 = req('POST', '/orders', big, token=LT1)
    check('کد جایزه یک‌بارمصرف است: بار دوم رد می‌شود', r2.get('ok') is False and 'ظرفیت' in (r2.get('msg') or ''), r2)
# مدیر: تنظیمات و جایزه‌ها
st, r = req('GET', '/admin/lucky')
check('admin/lucky بدون توکن: ممنوع', st in (401, 403), st)
st, r = req('GET', '/admin/lucky', token=ADMIN_TOKEN)
check('admin/lucky: جایزه‌ها، تنظیمات و فهرست برندگان', st == 200 and len(r['prizes']) >= 6 and r['settings']['cooldownHours'] and r['wins'], f'{st}')
st, r = req('PUT', '/admin/lucky', {'enabled': True, 'cooldownHours': 0, 'validDays': 30}, token=ADMIN_TOKEN)
check('admin/lucky: فاصلهٔ ۰ ساعت رد می‌شود', st == 400, st)
st, r = req('PUT', '/admin/lucky', {'enabled': False, 'cooldownHours': 24, 'validDays': 30}, token=ADMIN_TOKEN)
st, r = req('POST', '/lucky/spin', token=LT2)
check('کارت شانس خاموش: چرخش رد می‌شود', r.get('ok') is False, r)
st, r = req('PUT', '/admin/lucky', {'enabled': True, 'cooldownHours': 24, 'validDays': 30}, token=ADMIN_TOKEN)
st, r = req('POST', '/admin/lucky', {'title': 'جایزهٔ تست', 'type': 'pct', 'val': 7, 'weight': 3}, token=ADMIN_TOKEN)
check('admin/lucky: جایزهٔ جدید', st == 200 and r['prize']['val'] == 7, f'{st} {r}')
PRID = r.get('prize', {}).get('id')
st, r = req('POST', '/admin/lucky', {'title': 'بد', 'type': 'pct', 'val': 900}, token=ADMIN_TOKEN)
check('admin/lucky: درصد نامعتبر رد می‌شود', st == 400, st)
st, r = req('DELETE', f'/admin/lucky/prizes/{PRID}', token=ADMIN_TOKEN)
check('admin/lucky: حذف جایزه', st == 200, st)

# ---------------- جمع‌بندی ----------------
print('=' * 64)
print(f'نتیجه: {len(PASS)} موفق، {len(FAIL)} ناموفق از {len(PASS) + len(FAIL)} بررسی')
if FAIL:
    print('بررسی‌های ناموفق:')
    for name, d in FAIL:
        print(f'  ✗ {name} → {d}')
sys.exit(1 if FAIL else 0)
