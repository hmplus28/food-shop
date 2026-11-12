"""محصولات «مجازی» برای پک‌ها و خرید اطمینان

پک و کالای خرید اطمینان قیمت خودشان را دارند؛ برای اینکه سبد/سفارش/موجودی/قیمت سمت سرور مثل بقیهٔ کالاها
کار کند، هر کدام یک محصول پنهان (hide=True، وزن [۱]) دارند که با تغییر مدیر همگام می‌شود.
قیمت محصول = تومان × ۱۰۰۰ (چون قیمت واحد = price × وزن ÷ ۱۰۰۰ و وزن ۱ است).
"""
from django.db.models import Max

MARK = '__virtual'


def next_product_id(Product):
    return max(100, Product.objects.aggregate(m=Max('id'))['m'] or 0) + 1


def sync_virtual(Product, pid, *, name, image, price, stock, active, kind):
    """ساخت/به‌روزرسانی محصول مجازی؛ شناسهٔ آن را برمی‌گرداند. غیرفعال = موجودی صفر (قابل سفارش نیست)"""
    p = Product.objects.filter(pk=pid).first() if pid else None
    if p is None:
        p = Product(id=next_product_id(Product))
    p.name = name
    p.cat = 'giftbox'
    p.img = image or ''
    p.price = int(price) * 1000
    p.weights = [1]
    p.stock = int(stock) if active else 0
    p.disc = 0
    p.grade = kind
    p.hide = True
    p.sec = [MARK]
    p.tags = [kind]
    p.desc = p.desc or f'{kind}؛ قیمت ویژه'
    p.save()
    return p.id


def drop_virtual(Product, pid):
    if pid:
        Product.objects.filter(pk=pid).delete()
