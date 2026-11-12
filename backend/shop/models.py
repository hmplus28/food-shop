"""مدل‌های فروشگاه خانم گل

طراحی بر اساس قرارداد فرانت (app/src/services/api.js):
- شناسهٔ محصولات عددی است تا فرانت مستقیم همان id را بخواند.
- سفارش کد یکتا دارد (KG-xxxxx) و «کد سمت مرورگر» هم برای همگام‌سازی نگه داشته می‌شود.
- تنظیمات ظاهری سایت (تم/رنگ) در SiteSetting ذخیره می‌شود تا برای همهٔ بازدیدکنندگان یکسان باشد.
"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class ShopUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone, name='', password=None, **extra):
        if not phone:
            raise ValueError('شماره موبایل الزامی است')
        user = self.model(phone=phone, name=name or 'کاربر', **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, name='مدیر', password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'admin')
        return self.create_user(phone, name, password, **extra)


class ShopUser(AbstractBaseUser, PermissionsMixin):
    """کاربر فروشگاه — ثبت‌نام و ورود با شماره موبایل و رمز عبور"""
    ROLE = [('user', 'کاربر'), ('admin', 'مدیر')]

    phone = models.CharField('موبایل', max_length=15, unique=True, db_index=True)
    name = models.CharField('نام و نام خانوادگی', max_length=120, blank=True, default='کاربر')
    username = models.CharField('نام کاربری (اختیاری)', max_length=60, unique=True, null=True, blank=True)
    role = models.CharField('نقش', max_length=10, choices=ROLE, default='user')
    is_active = models.BooleanField('فعال', default=True)
    is_staff = models.BooleanField('دسترسی ادمین جنگو', default=False)
    date_joined = models.DateTimeField('تاریخ عضویت', auto_now_add=True)

    objects = ShopUserManager()
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return f'{self.name} ({self.phone})'

    @property
    def public(self):
        return {'name': self.name, 'phone': self.phone, 'role': self.role}


class Product(models.Model):
    """محصول — ساختار فیلدها دقیقاً همان چیزی است که فرانت normalize می‌کند"""
    name = models.CharField('نام', max_length=200)
    cat = models.CharField('دسته', max_length=40, db_index=True)
    img = models.CharField('تصویر (URL)', max_length=500, blank=True, default='')
    price = models.BigIntegerField('قیمت پایه هر کیلو/عدد (تومان)')
    weights = models.JSONField('وزن‌های مجاز (گرم)', default=list)
    stock = models.IntegerField('موجودی', default=0)
    disc = models.IntegerField('تخفیف ٪', default=0)
    grade = models.CharField('درجه', max_length=60, blank=True, default='درجه یک')
    rate = models.FloatField('امتیاز', default=4.5)
    sold = models.IntegerField('فروش', default=0)
    tags = models.JSONField('برچسب‌ها', default=list)
    sec = models.JSONField('بخش‌های صفحهٔ اصلی', default=list)
    desc = models.TextField('توضیحات', blank=True, default='')
    hide = models.BooleanField('پنهان از فروشگاه', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['id']

    def __str__(self):
        return f'{self.id}. {self.name}'


class Order(models.Model):
    """سفارش — وضعیت: ۰ در حال ثبت، ۱ در حال آماده‌سازی، ۲ در مسیر ارسال، ۳ تحویل شده"""
    code = models.CharField('کد سفارش', max_length=20, unique=True, db_index=True)
    client_code = models.CharField('کد سمت مرورگر', max_length=20, blank=True, default='')
    user = models.ForeignKey(ShopUser, verbose_name='کاربر', null=True, blank=True,
                             on_delete=models.SET_NULL, related_name='orders')
    status = models.PositiveSmallIntegerField('وضعیت', default=0)
    sub = models.BigIntegerField('جمع کالاها', default=0)
    off = models.BigIntegerField('تخفیف', default=0)
    coupon = models.CharField('کد تخفیف', max_length=40, blank=True, default='')
    ship_cost = models.BigIntegerField('هزینهٔ ارسال', default=0)
    ship_type = models.CharField('نوع ارسال', max_length=20, default='peyk')
    ship_label = models.CharField('برچسب ارسال', max_length=120, blank=True, default='')
    ship_days = models.CharField('زمان ارسال', max_length=60, blank=True, default='')
    total = models.BigIntegerField('قابل پرداخت', default=0)
    a_name = models.CharField('نام گیرنده', max_length=120)
    a_phone = models.CharField('موبایل گیرنده', max_length=15, db_index=True)
    a_prov = models.CharField('استان', max_length=60, blank=True, default='')
    a_city = models.CharField('شهر', max_length=60, blank=True, default='')
    a_addr = models.TextField('آدرس پستی')
    note = models.TextField('توضیح سفارش', blank=True, default='')
    created_at = models.DateTimeField('زمان ثبت', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.code


class OrderItem(models.Model):
    """اقلام سفارش — اسنپ‌شات نام/قیمت لحظهٔ خرید (حذف محصول سفارش را خراب نمی‌کند)"""
    order = models.ForeignKey(Order, verbose_name='سفارش', related_name='items', on_delete=models.CASCADE)
    pid = models.IntegerField('شناسه محصول')
    name = models.CharField('نام محصول', max_length=200)
    img = models.CharField('تصویر', max_length=500, blank=True, default='')
    w = models.IntegerField('وزن (گرم؛ ۱=عدد)')
    qty = models.IntegerField('تعداد')
    unit_price = models.BigIntegerField('قیمت واحد')
    cost = models.BigIntegerField('جمع ردیف')

    class Meta:
        verbose_name = 'قلم سفارش'
        verbose_name_plural = 'اقلام سفارش‌ها'


class SiteSetting(models.Model):
    """تنظیمات سراسری سایت (کلید/مقدار JSON) — مثلاً key='look' برای تم و رنگ برند؛ فقط مدیر ویرایش می‌کند"""
    key = models.CharField('کلید', max_length=40, unique=True)
    value = models.JSONField('مقدار', default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تنظیم سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def __str__(self):
        return self.key


class Coupon(models.Model):
    """کد تخفیف — از پنل مدیر ساخته/ویرایش می‌شود و تنها مرجع محاسبهٔ سفارش در سرور است"""
    KIND = [('pct', 'درصدی'), ('cash', 'مبلغ ثابت (تومان)'), ('ship', 'ارسال رایگان'), ('day', 'اولویت ارسال همان روز')]

    code = models.CharField('کد', max_length=30, unique=True)
    kind = models.CharField('نوع', max_length=6, choices=KIND, default='pct')
    value = models.PositiveIntegerField('مقدار (درصد یا تومان)', default=0)
    min_total = models.BigIntegerField('حداقل مبلغ سفارش (تومان)', default=0)
    first_only = models.BooleanField('فقط اولین خرید', default=False)
    label = models.CharField('توضیح', max_length=120, blank=True, default='')
    active = models.BooleanField('فعال', default=True)
    owner = models.ForeignKey('ShopUser', null=True, blank=True, on_delete=models.CASCADE, related_name='personal_coupons',
                              verbose_name='متعلق به (کد شخصی)')
    max_uses = models.PositiveIntegerField('سقف استفاده (۰ = نامحدود)', default=0)
    used = models.PositiveIntegerField('دفعات استفاده', default=0)
    expires_at = models.DateTimeField('انقضا', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'
        ordering = ['-created_at', 'code']

    def __str__(self):
        return self.code

    @property
    def public(self):
        """قالب مورد انتظار فرانت (همان COUPONS قدیمی): type/val/min/first/label"""
        return {'code': self.code, 'type': self.kind, 'val': self.value, 'min': self.min_total,
                'first': self.first_only, 'label': self.label or self.code}

    def problem(self, user=None):
        """پیام فارسی اگر الان قابل استفاده نیست، وگرنه None (کدهای شخصی فقط برای صاحب حساب)"""
        if self.owner_id and (user is None or getattr(user, 'id', None) != self.owner_id):
            return 'این کد متعلق به حساب دیگری است'
        if not self.active:
            return 'کد تخفیف نامعتبر است'
        if self.expires_at and timezone.now() >= self.expires_at:
            return 'مهلت استفاده از این کد تخفیف تمام شده است'
        if self.max_uses and self.used >= self.max_uses:
            return 'ظرفیت استفاده از این کد تخفیف تمام شده است'
        return None


class ShippingMethod(models.Model):
    """روش ارسال — هزینه و زمان را مدیر از پنل تعیین می‌کند"""
    key = models.CharField('شناسه', max_length=20, unique=True)
    label = models.CharField('عنوان', max_length=120)
    cost = models.BigIntegerField('هزینه (تومان)', default=0)
    days = models.CharField('زمان تحویل', max_length=60, blank=True, default='')
    hint = models.CharField('توضیح کوتاه', max_length=120, blank=True, default='')
    active = models.BooleanField('فعال', default=True)
    sort = models.PositiveSmallIntegerField('ترتیب', default=0)

    class Meta:
        verbose_name = 'روش ارسال'
        verbose_name_plural = 'روش‌های ارسال'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.label

    @property
    def public(self):
        return {'type': self.key, 'label': self.label, 'cost': self.cost, 'days': self.days, 'hint': self.hint or self.days}


class Page(models.Model):
    """صفحات محتوایی (راهنمای خرید، سوالات متداول، قوانین، …) — توسط مدیر ویرایش می‌شود"""
    KIND = [('text', 'متنی'), ('faq', 'سوالات متداول'), ('shipping', 'ارسال (جدول هزینه‌ها)'), ('contact', 'تماس')]
    GROUP = [('guide', 'راهنمای خرید'), ('about', 'دربارهٔ ما'), ('legal', 'قوانین')]
    slug = models.CharField('نشانی', max_length=60, unique=True)
    title = models.CharField('عنوان', max_length=120)
    kind = models.CharField('نوع', max_length=10, choices=KIND, default='text')
    group = models.CharField('گروه', max_length=10, choices=GROUP, default='guide')
    body = models.TextField('متن', blank=True, default='')
    items = models.JSONField('سوال و جواب‌ها', default=list, blank=True)
    active = models.BooleanField('نمایش', default=True)
    sort = models.PositiveSmallIntegerField('ترتیب', default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'صفحه'
        verbose_name_plural = 'صفحات'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.title


class LuckyPrize(models.Model):
    """جایزه‌های کارت شانس (وزن = احتمال نسبی)"""
    title = models.CharField('عنوان', max_length=80)
    desc = models.CharField('توضیح', max_length=200, blank=True, default='')
    kind = models.CharField('نوع', max_length=6, choices=Coupon.KIND, default='pct')
    value = models.PositiveIntegerField('مقدار', default=0)
    min_total = models.BigIntegerField('حداقل خرید', default=0)
    weight = models.PositiveSmallIntegerField('وزن (احتمال نسبی)', default=10)
    icon = models.CharField('آیکن', max_length=30, default='i-gift')
    active = models.BooleanField('فعال', default=True)

    class Meta:
        verbose_name = 'جایزهٔ کارت شانس'
        verbose_name_plural = 'جایزه‌های کارت شانس'
        ordering = ['-weight', 'id']

    def __str__(self):
        return self.title


class LuckyWin(models.Model):
    """سابقهٔ هر بار استفاده از کارت شانس — روی حساب کاربر ثبت می‌شود"""
    user = models.ForeignKey('ShopUser', on_delete=models.CASCADE, related_name='lucky_wins')
    prize_title = models.CharField(max_length=80)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name='lucky_wins')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'برندهٔ کارت شانس'
        verbose_name_plural = 'برنده‌های کارت شانس'
        ordering = ['-created_at']


class ConsultRequest(models.Model):
    """درخواست مشاورهٔ تلفنی از صفحهٔ اصلی"""
    name = models.CharField('نام', max_length=120)
    phone = models.CharField('موبایل', max_length=15)
    topic = models.CharField('موضوع', max_length=80, blank=True, default='')
    done = models.BooleanField('پیگیری شد', default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'درخواست مشاوره'
        verbose_name_plural = 'درخواست‌های مشاوره'
        ordering = ['done', '-created_at']


class SmsLog(models.Model):
    """گزارش پیامک‌های ارسالی/آزمایشی — در پنل مدیر قابل مشاهده است"""
    ts = models.DateTimeField('زمان', auto_now_add=True, db_index=True)
    provider = models.CharField('سرویس‌دهنده', max_length=20)
    to = models.CharField('گیرنده', max_length=15)
    text = models.TextField('متن')
    tag = models.CharField('نوع', max_length=40, blank=True, default='')
    ok = models.BooleanField('موفق', default=False)
    detail = models.TextField('جزئیات پاسخ', blank=True, default='')

    class Meta:
        verbose_name = 'پیامک'
        verbose_name_plural = 'پیامک‌ها'
        ordering = ['-ts']
