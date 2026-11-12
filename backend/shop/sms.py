"""سرویس پیامک فروشگاه خانم گل — اتصال به «پنل پیامکی»

سرویس‌دهنده‌های پشتیبانی‌شده (با SMS_PROVIDER در backend/.env انتخاب می‌شود):

  kavenegar    کاوه‌نگار — ارسال عادی + کد یکبار مصرف با قالب Verify (Lookup)
  smsir        SMS.ir — ارسال انبوه + کد یکبار مصرف با قالب Verify
  ghasedak     قاصدک — ارسال ساده + کد یکبار مصرف با قالب
  melipayamak  ملی پیامک — ارسال ساده (کد یکبار مصرف به‌صورت متن)
  console      حالت توسعه — پیامک واقعی نمی‌رود؛ در لاگ سرور و «پیامک‌های پنل مدیر» ثبت می‌شود

همهٔ ارسال‌ها در مدل SmsLog ثبت می‌شوند تا مدیر از پنل Vue (تب «پیامک‌ها»)
وضعیت اتصال پنل پیامکی را ببیند. ارسال‌های اطلاع‌رسانی سفارش با Thread
پس‌زمینه انجام می‌شود تا پاسخ درگاه/تسویه کند نشود.
"""
import re
import threading
import urllib.parse
import urllib.request
import json
import logging

from django.conf import settings

from .models import SmsLog

log = logging.getLogger('shop.sms')

PHONE_RE = re.compile(r'^09\d{9}$')
HTTP_TIMEOUT = 8


def normalize_phone(raw):
    """۰۹۱۲… / +98912… / 0098912… / 912… / ارقام فارسی و عربی → 0912…  |  نامعتبر → None"""
    if raw is None:
        return None
    s = str(raw).strip()
    # ارقام فارسی (U+06F0…F9) و عربی (U+0660…69) → ASCII
    s = s.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789'))
    digits = re.sub(r'\D', '', s)
    if digits.startswith('98') and len(digits) == 12:
        digits = '0' + digits[2:]
    elif digits.startswith('0098') and len(digits) == 14:
        digits = '0' + digits[4:]
    elif not digits.startswith('0') and len(digits) == 10:
        digits = '0' + digits
    return digits if PHONE_RE.match(digits) else None


def provider_status():
    """وضعیت اتصال پنل پیامک — برای /health و پنل مدیر"""
    p = settings.SMS_PROVIDER
    configured = {
        'console': True,
        'kavenegar': bool(settings.KAVENEGAR_API_KEY),
        'smsir': bool(settings.SMSIR_API_KEY),
        'ghasedak': bool(settings.GHASEDAK_API_KEY),
        'melipayamak': bool(settings.MELIPAYAMAK_USERNAME and settings.MELIPAYAMAK_PASSWORD),
    }.get(p, False)
    return {'provider': p, 'configured': configured}


# ---------------- ارسال HTTP کمکی (بدون وابستگی extra) ----------------

def _http_json(url, method='GET', headers=None, params=None, body=None, timeout=HTTP_TIMEOUT):
    """درخواست سادهٔ stdlib؛ خروجی (ok, detail)"""
    try:
        if params:
            url = url + ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
        data = None
        hdrs = dict(headers or {})
        if body is not None:
            data = json.dumps(body).encode('utf-8')
            hdrs.setdefault('Content-Type', 'application/json')
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read(2048).decode('utf-8', 'replace')
            return 200 <= resp.status < 300, text or f'HTTP {resp.status}'
    except urllib.error.HTTPError as e:
        try:
            text = e.read(512).decode('utf-8', 'replace')
        except Exception:
            text = ''
        return False, f'HTTP {e.code}: {text}'
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def _http_form(url, headers=None, fields=None, timeout=HTTP_TIMEOUT):
    try:
        data = urllib.parse.urlencode(fields or {}).encode('utf-8')
        hdrs = dict(headers or {})
        hdrs.setdefault('Content-Type', 'application/x-www-form-urlencoded')
        req = urllib.request.Request(url, data=data, headers=hdrs, method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300, resp.read(2048).decode('utf-8', 'replace') or f'HTTP {resp.status}'
    except urllib.error.HTTPError as e:
        try:
            return False, f'HTTP {e.code}: ' + e.read(512).decode('utf-8', 'replace')
        except Exception:
            return False, f'HTTP {e.code}'
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def _fmt_money(n):
    return f'{int(n):,}'


# ---------------- آداپتورهای سرویس‌دهنده‌ها ----------------

def _send_kavenegar(to, text):
    base = f'https://api.kavenegar.com/v1/{settings.KAVENEGAR_API_KEY}'
    ok, detail = _http_json(base + '/sms/send.json', params={
        'receptor': to, 'message': text, **({'sender': settings.SMS_SENDER} if settings.SMS_SENDER else {}),
    })
    if ok and '"status":200' not in detail and 'return' in detail:
        # کاوه‌نگار کد وضعیت داخلی هم دارد؛ پاسخ ۲۰۰ ولی status != 200 یعنی خطا
        try:
            if json.loads(detail).get('return', {}).get('status') != 200:
                return False, detail[:300]
        except Exception:
            pass
    return ok, detail[:300]


def _send_smsir(to, text):
    return _http_json('https://api.sms.ir/v1/send/bulk', method='POST',
                      headers={'x-api-key': settings.SMSIR_API_KEY},
                      body={'lineNumber': settings.SMSIR_LINE, 'messageText': text, 'mobiles': [to]})


def _send_ghasedak(to, text):
    return _http_form('https://api.ghasedak.me/v2/sms/send/simple',
                      headers={'apikey': settings.GHASEDAK_API_KEY},
                      fields={'message': text, 'receptor': to, **({'linenumber': settings.GHASEDAK_LINE} if settings.GHASEDAK_LINE else {})})


def _send_melipayamak(to, text):
    return _http_json('https://rest.payamak-panel.com/api/SendSMS/SendSMS', method='POST',
                      body={'username': settings.MELIPAYAMAK_USERNAME, 'password': settings.MELIPAYAMAK_PASSWORD,
                            'to': to, 'from': settings.MELIPAYAMAK_FROM, 'text': text, 'isflash': False})


SENDERS = {
    'kavenegar':   {'send': _send_kavenegar},
    'smsir':       {'send': _send_smsir},
    'ghasedak':    {'send': _send_ghasedak},
    'melipayamak': {'send': _send_melipayamak},
    'console':     {'send': lambda to, t: (True, 'console')},
}


def send_sms(to, text, tag=''):
    """ارسال پیامک + ثبت در گزارش. خروجی (ok, detail)"""
    to = normalize_phone(to)
    if not to:
        return False, 'شماره گیرنده معتبر نیست'
    provider = settings.SMS_PROVIDER
    sender = SENDERS.get(provider)
    if not sender:
        ok, detail = False, f'سرویس‌دهندهٔ ناشناخته: {provider}'
    else:
        try:
            ok, detail = sender['send'](to, text)
        except Exception as e:                      # noqa: BLE001 — هر خطای پنل نباید API را بیندازد
            ok, detail = False, f'{type(e).__name__}: {e}'
    if provider == 'console':
        log.info('[پیامک به %s] %s', to, text)
    SmsLog.objects.create(provider=provider, to=to, text=text, tag=tag or 'send', ok=ok,
                          detail=str(detail)[:500])
    return ok, detail


# ---------------- اطلاع‌رسانی‌های سفارش (پس‌زمینه) ----------------

def _async(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()


def notify_new_order(order):
    """پیامک ثبت سفارش: به مشتری (اگر فعال باشد) + به مدیر فروشگاه (اگر شماره داده شده باشد)"""
    total = _fmt_money(order.total)
    if settings.SMS_ORDER_TO_CUSTOMER:
        text = (f'{settings.SHOP_NAME}: سفارش {order.code} ثبت شد؛ '
                f'مبلغ {total} تومان. پیگیری: {settings.SHOP_URL}track?code={order.code}')
        _async(_safe_send, order.a_phone, text, 'order-customer')
    if settings.SHOP_NOTIFY_PHONE:
        text = (f'سفارش جدید {order.code}\nمبلغ: {total} تومان\n'
                f'{order.a_name} — {order.a_phone}\nاقلام: {order.items.count()} ردیف')
        _async(_safe_send, settings.SHOP_NOTIFY_PHONE, text, 'order-admin')


def notify_status_change(order, status_index):
    """پیامک تغییر وضعیت سفارش به مشتری"""
    if not settings.SMS_STATUS_TO_CUSTOMER:
        return
    label = pricing_status_label(status_index)
    text = f'{settings.SHOP_NAME}: وضعیت سفارش {order.code} به «{label}» تغییر کرد.'
    _async(_safe_send, order.a_phone, text, 'status-change')


def _safe_send(to, text, tag):
    try:
        send_sms(to, text, tag)
    except Exception:                                # noqa: BLE001 — اطلاع‌رسانی نباید خطا بدهد
        log.exception('خطای ارسال پیامک اطلاع‌رسانی')


def pricing_status_label(i):
    from .pricing import STATUS_LABELS
    return STATUS_LABELS[i] if 0 <= i < len(STATUS_LABELS) else 'نامشخص'
