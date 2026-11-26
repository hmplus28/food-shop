"""سید یک‌بارمصرف کالاهای خواربار (روغن، تن‌ماهی، چای، رب، زعفران و زرشک)

اجرا روی هاست:  python manage.py seed_grocery
(از طریق deploy.sh:  bash deploy.sh --manage seed_grocery )

- ایمپوتنت: اجرای دوباره چیزی را دوباره نمی‌سازد و گزارش می‌دهد.
- تصاویر از پوشهٔ shop/seed_media/ (در ریپو) به MEDIA_ROOT کپی می‌شود با نام
  ۱۲هگزِ قطعی (مشتق از نام فایل) و ردیف MediaFile هم ساخته می‌شود تا از
  /api/v1/media/<name> سرو شود و پنل ادمین هم در کتابخانهٔ تصاویر ببیندش.
- قیمت ۰ یعنی «تماس بگیرید» — فرانت برای این محصولات دکمهٔ خرید را به تماس تبدیل می‌کند.
- محصولات در ریل «پرفروش‌ترین‌ها» صفحهٔ اصلی هم نمایش داده می‌شوند (sec=best).
- روش ارسال «تحویل حضوری» (hadir) هم اگر نبود ساخته می‌شود (هزینهٔ صفر).
"""
import shutil
from pathlib import Path

from django.conf import settings

from .models import MediaFile, NavCat, Product, ShippingMethod

MEDIA_SRC = Path(__file__).resolve().parent / 'seed_media'

# (اسلاگ تصویر، نام دستهٔ منو، آیکن، زیرشاخه‌ها)
GROCERY_CATS = [
    ('oil-cook', 'روغن پخت و پز', 'i-box', ['روغن مایع', 'حلب ۵ کیلویی', 'روغن نیمه‌جامد']),
    ('oil-fry', 'روغن سرخ کردنی', 'i-fire', ['۵ لیتری', '۳ لیتری', 'روغن مخصوص سرخ‌کردنی']),
    ('canned', 'تن ماهی و کنسرو', 'i-box', ['تن ماهی', 'کنسرو', 'رب و کنسروات']),
    ('chai', 'چای', 'i-leaf', ['چای عطری', 'چای ساده', 'چای کیسه‌ای']),
    ('rab', 'رب و سس', 'i-box', ['رب گوجه', 'رب خانگی', 'سس']),
]

# (اسلاگ، نام، دسته، قیمت تومان، واحد، توضیح) — قیمت ۰ = تماس بگیرید
# unit: piece = بسته/عدد (وزن [1]) ، kg = کیلویی با وزن‌های انتخابی
GROCERY_PRODUCTS = [
    ('halab-ghonche',   'روغن حلب غنچه ۵ کیلویی',            'oil-cook', 2_050_000, 'piece', 'روغن حلب غنچه مخصوص پخت و پز، قوطی ۵ کیلویی اقتصادی؛ مناسب قابلمه‌های بزرگ و آشپزخانه‌های پرجمعیت.'),
    ('tabarrok-oil',    'روغن مایع تبرک ۵ لیتری',            'oil-cook', 1_680_000, 'piece', 'روغن مایع تبرّک پخت و پز، گالن ۵ لیتری؛ سبک و کم‌اسانس برای پخت روزانه.'),
    ('rana-oil',        'روغن مایع رعنا ۵ لیتری',            'oil-cook', 1_670_000, 'piece', 'روغن مایع رعنا، گالن ۵ لیتری؛ پخت‌وپز سبک با طعم طبیعی.'),
    ('ladan-oil',       'روغن لادن ۳ لیتری پخت و پز',        'oil-cook', 1_170_000, 'piece', 'روغن لادن مخصوص پخت و پز، قوطی ۳ لیتری؛ اقتصادی و مناسب مصرف خانوار.'),
    ('tabarrok-fry',    'روغن سرخ کردنی تبرک ۵ لیتری',       'oil-fry',  1_750_000, 'piece', 'روغن سرخ‌کردنی تبرک، گالن ۵ لیتری؛ مقاوم در حرارت بالا و کم‌کف برای سرخ کردن عمیق.'),
    ('rana-fry5',       'روغن سرخ کردنی رعنا ۵ لیتری',       'oil-fry',  1_780_000, 'piece', 'روغن سرخ‌کردنی مخصوص رعنا، گالن ۵ لیتری؛ برای سرخ کردن طولانی و قابلمهٔ باز.'),
    ('rana-fry3',       'روغن سرخ کردنی رعنا ۳ لیتری',       'oil-fry',  1_150_000, 'piece', 'روغن سرخ‌کردنی رعنا، قوطی ۳ لیتری؛ اندازهٔ مناسب مصرف هفتگی.'),
    ('shidan-tuna',     'تن ماهی شیدان',                     'canned',     280_000, 'piece', 'تن ماهی شیدان با روغن گیاهی، قوطی ۱۸۰ گرمی؛ گوشت سفید و تمیز.'),
    ('shilton-tuna',    'تن ماهی شیلتون',                    'canned',           0, 'piece', 'تن ماهی شیلتون، قوطی استاندارد؛ برای استعلام قیمت روز با فروشگاه تماس بگیرید.'),
    ('ladan-tuna',      'تن ماهی لادن',                      'canned',           0, 'piece', 'تن ماهی لادن، قوطی استاندارد؛ برای استعلام قیمت روز با فروشگاه تماس بگیرید.'),
    ('shahrzad-atri',   'چای شهرزاد عطری',                   'chai',      950_000, 'piece', 'چای سیاه شهرزاد عطری، بستهٔ بزرگ؛ عطر بهار نارنج و رنگ دیرگذر.'),
    ('shahrzad-sade',   'چای شهرزاد ساده',                   'chai',      900_000, 'piece', 'چای سیاه شهرزاد ساده، بستهٔ بزرگ؛ طعم اصیل بدون عطرافزوده.'),
    ('hamedanian-rab',  'رب گوجه همدانیان',                  'rab',       310_000, 'piece', 'رب گوجه‌فرنگی همدانیان، قوطی استاندارد؛ گوجه رسید هفت‌گلاب با رنگ طبیعی.'),
    ('rana-rab',        'رب گوجه رعنا',                      'rab',             0, 'piece', 'رب گوجه‌فرنگی رعنا؛ برای استعلام قیمت روز با فروشگاه تماس بگیرید.'),
    ('tabarrok-rab',    'رب گوجه تبرک',                      'rab',             0, 'piece', 'رب گوجه‌فرنگی تبرک؛ برای استعلام قیمت روز با فروشگاه تماس بگیرید.'),
    ('saffron-powder',  'پودر زعفران ۱ کیلویی',              'saffron', 1_100_000, 'piece', 'پودر زعفران بستهٔ ۱ کیلویی؛ برای صنفی‌ها و کاربرد صنعتی شیرینی و نان.'),
    ('afras-saffron',   'زعفران درجه ۱ افراس',               'saffron', 1_890_000, 'piece', 'زعفران درجه یک بسته‌بندی افراس؛ رنگ و عطر تضمینی با پلمپ اصالت.'),
    ('ghaenat-saffron', 'زعفران قائنات',                     'saffron', 1_150_000, 'piece', 'زعفران اصیل قائنات، بستهٔ اقتصادی؛ انتخاب مطمئن برای مصرف روزانه.'),
    ('pofaki-barberry', 'زرشک پفکی صادراتی',                 'saffron',   980_000, 'kg',    'زرشک پفکی صادراتی درجه یک؛ قرمز، ترد و بدون دانه؛ مناسب پلئو و صادرات.'),
]

HADIR = dict(key='hadir', label='تحویل حضوری در فروشگاه', cost=0,
             days='هماهنگی تلفنی', hint='بدون هزینهٔ ارسال؛ سفارش را از فروشگاه تحویل بگیرید',
             active=True, sort=99)


def _hex12(seed: str) -> str:
    import hashlib
    return hashlib.md5(seed.encode()).hexdigest()[:12]


def ensure_images() -> dict:
    """کپی تصاویر ریپو → MEDIA_ROOT با نام ۱۲هگز قطعی + ردیف MediaFile"""
    _os = __import__('os')
    _os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    out = {'new': 0, 'kept': 0}
    for f in sorted(MEDIA_SRC.glob('*.jpg')):
        name = _hex12(f.stem) + '.jpg'
        dst = Path(settings.MEDIA_ROOT) / name
        if dst.exists() and dst.stat().st_size > 0:
            out['kept'] += 1
        else:
            shutil.copyfile(f, dst)
            out['new'] += 1
        MediaFile.objects.get_or_create(name=name, defaults=dict(original=f'grocery-{f.stem}.jpg', size=dst.stat().st_size))
    return out


def ensure_categories() -> dict:
    out = {'new': 0, 'kept': 0}
    base = NavCat.objects.order_by('-sort').first()
    start = (base.sort + 1) if base else 0
    for i, (slug, name, icon, subs) in enumerate(GROCERY_CATS):
        _, created = NavCat.objects.get_or_create(
            slug=slug,
            defaults=dict(name=name, icon=icon, subs=subs, feat_img='', feat_title='', feat_sub='',
                          sort=start + i, active=True))
        out['new' if created else 'kept'] += 1
    return out


def ensure_products() -> dict:
    out = {'new': [], 'kept': 0, 'home_updated': 0}
    for slug, name, cat, price, unit, desc in GROCERY_PRODUCTS:
        img = 'media/' + _hex12(slug) + '.jpg'
        p = Product.objects.filter(name=name).first()
        if p:
            out['kept'] += 1
            if 'best' not in (p.sec or []):        # نمایش در ریل «پرفروش‌ترین‌ها» صفحهٔ اصلی
                p.sec = list(p.sec or []) + ['best']
                p.save(update_fields=['sec'])
                out['home_updated'] += 1
            continue
        Product.objects.create(
            name=name, cat=cat, img=img, price=price, unit=unit,
            weights=[1] if unit != 'kg' else [250, 500, 1000],
            stock=30, disc=0, grade='درجه یک', rate=4.6, sold=0,
            tags=['خواربار'], sec=['best'], desc=desc, hide=False)
        out['new'].append(name)
    return out


def ensure_hadir_shipping() -> bool:
    _, created = ShippingMethod.objects.get_or_create(key=HADIR['key'], defaults=HADIR)
    return created


def seed_grocery() -> dict:
    imgs = ensure_images()
    cats = ensure_categories()
    prods = ensure_products()
    hadir = ensure_hadir_shipping()
    return {'images': imgs, 'categories': cats, 'products': prods, 'hadir_created': hadir,
            'products_total': Product.objects.count()}
