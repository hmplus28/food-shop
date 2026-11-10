"""قواعد قیمت‌گذاری و تخفیف — ترجمهٔ دقیق منطق فرانت (app/src/stores/cart.js و data/catalog.js)

مهم: round در جاوااسکریپت نیم‌بالا است ولی round پایتون بانکی؛
برای هم‌خوانی قیمت‌ها با فرانت از js_round استفاده می‌کنیم.
"""
import math

FREE_SHIP = 1_500_000          # سقف ارسال رایگان (تومان)
MAX_QTY_PER_LINE = 20          # سقف تعداد هر ردیف — همان سقف سبد فرانت

SHIP_OPTIONS = {
    'peyk':  {'cost': 89_000,  'label': 'پیک فوری (تهران)',        'days': 'همان روز'},
    'post':  {'cost': 59_000,  'label': 'پست پیشتاز (سراسر کشور)', 'days': '۲ تا ۴ روز کاری'},
    'tipax': {'cost': 99_000,  'label': 'تیپاکس (سراسر کشور)',     'days': '۱ تا ۳ روز کاری'},
}
DEFAULT_SHIP = 'peyk'

COUPONS = {
    'WELCOME10': {'type': 'pct',  'val': 10, 'min': 500_000, 'first': True,  'label': '۱۰٪ تخفیف اولین خرید (حداقل ۵۰۰٬۰۰۰ تومان)'},
    'LUCK5':     {'type': 'pct',  'val': 5,  'min': 0,                        'label': '۵٪ تخفیف کارت شانس'},
    'LUCK20':    {'type': 'pct',  'val': 20, 'min': 300_000,                  'label': '۲۰٪ تخفیف طلایی (حداقل ۳۰۰٬۰۰۰ تومان)'},
    'NEXT15':    {'type': 'pct',  'val': 15, 'min': 0,                        'label': '۱۵٪ تخفیف خرید بعدی'},
    'SHIP0':     {'type': 'ship', 'val': 0,  'min': 0,                        'label': 'ارسال رایگان'},
    'CASH50':    {'type': 'cash', 'val': 50_000, 'min': 300_000,              'label': '۵۰٬۰۰۰ تومان اعتبار (حداقل ۳۰۰٬۰۰۰ تومان)'},
    'SAMEDAY':   {'type': 'day',  'val': 0,  'min': 0,                        'label': 'اولویت ارسال همان روز'},
}

STATUS_LABELS = ['در حال ثبت', 'در حال آماده‌سازی', 'در مسیر ارسال', 'تحویل شده']


def js_round(x):
    """گرد کردن مثل Math.round جاوااسکریپت (نیم‌بالا)"""
    return int(math.floor(x + 0.5))


def line_unit_price(product, w):
    """قیمت واحد یک ردیف — همان priceOf فرانت:
    پایه = قیمت × وزن ÷ ۱۰۰۰ و در صورت تخفیف، گرد به هزار تومان پایین."""
    base = js_round(product.price * w / 1000)
    if product.disc:
        base = js_round(base * (100 - product.disc) / 100 / 1000) * 1000
    return base


def coupon_effect(code, sub, first_order):
    """اعتبارسنجی و اثر کد تخفیف → (off, ship_free, error_msg)
    خطا → (0, False, پیام فارسی)"""
    code = (code or '').strip().upper()
    if not code:
        return 0, False, None
    rule = COUPONS.get(code)
    if not rule:
        return 0, False, 'کد تخفیف نامعتبر است'
    if rule.get('first') and not first_order:
        return 0, False, 'کد WELCOME10 فقط برای اولین خرید است'
    if sub < rule.get('min', 0):
        return 0, False, 'مبلغ سفارش برای این کد تخفیف کافی نیست'
    t = rule['type']
    if t == 'pct':
        return js_round(sub * rule['val'] / 100), False, None
    if t == 'cash':
        return min(rule['val'], sub), False, None
    if t == 'ship':
        return 0, True, None
    return 0, False, None     # نوع day (SAMEDAY) اثر مالی ندارد


def compute_order(items, coupon, ship_type, first_order):
    """محاسبهٔ نهایی سفارش از اقلام معتبر.

    items: list of (product, w, qty) — اعتبارسنجی وزن/تعداد در ویو انجام شده است.
    خروجی dict با همهٔ فیلدهای مالی؛ خطای کد تخفیف/ارسال با ValueError فارسی برمی‌گردد.
    """
    ship_type = (ship_type or DEFAULT_SHIP).strip()
    if ship_type not in SHIP_OPTIONS:
        raise ValueError('روش ارسال نامعتبر است')

    sub = 0
    for product, w, qty in items:
        sub += line_unit_price(product, w) * qty

    off, ship_free, err = coupon_effect(coupon, sub, first_order)
    if err:
        raise ValueError(err)

    opt = SHIP_OPTIONS[ship_type]
    ship_cost = 0 if (sub >= FREE_SHIP or ship_free) else opt['cost']
    total = max(0, sub - off + ship_cost)

    return {
        'sub': sub, 'off': off, 'coupon': (coupon or '').strip().upper(),
        'ship_cost': ship_cost, 'ship_type': ship_type,
        'ship_label': opt['label'], 'ship_days': opt['days'],
        'total': total,
    }
