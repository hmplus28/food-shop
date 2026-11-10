"""همگام‌سازی دادهٔ اولیه — محصولات همان کاتالوگ فرانت (app/src/data/catalog.js)

تا فرانت و بک‌اند روی «همان ۲۸ محصول با همان شناسه/قیمت» کار کنند.
صدا زدن ensure_seed() در /health و لیست محصولات؛ اگر جدول خالی بود یک‌بار پر می‌شود.
"""
import secrets

from django.conf import settings
from django.utils import timezone

from .models import Product, ShopUser

IMG = 'https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/'

BASE = [
    dict(id=1,  name='پسته اکبری ممتاز رفسنجان',        cat='pistachio',  img=IMG+'ec01895c5c0b.jpg',  price=1_980_000, weights=[250,500,1000,2000], stock=42, disc=10, grade='ممتاز',   rate=4.9, sold=1240, tags=['پرفروش','ممتاز'], sec=['best','amz'], desc='پسته اکبری درشت و خندار رفسنجان؛ بو داده با نمک دریا و کاملاً تازه. عالی برای مهمانی و شب یلدا.'),
    dict(id=2,  name='پسته احمدآقایی ممتاز',             cat='pistachio',  img=IMG+'f6d280936b47.jpg',  price=1_750_000, weights=[250,500,1000,2000], stock=38, disc=0,  grade='ممتاز',   rate=4.8, sold=980,  tags=['پرفروش'],        sec=['best'],       desc='پسته احمدآقایی باریک و خندان با مغز سبز تیره؛ محبوب‌ترین پسته برای پذیرایی.'),
    dict(id=3,  name='پسته فندقی بو داده',               cat='pistachio',  img=IMG+'e218521bb098.jpg',  price=1_450_000, weights=[250,500,1000,2000], stock=55, disc=5,  grade='درجه یک', rate=4.7, sold=760,  tags=[],               sec=['best'],       desc='پسته فندقی ریز و خوش‌مزه؛ مناسب عصرانه و تنقلات روزانه خانواده.'),
    dict(id=4,  name='مغز پسته سبز پرزدار',              cat='pistachio',  img=IMG+'99b54d43d43f.jpg',  price=2_950_000, weights=[250,500,1000],      stock=22, disc=0,  grade='ممتاز',   rate=4.9, sold=530,  tags=['ممتاز'],         sec=['best','new'], desc='مغز پسته سبز درجه یک برای شیرینی‌پزی، سالاد و پذیرایی؛ رنگ و طعم بی‌نظیر.'),
    dict(id=5,  name='بادام درختی خام (مامایی)',         cat='almond',     img=IMG+'5f3a2793e06f.jpg',  price=850_000,   weights=[250,500,1000,2000], stock=64, disc=0,  grade='درجه یک', rate=4.8, sold=1105, tags=['پرفروش'],        sec=['best'],       desc='بادام مامایی درشت و پوست‌کاغذی؛ تازه از باغ‌های سمنان و ارسنجان.'),
    dict(id=6,  name='بادام درختی بو داده نمکین',        cat='almond',     img=IMG+'c6b8b1936b7c.jpg',  price=920_000,   weights=[250,500,1000,2000], stock=47, disc=8,  grade='درجه یک', rate=4.7, sold=640,  tags=[],               sec=['amz'],        desc='بادام بو داده با نمک دریایی؛ روزانه تازه برشته می‌شود.'),
    dict(id=7,  name='بادام هندی شور',                   cat='ajil',       img=IMG+'eddf227382bb.png',  price=1_450_000, weights=[250,500,1000,2000], stock=51, disc=12, grade='درجه یک', rate=4.8, sold=1520, tags=['پرفروش'],        sec=['best','amz'], desc='بادام هندی درشت و کرمی با نمک متعادل؛ محبوب‌ترین مغز مهمانی.'),
    dict(id=8,  name='مغز گردو هفت‌پر تویسرکان',         cat='walnut',     img=IMG+'40ca66cd7225.webp', price=1_250_000, weights=[250,500,1000,2000], stock=36, disc=15, grade='ممتاز',   rate=4.9, sold=870,  tags=['پرفروش'],        sec=['best','amz'], desc='مغز گردو روشن و هفت‌پر بدون تلخی؛ سرشار از امگا۳.'),
    dict(id=9,  name='فندق خام درشت',                    cat='hazelnut',   img=IMG+'77db1fb48eed.jpg',  price=780_000,   weights=[250,500,1000,2000], stock=58, disc=0,  grade='درجه یک', rate=4.6, sold=690,  tags=[],               sec=['best'],       desc='فندق درشت اردبیل؛ خام و سالم، مناسب بو دادن خانگی و شکلات‌سازی.'),
    dict(id=10, name='تخمه کدو گوشتی بو داده',           cat='seeds',      img=IMG+'5675e680be54.jpg',  price=920_000,   weights=[250,500,1000,2000], stock=44, disc=10, grade='درجه یک', rate=4.8, sold=930,  tags=['پرفروش'],        sec=['best','amz'], desc='تخمه کدو گوشتی سبز و بدون پوست با نمک کم؛ میان‌وعده‌ای سالم برای همه سنین.'),
    dict(id=11, name='مغز تخمه آفتابگردان',              cat='seeds',      img=IMG+'397a7c914638.png',  price=690_000,   weights=[250,500,1000,2000], stock=70, disc=0,  grade='درجه یک', rate=4.5, sold=410,  tags=[],               sec=['new'],        desc='مغز تخمه آفتابگردان تمیز و تازه؛ برای سالاد، نان و آشپزی.'),
    dict(id=12, name='تخمه ژاپنی نمکین',                 cat='seeds',      img=IMG+'bacd7f52d5e8.jpg',  price=290_000,   weights=[250,500,1000,2000], stock=88, disc=5,  grade='درجه یک', rate=4.4, sold=1240, tags=[],               sec=[],             desc='تخمه ژاپنی خوش‌بهر با نمک لیمویی؛ همراه همیشگی دورهمی‌ها.'),
    dict(id=13, name='انجیر خشک استهبان ممتاز',          cat='mulberryfig',img=IMG+'7b3e238840f4.jpeg', price=640_000,   weights=[250,500,1000,2000], stock=40, disc=10, grade='ممتاز',   rate=4.9, sold=540,  tags=['ممتاز'],         sec=['new','amz'],  desc='انجیر خشک استهبان با گلوی سفید و شیرینی طبیعی؛ چیده‌شده از باغ‌های فارس.'),
    dict(id=14, name='توت خشک سفید درشت',                cat='mulberryfig',img=IMG+'83e1a888b37f.jpg',  price=720_000,   weights=[250,500,1000,2000], stock=33, disc=0,  grade='ممتاز',   rate=4.8, sold=470,  tags=[],               sec=['new'],        desc='توت خشک سفید درشت و پرشیرینی؛ جایگزین سالم قند کنار چای.'),
    dict(id=15, name='کشمش سبز قلمی ملایم',              cat='raisin',     img=IMG+'184fecd2458a.jpg',  price=380_000,   weights=[250,500,1000,2000], stock=76, disc=8,  grade='درجه یک', rate=4.7, sold=810,  tags=[],               sec=['new'],        desc='کشمش سبز قلمی با شیرینی ملایم؛ عالی برای پلئو، شیرینی و میان‌وعده.'),
    dict(id=16, name='مویز بدون هسته (کشمش سیاه)',       cat='raisin',     img=IMG+'1e147cae76b8.jpg',  price=420_000,   weights=[250,500,1000,2000], stock=62, disc=0,  grade='ممتاز',   rate=4.8, sold=520,  tags=[],               sec=['new'],        desc='مویز تیره و آفتابی بدون هسته؛ سرشار از آهن و انرژی طبیعی.'),
    dict(id=17, name='کشمش پلویی طلایی',                 cat='raisin',     img=IMG+'aa25c7492bb4.jpg',  price=260_000,   weights=[250,500,1000,2000], stock=90, disc=5,  grade='درجه یک', rate=4.5, sold=1150, tags=[],               sec=[],             desc='کشمش پلویی روشن و کم‌شیرین؛ انتخاب اول قابلمه‌های ایرانی.'),
    dict(id=18, name='خرما پیارم ممتاز حصکوه',           cat='date',       img=IMG+'fb2be35ef680.jpeg', price=890_000,   weights=[250,500,1000,2000], stock=29, disc=10, grade='ممتاز',   rate=4.9, sold=640,  tags=['ممتاز'],         sec=['new','amz'],  desc='خرما پیارم درشت و مرطوب با شیرینی کاراملی؛ لقب «خرمای شاهانه» را دارد.'),
    dict(id=19, name='خرمای مضافتی بم',                  cat='date',       img=IMG+'42f5d4b9754e.jpg',  price=320_000,   weights=[250,500,1000,2000], stock=96, disc=12, grade='درجه یک', rate=4.8, sold=1980, tags=['پرفروش'],        sec=['amz'],        desc='خرمای مضافتی تازه و مرطوب بم؛ شیرین، نرم و محبوب همه.'),
    dict(id=20, name='برگه زردآلو آفتابی',               cat='dryfruit',   img=IMG+'b2f2d1414a8d.jpg',  price=560_000,   weights=[250,500,1000,2000], stock=37, disc=0,  grade='ممتاز',   rate=4.7, sold=380,  tags=[],               sec=['new'],        desc='برگه زردآلو خشک‌شده زیر آفتاب بدون افزودن شکر؛ ترش و شیرین طبیعی.'),
    dict(id=21, name='آلو خشک بخارا',                    cat='dryfruit',   img=IMG+'3cb5b008199c.jpg',  price=340_000,   weights=[250,500,1000,2000], stock=54, disc=5,  grade='درجه یک', rate=4.6, sold=760,  tags=[],               sec=[],             desc='آلو بخارای آبدار و گوشت‌دار؛ برای خورشت، پلئو و میان‌وعده.'),
    dict(id=22, name='چیپس میوه مخلوط بدون قند',         cat='dryfruit',   img=IMG+'f668152a2bcf.png',  price=480_000,   weights=[250,500,1000],      stock=31, disc=15, grade='درجه یک', rate=4.6, sold=290,  tags=[],               sec=['new','amz'],  desc='چیپس سیب، هلو و موز خشک‌شده بدون قند افزودنی؛ اسنک سالم بچه‌ها.'),
    dict(id=23, name='میوه خشک مخلوط مهمانی',            cat='dryfruit',   img=IMG+'4aa5a36466e4.jpg',  price=620_000,   weights=[250,500,1000,2000], stock=48, disc=0,  grade='ممتاز',   rate=4.8, sold=450,  tags=[],               sec=['new'],        desc='ترکیبی رنگارنگ از برگه‌ها و میوه‌های خشک؛ پذیرایی متفاوت و سالم.'),
    dict(id=24, name='آجیل مخلوط شور (پنج‌مغز)',         cat='ajil',       img=IMG+'66fd0cba7ee8.jpg',  price=1_680_000, weights=[250,500,1000,2000], stock=26, disc=10, grade='ممتاز',   rate=4.9, sold=2100, tags=['پرفروش'],        sec=['best','amz'], desc='پسته، بادام، فندق، مغز گردو و بادام هندی؛ با نسبت طلایی و تازه بو داده.'),
    dict(id=25, name='آجیل مخلوط شیرین چهارمغز',         cat='ajil',       img=IMG+'ca78178474b1.png',  price=1_590_000, weights=[250,500,1000,2000], stock=34, disc=0,  grade='ممتاز',   rate=4.7, sold=380,  tags=[],               sec=['best'],       desc='مغزهای بدون نمک برای بارداری، رژیم و ورزشکاران؛ ترکیب متعادل چهار مغز.'),
    dict(id=26, name='زعفران سرگل ممتاز قائنات',         cat='saffron',    img=IMG+'2c259b7044c5.jpg',  price=165_000_000, weights=[2,5,10,25],       stock=60, disc=5,  grade='ممتاز',   rate=5.0, sold=340,  tags=['ممتاز'],         sec=['new'],        desc='زعفران سرگل درجه یک قائنات با رنگ‌دهی فوق‌العاده؛ بسته‌بندی شکستنی با پلمپ.'),
    dict(id=27, name='دمنوش گل گاوزبان و سنبل‌الطیب',    cat='tea',        img=IMG+'36eff119ff2f.jpg',  price=380_000,   weights=[100,250,500],       stock=65, disc=0,  grade='درجه یک', rate=4.8, sold=420,  tags=[],               sec=['new'],        desc='دمنوش آرام‌بخش با گل گاوزبان، سنبل‌الطیب و اسطوخودوس؛ آرامش شبانه.'),
    dict(id=28, name='دمنوش آرامش (به‌لیمو و گل محمدی)', cat='tea',        img=IMG+'e5e69256f8fd.jpg',  price=420_000,   weights=[100,250,500],       stock=52, disc=10, grade='درجه یک', rate=4.7, sold=260,  tags=[],               sec=['amz'],        desc='ترکیب معطر به‌لیمو، گل محمدی و بهارنارنج؛ نوشیدنی برگزیده عصرها.'),
]


def seed_products(force=False):
    """درج ۲۸ محصول پایه (فقط وقتی جدول خالی است؛ با force همه بازنویسی می‌شوند)"""
    if force:
        Product.objects.all().delete()
    elif Product.objects.exists():
        return False
    Product.objects.bulk_create([Product(**p) for p in BASE], batch_size=50)
    return True


def ensure_admin():
    """ساخت/به‌روزرسانی حساب مدیر فروشگاه از env (ADMIN_USERNAME/ADMIN_PASSWORD)"""
    user = ShopUser.objects.filter(username=settings.ADMIN_USERNAME).first()
    if user is None:
        user = ShopUser.objects.filter(phone=settings.ADMIN_PHONE).first()
    created = user is None
    if created:
        user = ShopUser(username=settings.ADMIN_USERNAME, phone=settings.ADMIN_PHONE)
    user.name = user.name or 'مدیر فروشگاه'
    user.role = 'admin'
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    if created or not user.check_password(settings.ADMIN_PASSWORD):
        user.set_password(settings.ADMIN_PASSWORD)
    user.save()
    return user, created


def ensure_seed():
    """ایمن برای صدا زدن در هر درخواست — فقط بار اول کاری می‌کند"""
    seeded = seed_products()
    if seeded:
        ensure_admin()
    return seeded


def seed_all():
    """دستور مدیریتی: محصول + مدیر + گزارش"""
    p = seed_products()
    admin, created = ensure_admin()
    return {
        'products_seeded': p,
        'products_total': Product.objects.count(),
        'admin_created': created,
        'admin_phone': admin.phone,
        'admin_username': admin.username,
        'at': timezone.now().isoformat(),
        'dev_password_hint': f'{settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD} (از .env عوض کنید)',
        'secret_sample': secrets.token_hex(4),
    }
