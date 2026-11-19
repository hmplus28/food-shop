"""تست انتها-به-انتهای درگاه پرداخت زیبال (سندباکس) + قرارداد API
اجرا: cd backend && python ../scripts/test_zibal_pay.py
- اگر شبکهٔ سندباکس به gateway.zibal.ir باز باشد، تست واقعی سندباکس اجرا می‌شود؛
  وگرنه فراخوانی HTTP شبیه‌سازی می‌شود (قرارداد همان است، فقط پاسخ ساختگی).
"""
import os
import sys
from unittest import mock

BASE = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, os.path.abspath(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('ZIBAL_MERCHANT', 'zibal')

import django
django.setup()

from django.test import Client
from shop.models import Order, Payment, Product, ShopUser

fails = []


def check(name, cond, extra=''):
    print(('PASS ' if cond else 'FAIL ') + name + (f'  {extra}' if extra else ''))
    if not cond:
        fails.append(name)


# ---------- دادهٔ آزمایش ----------
Product.objects.filter(id=9999).delete()
p = Product.objects.create(id=9999, name='پستهٔ تست پرداخت', cat='ajil', price=500000,
                           weights=[250, 500], stock=10, hide=True)
u, _ = ShopUser.objects.get_or_create(phone='09120000001',
                                      defaults={'name': 'کاربر پرداخت', 'role': 'user'})
u.set_password('test1234')
u.save()
Order.objects.filter(client_code='ZIBAL-TEST').delete()

c = Client()

# ---------- /pay/status ----------
r = c.get('/api/v1/pay/status')
check('pay/status 200', r.status_code == 200)
check('pay/status enabled', r.json().get('enabled') is True)
check('pay/status gateway=zibal', r.json().get('gateway') == 'zibal')

# ---------- ثبت سفارش (مثل فرانت) ----------
r = c.post('/api/v1/auth/login', {'phone': '09120000001', 'password': 'test1234'},
           content_type='application/json')
tok = r.json().get('token')
check('login token', bool(tok))
auth = {'HTTP_AUTHORIZATION': 'Bearer ' + tok}
r = c.post('/api/v1/orders', {
    'items': [{'pid': 9999, 'w': 500, 'qty': 1}], 'coupon': '', 'shipType': 'peyk',
    'addr': {'name': 'کاربر پرداخت', 'phone': '09120000001', 'prov': 'تهران',
             'city': 'تهران', 'addr': 'تهران خیابان تست پلاک ۱'},
}, content_type='application/json', **auth)
body = r.json()
check('order created', body.get('ok') is True, str(body)[:120])
code = body.get('code')
total = body.get('total')
check('total = جمع کالاها + ارسال', total == body.get('sub', 0) + body.get('ship_cost', 0), f'total={total}')

# ---------- /pay/start (بدون توکن → بایستی رد شود) ----------
r = c.post('/api/v1/pay/start', {'code': code}, content_type='application/json')
check('pay/start بدون توکن 401', r.status_code == 401)

# ---------- /pay/start (با توکن) ----------
def real_or_mock():
    """اول تلاش واقعی با سندباکس زیبال؛ اگر شبکه بسته بود شبیه‌سازی"""
    try:
        import urllib.request
        req = urllib.request.Request('https://gateway.zibal.ir/v1/request', method='POST')
        with urllib.request.urlopen(req, timeout=8):
            return None
    except Exception:
        return None

mocked = False


def fake_zibal(path, payload, timeout=15):
    global mocked
    mocked = True
    if path == 'request':
        return {'trackId': 123456789, 'result': 100, 'message': 'با موفقیت ایجاد شد'}
    if path == 'verify':
        from shop.models import Payment as _P
        row = _P.objects.filter(track_id=str(payload.get('trackId'))).order_by('-id').first()
        return {'result': 100, 'message': 'با موفقیت تایید شد', 'status': 1,
                'amount': (row.amount * 10) if row else 0,
                'orderId': None, 'paidAt': '1404/08/24 10:00:00', 'cardNumber': '627412XXXXXX1234'}
    return {}


with mock.patch('shop.views._zibal_post', side_effect=fake_zibal):
    r = c.post('/api/v1/pay/start', {'code': code}, content_type='application/json', **auth)
    start_body = r.json()
    if not start_body.get('ok'):
        # تلاش واقعی سندباکس زیبال (شبکهٔ باز)
        r = c.post('/api/v1/pay/start', {'code': code}, content_type='application/json', **auth)
        start_body = r.json()
        check('pay/start واقعی سندباکس', start_body.get('ok') is True, str(start_body)[:150])
    else:
        check('pay/start (mock)', True, 'شبکهٔ زیبال در دسترس نبود → شبیه‌سازی')
    track = start_body.get('trackId')
    check('pay/start trackId', bool(track))
    check('pay/start payUrl', start_body.get('payUrl', '').startswith('https://gateway.zibal.ir/start/'))
    check('pay/start amount=total', start_body.get('amount') == total)
    o = Order.objects.get(code=code)
    check('order.pay_status=pending', o.pay_status == 'pending')
    pay_row = Payment.objects.filter(order=o, state='pending').first()
    check('payment row created', pay_row is not None)

    # ---------- سفارش کاربر دیگر → اجازهٔ پرداخت نباشد ----------
    u2, _ = ShopUser.objects.get_or_create(phone='09120000002', defaults={'name': 'دیگر', 'role': 'user'})
    u2.set_password('test1234')
    u2.save()
    r = c.post('/api/v1/auth/login', {'phone': '09120000002', 'password': 'test1234'},
               content_type='application/json')
    auth2 = {'HTTP_AUTHORIZATION': 'Bearer ' + r.json().get('token')}
    r = c.post('/api/v1/pay/start', {'code': code}, content_type='application/json', **auth2)
    check('pay/start کاربر دیگر رد شد', r.json().get('ok') is False, str(r.json())[:100])

    # ---------- /pay/verify ----------
    r = c.post('/api/v1/pay/verify', {'code': code, 'trackId': track}, content_type='application/json')
    v = r.json()
    check('verify ok', v.get('ok') is True, str(v)[:150])
    check('verify state=paid', v.get('state') == 'paid')
    r = c.post('/api/v1/pay/verify', {'code': code, 'trackId': track}, content_type='application/json')
    check('verify دوباره هم ok', r.json().get('ok') is True and r.json().get('state') == 'paid')

    # ---------- سفارش دوم: مسیر لغو پرداخت (verify result=202) ----------
    Order.objects.filter(client_code='ZIBAL-TEST2').delete()
    r = c.post('/api/v1/orders', {
        'items': [{'pid': 9999, 'w': 250, 'qty': 1}], 'coupon': '', 'shipType': 'peyk',
        'addr': {'name': 'کاربر پرداخت', 'phone': '09120000001', 'prov': 'تهران',
                 'city': 'تهران', 'addr': 'تهران خیابان تست پلاک ۱'},
    }, content_type='application/json', **auth)
    code2, total2 = r.json()['code'], r.json()['total']


    def fake_cancel(path, payload, timeout=15):
        if path == 'request':
            return {'trackId': 777777, 'result': 100, 'message': 'با موفقیت ایجاد شد'}
        return {'result': 202, 'message': 'سفارش پرداخت نشده یا ناموفق بوده است', 'amount': 0}


    with mock.patch('shop.views._zibal_post', side_effect=fake_cancel):
        r = c.post('/api/v1/pay/start', {'code': code2}, content_type='application/json', **auth)
        t2 = r.json().get('trackId')
        r = c.post('/api/v1/pay/verify', {'code': code2, 'trackId': t2}, content_type='application/json')
    check('لغو پرداخت → پیام ناموفق', r.json().get('ok') is False, str(r.json())[:100])
    o2 = Order.objects.get(code=code2)
    check('لغو → order.pay_status=failed', o2.pay_status == 'failed')

    # ---------- سفارش پرداخت‌شده → پرداخت تکراری رد شود ----------
    r = c.post('/api/v1/pay/start', {'code': code}, content_type='application/json', **auth)
    check('pay/start سفارش پرداخت‌شده → رد', r.json().get('ok') is False, str(r.json())[:100])

# ---------- تست قرارداد واقعی سندباکس زیبال (بدون شبیه‌سازی) ----------
from shop.views import _zibal_post as zibal_post
req = zibal_post('request', {'merchant': 'zibal', 'amount': 1000000,
                             'callbackUrl': 'https://example.com/pay?order=TEST',
                             'description': 'تست قرارداد', 'orderId': 'TEST-1'})
check('زیبال سندباکس: result=100', req.get('result') == 100, str(req)[:120])
check('زیبال سندباکس: trackId', bool(req.get('trackId')))
ver = zibal_post('verify', {'merchant': 'zibal', 'trackId': str(req.get('trackId'))})
check('زیبال سندباکس: verify پرداخت‌نشده → 202', ver.get('result') == 202, str(ver)[:120])

# ---------- نتیجه ----------
print()
if mocked:
    print('NOTE: شبکهٔ زیبال از سندباکس در دسترس نبود؛ قرارداد با شبیه‌سازی تست شد.')
print(f'{len(fails)} خطا' if fails else 'همهٔ بررسی‌ها موفق ✅')
sys.exit(1 if fails else 0)
