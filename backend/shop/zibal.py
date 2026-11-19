"""درگاه پرداخت زیبال (IPG نسخهٔ v1) — فقط کتابخانهٔ استاندارد

اصول امنیتی:
- مبلغ از «جمع سفارش» ذخیره‌شده در سرور می‌آید (تومان × ۱۰ = ریال)؛ هرگز از کلاینت.
- نتیجهٔ پرداخت را فقط verify سرور به سرور تعیین می‌کند؛ پارامترهای callback مرورگر اعتبار ندارند.
- در verify، مبلغ و orderId پاسخ درگاه باید دقیقاً با سفارش یکی باشند وگرنه پرداخت پذیرفته نمی‌شود.
- کد مرچنت هرگز در لاگ/پاسخ نمی‌آید.

نکته: مسیرها و فیلدها مطابق مستندات رسمی IPG زیبال (OpenAPI): POST /v1/request ، GET /start/{trackId} (نیازمند Referer
هم‌دامنهٔ ثبت‌شده؛ مرورگر خودکار می‌فرستد)، POST /v1/verify. آدرس پایه با ZIBAL_BASE قابل تغییر است.
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

log = logging.getLogger('shop')

_REQUEST_ERRORS = {
    102: 'کد پذیرندهٔ زیبال پیدا نشد (merchant نامعتبر است)',
    103: 'کد پذیرندهٔ زیبال غیرفعال است',
    104: 'کد پذیرندهٔ زیبال نامعتبر است',
    105: 'مبلغ باید حداقل ۱٬۰۰۰ ریال (۱۰۰ تومان) باشد',
    115: 'IP سرور در پنل زیبال ثبت نشده است',
    140: 'آدرس بازگشت (callback) ارسال نشده است',
    106: 'آدرس بازگشت (callback) نامعتبر است یا با دامنهٔ ثبت‌شده در زیبال یکی نیست',
    113: 'مبلغ از سقف تراکنش بیشتر است',
}
_VERIFY_ERRORS = {
    202: 'سفارش پرداخت نشده یا ناموفق بوده است',
    203: 'شناسهٔ تراکنش نامعتبر است',
    115: 'IP سرور در پنل زیبال ثبت نشده است',
    103: 'درگاه زیبال غیرفعال است',
}


def enabled():
    return bool(settings.ZIBAL_MERCHANT)


def _base():
    return (settings.ZIBAL_BASE or 'https://gateway.zibal.ir').rstrip('/')


def start_url(track_id):
    return f'{_base()}/start/{track_id}'


def _post(path, body):
    req = urllib.request.Request(_base() + path, data=json.dumps(body).encode('utf-8'), method='POST',
                                 headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode('utf-8'))
        except Exception:                                    # noqa: BLE001
            return {'result': -1, 'message': f'HTTP {e.code}'}
    except Exception as e:                                   # noqa: BLE001
        log.error('اتصال به زیبال ناموفق: %s', type(e).__name__)
        return None


def request_payment(amount_toman, callback_url, description, order_id, mobile=''):
    """ساخت تراکنش → (trackId, None) یا (None, پیام فارسی)"""
    body = {'merchant': settings.ZIBAL_MERCHANT, 'amount': int(amount_toman) * 10, 'callbackUrl': callback_url,
            'description': description[:200], 'orderId': order_id}
    if mobile:
        body['mobile'] = mobile
    resp = _post('/v1/request', body)
    if resp is None:
        return None, 'اتصال به درگاه پرداخت برقرار نشد؛ دوباره تلاش کنید'
    if resp.get('result') == 100 and resp.get('trackId'):
        return str(resp['trackId']), None
    return None, _REQUEST_ERRORS.get(resp.get('result')) or resp.get('message') or 'خطا در ارتباط با درگاه پرداخت'


def verify(amount_toman, track_id, order_id):
    """تأیید تراکنش → (موفق?, ref_number, پیام). نتیجهٔ ۱۰۰ و ۲۰۱ (قبلاً تأیید شده) موفق‌اند؛
    ولی فقط اگر مبلغ و orderId پاسخ با سفارش بخواند."""
    resp = _post('/v1/verify', {'merchant': settings.ZIBAL_MERCHANT, 'trackId': int(track_id) if str(track_id).isdigit() else track_id})
    if resp is None:
        return False, '', 'اتصال به درگاه برای تأیید پرداخت برقرار نشد'
    if resp.get('result') in (100, 201):
        try:
            paid = int(resp.get('amount'))
        except (TypeError, ValueError):
            return False, '', 'مبلغ تأییدشده از درگاه خوانده نشد'
        if resp.get('status') not in (None, 1):
            return False, '', 'پرداخت نهایی نشده است'
        if paid != int(amount_toman) * 10:
            log.error('عدم تطابق مبلغ پرداخت: سفارش %s', order_id)
            return False, '', 'مبلغ پرداخت‌شده با مبلغ سفارش یکی نیست'
        if resp.get('orderId') is not None and str(resp.get('orderId')) != str(order_id):
            log.error('عدم تطابق orderId پرداخت: سفارش %s', order_id)
            return False, '', 'تراکنش متعلق به این سفارش نیست'
        return True, str(resp.get('refNumber') or ''), None
    return False, '', _VERIFY_ERRORS.get(resp.get('result')) or resp.get('message') or 'پرداخت تأیید نشد'
