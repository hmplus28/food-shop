"""نمای‌های API فروشگاه خانم گل

قرارداد با فرانت (app/src/services/api.js):
- خطاهای منطقی → 200 با {ok:false, msg} (فرانت پیام فارسی را مستقیم نشان می‌دهد)
- خطاهای ساختاری/اعتبارسنجی → 400 با {ok:false, msg}
- نقاط پایانی محافظت‌شده → هدر Authorization: Bearer <jwt>
"""
import random

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (Banner, ConsultRequest, MediaFile, NavCat, NavLink, OrderEvent, Pack, Payment, TrustItem, Coupon, LuckyPrize, LuckyWin, Order, OrderItem, Page, Product, ShippingMethod,
                     ShopUser, SiteSetting, SmsLog)
from .permissions import IsShopAdmin
from .pricing import CANCELLED, STATUS_LABELS, MAX_QTY_PER_LINE, compute_order, js_round, line_unit_price
from .seed import ensure_seed
from .serializers import (LoginSerializer, OrderCreateSerializer, OrderOutSerializer,
                          OrderStatusPatchSerializer, OrderTrackSerializer, ProductSerializer, ProductWriteSerializer,
                          RegisterSerializer)
from .sms import _async, notify_new_order, notify_status_change, normalize_phone, provider_status, send_sms

API_VERSION = '1.0.0'


def fail(msg, code=status.HTTP_200_OK):
    return Response({'ok': False, 'msg': msg}, status=code)


def ok(data=None, code=status.HTTP_200_OK):
    body = {'ok': True}
    body.update(data or {})
    return Response(body, status=code)


def first_msg(errors):
    """اولین پیام خطای سریالایزر به‌صورت رشتهٔ فارسی"""
    for v in errors.values():
        if isinstance(v, list) and v:
            return str(v[0])
    return 'اطلاعات ارسالی معتبر نیست'


def issue_tokens(user):
    rt = RefreshToken.for_user(user)
    return {'token': str(rt.access_token), 'refresh': str(rt)}


class AuthThrottle(AnonRateThrottle):
    scope = 'auth'


class CouponThrottle(AnonRateThrottle):
    scope = 'coupon'


# ---------------- سلامت سرویس ----------------

class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ensure_seed()
        return ok({'name': 'khanom-gol-api', 'version': API_VERSION, 'api': True,
                   'time': int(timezone.now().timestamp() * 1000),
                   'shop': settings.SHOP_NAME, 'sms': provider_status()})


# ---------------- فید ترب (Torob) ----------------

CAT_NAMES = {
    'ajil': 'آجیل و مغزها', 'pistachio': 'پسته', 'almond': 'بادام', 'walnut': 'گردو', 'hazelnut': 'فندق',
    'seeds': 'تخمه و مغز تخمه', 'dryfruit': 'میوه خشک', 'raisin': 'کشمش و مویز', 'date': 'خرما و رطب',
    'mulberryfig': 'توت خشک و انجیر', 'saffron': 'زعفران و ادویه', 'tea': 'دمنوش و محصولات طبیعی',
    'giftbox': 'آجیل و پک‌های هدیه',
}
TOROB_PAGE_SIZE = 100


def _cat_names():
    """نام دسته‌ها با اولویت دادهٔ مدیریتی (NavCat)؛ برای فید ترب"""
    names = dict(CAT_NAMES)
    names.update({c.slug: c.name for c in NavCat.objects.all()})
    return names


def _weight_text(w):
    return 'عدد' if w == 1 else (f'{w // 1000} کیلوگرم' if w % 1000 == 0 else f'{w} گرم')


IMG_CDN = 'https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/'


def public_img(u):
    """آدرس مطلق تصویر برای فید/شبکه‌های بیرونی: اگر تصاویر روی هاست باشند (LOCAL_IMAGES) از همان‌جا"""
    u = u or ''
    name = u[len(IMG_CDN):] if u.startswith(IMG_CDN) else (u[4:] if u.startswith('img/') else None)
    if name is None:
        return u
    if settings.LOCAL_IMAGES:
        return settings.SHOP_URL.rstrip('/') + '/img/' + name
    return IMG_CDN + name


def torob_item(p, names=None):
    """یک محصول در قالب API ترب — قیمت و وزنِ پیش‌فرض همان است که صفحهٔ محصول نشان می‌دهد
    (وزن دوم فهرست)، تا قیمت فید و صفحه همیشه یکی باشد. قیمت‌ها به تومان."""
    names = names or CAT_NAMES
    ws = p.weights or [1]
    w = ws[min(1, len(ws) - 1)]
    price = line_unit_price(p, w)
    old = js_round(p.price * w / 1000) if p.disc else 0
    base = settings.SHOP_URL.rstrip('/')
    img = public_img(p.img)
    return {
        'title': f'{p.name} - {_weight_text(w)}',
        'subtitle': p.grade or '',
        'page_unique': str(p.id),
        'current_price': price,
        'old_price': old if old > price else 0,
        'availability': 'instock' if p.stock > 0 else 'outofstock',
        'category_name': names.get(p.cat, p.cat),
        'image_link': img,
        'image_links': [img] if img else [],
        'page_url': f'{base}/product/{p.id}/',
        'short_desc': (p.desc or '')[:300],
        'spec': {'وزن': _weight_text(w), 'درجه': p.grade or '', 'دسته': names.get(p.cat, p.cat)},
        'date_added': p.created_at.isoformat(),
        'date_updated': p.updated_at.isoformat(),
        'guarantee': 'مرجوعی رایگان تا ۷ روز',
    }


class TorobProductsView(APIView):
    """فید محصولات برای ترب: GET|POST /api/v1/torob/products?page=1
    خروجی: {count, max_pages, products:[...]} — فقط محصولات نمایان؛ بدون نیاز به ورود."""
    permission_classes = [AllowAny]
    throttle_classes = []        # خزندهٔ ترب نباید با سقف anon مسدود شود

    def _page(self, request):
        raw = request.query_params.get('page') or (request.data.get('page') if hasattr(request.data, 'get') else None)
        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 1

    def _respond(self, request):
        ensure_seed()
        qs = Product.objects.filter(hide=False).order_by('id')
        total = qs.count()
        pages = max(1, -(-total // TOROB_PAGE_SIZE))
        page = self._page(request)
        start = (page - 1) * TOROB_PAGE_SIZE
        names = _cat_names()
        return Response({'count': total, 'max_pages': pages,
                         'products': [torob_item(p, names) for p in qs[start:start + TOROB_PAGE_SIZE]]})

    def get(self, request):
        return self._respond(request)

    def post(self, request):
        return self._respond(request)


# ---------------- حساب کاربری ----------------

class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if not s.is_valid():
            return fail(first_msg(s.errors), 400)
        d = s.validated_data
        if ShopUser.objects.filter(phone=d['phone']).exists():
            return fail('این شماره قبلاً ثبت‌نام کرده است؛ وارد شوید')   # خطای منطقی → ۲۰۰ با ok:false
        user = ShopUser.objects.create_user(phone=d['phone'], name=d['name'].strip(), password=d['password'])
        return ok({'user': user.public, **issue_tokens(user)})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        if not s.is_valid():
            return fail(first_msg(s.errors), 400)
        d = s.validated_data
        phone = normalize_phone(d['phone']) or d['phone']
        user = ShopUser.objects.filter(phone=phone).first()
        if not user or not user.check_password(d['password']) or not user.is_active:
            return fail('شماره یا رمز عبور اشتباه است')
        return ok({'user': user.public, **issue_tokens(user)})


class PhoneCheckView(APIView):
    """POST /auth/phone-check {phone} → {exists} — برای مرحلهٔ «شمارهٔ موبایل» تکمیل خرید (ورود یا ساخت حساب)"""
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]

    def post(self, request):
        phone = normalize_phone(request.data.get('phone') or '')
        if not phone:
            return fail('شماره موبایل معتبر وارد کنید (۰۹…)', 400)
        return ok({'exists': ShopUser.objects.filter(phone=phone, is_active=True).exists(), 'phone': phone})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return ok({'user': request.user.public})


# ---------------- محصولات ----------------

class ProductListCreateView(APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsShopAdmin()]
        return [AllowAny()]

    def get(self, request):
        ensure_seed()
        qs = Product.objects.all()
        is_admin = request.user.is_authenticated and (request.user.role == 'admin' or request.user.is_staff)
        if not (is_admin and request.query_params.get('all') in ('1', 'true')):
            qs = qs.filter(hide=False)
        return Response([ProductSerializer(p).data for p in qs])

    def post(self, request):
        s = ProductWriteSerializer(data=request.data)
        if not s.is_valid():
            return fail(first_msg(s.errors), 400)
        from django.db.models import Max
        mx = Product.objects.aggregate(m=Max('id'))['m'] or 0
        p = Product(id=max(100, mx) + 1, **s.validated_data)   # همان قانون شناسهٔ فرانت (nextProductId)
        p.save()
        return ok({'product': ProductSerializer(p).data})


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method != 'GET':
            return [IsShopAdmin()]
        return [AllowAny()]

    def _get(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        p = self._get(pk)
        if not p or (p.hide and not (request.user.is_authenticated and request.user.role == 'admin')):
            return fail('محصول پیدا نشد', 404)
        return Response(ProductSerializer(p).data)

    def put(self, request, pk):
        p = self._get(pk)
        if not p:
            return fail('محصول پیدا نشد', 404)
        s = ProductWriteSerializer(p, data=request.data, partial=True)
        if not s.is_valid():
            return fail(first_msg(s.errors), 400)
        s.save()
        return ok({'product': ProductSerializer(p).data})

    def delete(self, request, pk):
        p = self._get(pk)
        if not p:
            return fail('محصول پیدا نشد', 404)
        p.delete()
        return ok({'deleted': int(pk)})


class AdminProductsBulkView(APIView):
    """POST /admin/products/bulk — عملیات گروهی روی محصولات برای مدیر: {ids: […], action: 'delete'|'hide'|'show'}
    برای پاک‌سازی محصولات نمونه و شروع فروش واقعی؛ اقلام سفارش‌های قبلی اسنپ‌شات است و آسیب نمی‌بیند."""
    permission_classes = [IsShopAdmin]

    def post(self, request):
        ids = request.data.get('ids')
        action = str(request.data.get('action') or 'delete')
        if not isinstance(ids, list) or not ids or len(ids) > 500:
            return fail('فهرست شناسهٔ محصولات را بفرستید (۱ تا ۵۰۰ مورد)', 400)
        clean = []
        for v in ids:
            try:
                clean.append(int(v))
            except (TypeError, ValueError):
                return fail('شناسهٔ محصول باید عدد باشد', 400)
        qs = Product.objects.filter(id__in=clean)
        found = qs.count()
        if not found:
            return fail('هیچ‌کدام از محصولات پیدا نشد', 404)
        if action == 'delete':
            n, _ = qs.delete()
            msg = f'{n} محصول حذف شد'
        elif action in ('hide', 'show'):
            n = qs.update(hide=(action == 'hide'))
            msg = f'{n} محصول پنهان شد' if action == 'hide' else f'{n} محصول دوباره نمایش داده می‌شود'
        else:
            return fail('عملیات نامعتبر (حذف/پنهان/نمایش)', 400)
        return ok({'done': n, 'missing': len(clean) - found, 'action': action, 'msg': msg})


# ---------------- سفارش‌ها ----------------

class OrderCreateListView(APIView):
    """POST: ثبت سفارش (مهمان هم مجاز) — GET: فهرست سفارش‌ها (فقط مدیر)"""
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsShopAdmin()]
        return [IsAuthenticated()]          # ثبت سفارش فقط با حساب کاربری (ورود/ثبت‌نام با موبایل و رمز)

    def post(self, request):
        s = OrderCreateSerializer(data=request.data)
        if not s.is_valid():
            return fail(first_msg(s.errors), 400)
        d = s.validated_data
        addr = d['addr']

        # اعتبارسنجی اقلام
        pairs = []
        for it in d['items']:
            p = Product.objects.filter(id=it['pid']).first()
            if not p:
                return fail(f'محصول شمارهٔ {it["pid"]} یافت نشد')
            if it['w'] not in (p.weights or []):
                return fail(f'وزن انتخابی برای «{p.name}» مجاز نیست')
            if it['qty'] > MAX_QTY_PER_LINE:
                return fail('تعداد هر ردیف حداکثر ۲۰ است')
            pairs.append((p, it['w'], it['qty']))

        first_order = not Order.objects.filter(Q(user=request.user) | Q(a_phone=request.user.phone)).exists()
        try:
            money = compute_order(pairs, d.get('coupon'), d.get('shipType') or d.get('ship_type'), first_order, request.user)
        except ValueError as e:
            return fail(str(e))

        client_code = (d.get('client_code') or request.data.get('code') or '').strip().upper()
        user = request.user

        with transaction.atomic():
            # موجودی: قفل ردیف محصولات، بررسی و کم‌کردن (جلوگیری از فروش بیش از موجودی)
            need = {}
            for p, w, qty in pairs:
                need[p.id] = need.get(p.id, 0) + qty
            locked = {p.id: p for p in Product.objects.select_for_update().filter(id__in=list(need))}
            for pid_, qty_ in need.items():
                lp = locked[pid_]
                if lp.stock < qty_:
                    return fail(f'موجودی «{lp.name}» کافی نیست' + (f' (فقط {lp.stock} عدد باقی مانده)' if lp.stock > 0 else ' (ناموجود)'))
            for pid_, qty_ in need.items():
                Product.objects.filter(id=pid_).update(stock=F('stock') - qty_, sold=F('sold') + qty_)
            code = self._unique_code()
            order = Order.objects.create(
                code=code, client_code=client_code, user=user, status=0,
                a_name=addr['name'], a_phone=addr['phone'], a_prov=addr['prov'],
                a_city=addr['city'], a_addr=addr['addr'], note=d.get('note', ''), **money)
            OrderEvent.objects.create(order=order, status=0, by=request.user.phone)
            if money['coupon']:
                Coupon.objects.filter(code=money['coupon']).update(used=F('used') + 1)   # شمارندهٔ استفاده
            for p, w, qty in pairs:
                unit = line_unit_price(p, w)
                order.items.create(pid=p.id, name=p.name, img=p.img, w=w, qty=qty,
                                   unit_price=unit, cost=unit * qty)

        if not settings.ZIBAL_MERCHANT:   # با درگاه فعال، پیامک «ثبت سفارش» فقط بعد از پرداخت موفق می‌رود (notify_payment_paid)
            notify_new_order(order)      # پیامک مشتری + مدیر (پس‌زمینه)
        return ok({'code': order.code, 'status': order.status, 'total': order.total, 'pay_status': order.pay_status,
                   'sub': order.sub, 'off': order.off, 'ship_cost': order.ship_cost})

    @staticmethod
    def _unique_code():
        for _ in range(50):
            code = f'KG-{random.randint(10000, 99999)}'
            if not Order.objects.filter(code=code).exists():
                return code
        return f'KG-{int(timezone.now().timestamp()) % 100000}'

    def get(self, request):
        qs = Order.objects.prefetch_related('items', 'events').all()
        st = request.query_params.get('status')
        if st not in (None, ''):
            if st not in ('0', '1', '2', '3', '4'):
                return fail('وضعیت باید عددی ۰ تا ۴ باشد', 400)
            qs = qs.filter(status=int(st))
        phone = normalize_phone(request.query_params.get('phone', ''))
        if phone:
            qs = qs.filter(a_phone=phone)
        q = (request.query_params.get('q') or '').strip()
        if q:
            qs = qs.filter(code__icontains=q) | qs.filter(a_name__icontains=q)
        try:
            limit = min(500, max(1, int(request.query_params.get('limit', 200))))
        except ValueError:
            limit = 200
        data = OrderOutSerializer(qs[:limit], many=True).data
        return ok({'count': qs.count(), 'results': data})


class MyOrdersView(APIView):
    """سفارش‌های کاربر لاگین‌شده (بر اساس حساب یا شمارهٔ موبایل)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Order.objects.prefetch_related('items').filter(
            user=request.user) | Order.objects.prefetch_related('items').filter(a_phone=request.user.phone)
        return ok({'count': qs.count(), 'results': OrderOutSerializer(qs[:200], many=True).data})


def _restore_stock(o):
    for it in o.items.all():                                   # بازگرداندن موجودی و آمار فروش
        Product.objects.filter(id=it.pid).update(stock=F('stock') + it.qty)
        Product.objects.filter(id=it.pid, sold__gte=it.qty).update(sold=F('sold') - it.qty)


class OrderCancelView(APIView):
    """POST /orders/<code>/cancel — لغو توسط خود مشتری؛ فقط سفارشِ «ثبت‌شده» (هنوز در آماده‌سازی نیست) و پرداخت‌نشده.
    سفارش پرداخت‌شده باید با پشتیبانی هماهنگ شود (بازگشت وجه دستی)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        o = Order.objects.filter(code=(code or '').strip().upper()).first()
        if not o or (o.user_id != request.user.id and o.a_phone != request.user.phone):
            return fail('سفارشی با این کد پیدا نشد', 404)
        if o.status == CANCELLED:
            return fail('این سفارش قبلاً لغو شده است')
        if o.status != 0:
            return fail('سفارش وارد مرحلهٔ آماده‌سازی/ارسال شده و دیگر قابل لغو نیست؛ با پشتیبانی تماس بگیرید')
        if o.pay_status == 'paid':
            return fail('این سفارش پرداخت شده است؛ برای لغو و بازگشت وجه با پشتیبانی تماس بگیرید')
        with transaction.atomic():
            o = Order.objects.select_for_update().get(pk=o.pk)
            if o.status != 0:
                return fail('وضعیت سفارش تغییر کرده است؛ صفحه را تازه کنید')
            _restore_stock(o)
            o.status = CANCELLED
            if o.pay_status in ('pending', 'failed'):
                o.pay_status = 'failed'
            o.save(update_fields=['status', 'pay_status', 'updated_at'])
            OrderEvent.objects.create(order=o, status=CANCELLED, note='لغو توسط مشتری', by=request.user.phone)
        return ok({'code': o.code, 'status': o.status, 'status_label': STATUS_LABELS[o.status]})


class OrderTrackPatchView(APIView):
    """GET: پیگیری عمومی با کد | PATCH: تغییر وضعیت (مدیر) + پیامک به مشتری"""
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsShopAdmin()]
        return [AllowAny()]

    def _find(self, code):
        c = (code or '').strip().upper()
        return Order.objects.prefetch_related('items').filter(code=c).first() \
            or Order.objects.prefetch_related('items').filter(client_code=c).first()

    def get(self, request, code):
        o = self._find(code)
        if not o:
            return fail('سفارشی با این کد پیدا نشد', 404)
        return Response({'ok': True, **OrderTrackSerializer(o).data})

    def patch(self, request, code):
        """مدیر: تغییر وضعیت و/یا ثبت کد رهگیری و توضیح برای مشتری — هر تغییر در تاریخچه می‌ماند؛ لغو، موجودی را برمی‌گرداند"""
        o = self._find(code)
        if not o:
            return fail('سفارشی با این کد پیدا نشد', 404)
        s = OrderStatusPatchSerializer(data=request.data)
        if not s.is_valid():
            return fail(first_msg(s.errors), 400)
        d = s.validated_data
        new_status = d.get('status', o.status)
        note = (d.get('note') or '').strip()
        tracking = d['tracking'].strip() if 'tracking' in d else o.tracking
        if o.status == CANCELLED and new_status != CANCELLED:
            return fail('سفارش لغوشده قابل بازگشایی نیست', 400)
        if new_status == o.status and not note and tracking == o.tracking:
            return fail('تغییری ارسال نشد', 400)
        with transaction.atomic():
            if new_status == CANCELLED and o.status != CANCELLED:
                _restore_stock(o)
            changed = new_status != o.status
            o.status, o.tracking = new_status, tracking
            o.save(update_fields=['status', 'tracking', 'updated_at'])
            OrderEvent.objects.create(order=o, status=new_status, note=note[:200], by=request.user.phone)
        if changed or note:
            notify_status_change(o, o.status, note)
        return ok({'code': o.code, 'status': o.status, 'status_label': STATUS_LABELS[o.status], 'tracking': o.tracking})


# ---------------- ظاهر سایت (تم/رنگ) — سراسری، فقط مدیر ویرایش می‌کند ----------------

THEME_IDS = ('default', 'anari', 'zeitoni', 'gahvei', 'tousi', 'banafsh', 'abi')
_HEX = __import__('re').compile(r'^#[0-9a-fA-F]{6}$')


def _look():
    rec = SiteSetting.objects.filter(key='look').first()
    v = rec.value if rec and isinstance(rec.value, dict) else {}
    theme = v.get('theme') if v.get('theme') in THEME_IDS else 'default'
    tune = v.get('tune') if isinstance(v.get('tune'), list) and len(v['tune']) == 4 \
        and all(isinstance(h, str) and _HEX.match(h) for h in v['tune']) else None
    return {'theme': theme, 'tune': tune}


class SiteSettingsView(APIView):
    """GET /settings — عمومی: تم و رنگ برند سایت (برای همهٔ بازدیدکنندگان یکسان)"""
    permission_classes = [AllowAny]

    def get(self, request):
        return ok(_look())


class AdminSiteSettingsView(APIView):
    """PUT /admin/settings {theme, tune} — فقط مدیر؛ مقدار نامعتبر رد می‌شود"""
    permission_classes = [IsShopAdmin]

    def put(self, request):
        theme = request.data.get('theme', 'default')
        tune = request.data.get('tune', None)
        if theme not in THEME_IDS:
            return fail('تم نامعتبر است', 400)
        if tune is not None and not (isinstance(tune, list) and len(tune) == 4
                                     and all(isinstance(h, str) and _HEX.match(h) for h in tune)):
            return fail('رنگ‌های برند نامعتبر است (۴ مقدار #rrggbb)', 400)
        SiteSetting.objects.update_or_create(key='look', defaults={'value': {'theme': theme, 'tune': tune}})
        return ok(_look())


# ---------------- مدیر فروشگاه ----------------

class AdminLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''
        if not username or not password:
            return fail('نام کاربری و رمز مدیر را وارد کنید')
        user = ShopUser.objects.filter(username=username).first() \
            or ShopUser.objects.filter(phone=normalize_phone(username) or '-').first()
        if user and user.check_password(password) and user.is_active and (user.role == 'admin' or user.is_staff):
            return ok({'user': {'name': user.name, 'username': user.username}, **issue_tokens(user)})
        # حساب env (بار اول قبل از seed) — خودکار ساخته می‌شود
        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            from .seed import ensure_admin
            user, _ = ensure_admin()
            return ok({'user': {'name': user.name, 'username': user.username}, **issue_tokens(user)})
        return fail('نام کاربری یا رمز مدیر اشتباه است')


def _sales(qs):
    """سفارش‌های محسوب در فروش: لغوشده‌ها حذف؛ با درگاه فعال، پرداخت‌نشده‌ها هم حذف"""
    qs = qs.exclude(status=CANCELLED)
    if settings.ZIBAL_MERCHANT:
        qs = qs.filter(pay_status='paid')
    return qs


def _dashboard_extras():
    """داده‌های نمودار/لیست داشبورد: فروش ۷ روز اخیر، پرفروش‌ها، وضعیت سفارش‌ها، کم‌موجودی‌ها.
    تجمیع روزانه در پایتون انجام می‌شود (TruncDate/__date روی MariaDB بدون جدول timezone مقدار NULL می‌دهد)"""
    from django.db.models import Count, Sum
    today = timezone.localdate()
    since = today - timezone.timedelta(days=6)
    start = timezone.make_aware(timezone.datetime.combine(since, timezone.datetime.min.time()))
    acc = {}
    for created, total in _sales(Order.objects.filter(created_at__gte=start)).values_list('created_at', 'total'):
        d = timezone.localtime(created).date()
        n, t = acc.get(d, (0, 0))
        acc[d] = (n + 1, t + (total or 0))
    daily = []
    for i in range(7):
        d = since + timezone.timedelta(days=i)
        n, t = acc.get(d, (0, 0))
        daily.append({'date': d.isoformat(), 'orders': n, 'revenue': t})
    top = [{'pid': r['pid'], 'name': r['name'], 'qty': r['q'], 'revenue': r['r'] or 0}
           for r in OrderItem.objects.values('pid', 'name').annotate(q=Sum('qty'), r=Sum('cost')).order_by('-q')[:5]]
    by_status = {str(r['status']): r['n'] for r in Order.objects.values('status').annotate(n=Count('id'))}
    low = [{'id': p.id, 'name': p.name, 'stock': p.stock}
           for p in Product.objects.filter(stock__lt=10, hide=False).order_by('stock')[:8]]
    return {'daily': daily, 'top': top, 'byStatus': by_status, 'lowStockItems': low,
            'coupons': Coupon.objects.filter(active=True).count(),
            'consults': ConsultRequest.objects.filter(done=False).count()}


class AdminStatsView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        orders = Order.objects.all()
        revenue = sum(_sales(orders).values_list('total', flat=True) or [0])
        st = provider_status()
        last_sms = SmsLog.objects.first()
        return ok({
            'products': Product.objects.count(),
            'orders': orders.count(),
            'users': ShopUser.objects.filter(role='user').count(),
            'revenue': revenue,
            'lowStock': Product.objects.filter(stock__lt=10, hide=False).count(),
            'statusLabels': STATUS_LABELS,
            **_dashboard_extras(),
            'sms': {**st, 'sent': SmsLog.objects.count(),
                    'last': int(last_sms.ts.timestamp() * 1000) if last_sms else None},
        })


class AdminUsersView(APIView):
    """GET /admin/users?q=&limit= — فهرست مشتریان با تعداد و مجموع سفارش (فقط مدیر)"""
    permission_classes = [IsShopAdmin]

    def get(self, request):
        from django.db.models import Count, Sum
        qs = ShopUser.objects.all().order_by('-date_joined')
        q = (request.query_params.get('q') or '').strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(phone__contains=normalize_phone(q) or q) | Q(name__icontains=q))
        try:
            limit = max(1, min(500, int(request.query_params.get('limit') or 200)))
        except ValueError:
            limit = 200
        stats = {r['a_phone']: r for r in Order.objects.exclude(status=CANCELLED).values('a_phone').annotate(n=Count('id'), total=Sum('total'))}
        rows = [_user_row(u, stats.get(u.phone, {})) for u in qs[:limit]]
        return ok({'users': rows, 'total': ShopUser.objects.count()})


def _user_row(u, st=None):
    st = st or {}
    return {'id': u.id, 'name': u.name, 'phone': u.phone, 'role': u.role, 'active': u.is_active,
            'joined': u.date_joined.isoformat(), 'orders': st.get('n', 0), 'spent': st.get('total') or 0}


class AdminUserDetailView(APIView):
    """PATCH /admin/users/<id> {active?, role?, password?} — مدیریت مشتری/مدیر (فقط مدیر)"""
    permission_classes = [IsShopAdmin]

    def patch(self, request, pk):
        u = ShopUser.objects.filter(pk=pk).first()
        if not u:
            return fail('کاربر پیدا نشد', 404)
        if u.pk == request.user.pk and ('active' in request.data or 'role' in request.data):
            return fail('نقش یا وضعیت حساب خودتان را نمی‌توانید تغییر دهید', 400)
        d = request.data
        if 'active' in d:
            u.is_active = bool(d['active'])
        if 'role' in d:
            if d['role'] not in ('user', 'admin'):
                return fail('نقش نامعتبر است', 400)
            u.role = d['role']
            u.is_staff = d['role'] == 'admin'
            if d['role'] != 'admin':
                u.is_superuser = False
        if d.get('password') is not None:
            pw = str(d['password'])
            if len(pw) < 4:
                return fail('رمز عبور حداقل ۴ کاراکتر باشد', 400)
            u.set_password(pw)
        u.save()
        return ok({'user': _user_row(u)})


# ---------------- کدهای تخفیف ----------------

_COUPON_CODE = __import__('re').compile(r'^[A-Z0-9_-]{3,30}$')


class CouponCheckView(APIView):
    """GET /coupons/check?code=X — فقط بعد از ورود: اگر کد معتبر و برای همین حساب قابل استفاده بود قاعده‌اش را می‌دهد"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [CouponThrottle]

    def get(self, request):
        code = (request.query_params.get('code') or '').strip().upper()
        c = Coupon.objects.filter(code=code).first() if _COUPON_CODE.match(code) else None
        if not c or c.problem(request.user):
            return fail((c.problem(request.user) if c else None) or 'کد تخفیف نامعتبر است')
        return ok({'coupon': c.public})


def _coupon_row(c):
    return {**c.public, 'id': c.id, 'active': c.active, 'maxUses': c.max_uses, 'used': c.used,
            'expiresAt': c.expires_at.isoformat() if c.expires_at else None,
            'status': c.problem() or 'قابل استفاده'}


def _coupon_from(data, inst=None):
    """اعتبارسنجی ورودی مدیر → (dict فیلدها, پیام خطا)"""
    from django.utils.dateparse import parse_date, parse_datetime

    def pick(k, default):
        return data[k] if k in data else default

    code = str(pick('code', inst.code if inst else '')).strip().upper()
    if not _COUPON_CODE.match(code):
        return None, 'کد باید ۳ تا ۳۰ حرف انگلیسی/عدد (و - _) باشد'
    kind = pick('type', pick('kind', inst.kind if inst else 'pct'))
    if kind not in ('pct', 'cash', 'ship', 'day'):
        return None, 'نوع کد تخفیف نامعتبر است'
    try:
        value = int(pick('val', pick('value', inst.value if inst else 0)) or 0)
        min_total = int(pick('min', pick('min_total', inst.min_total if inst else 0)) or 0)
        max_uses = int(pick('maxUses', inst.max_uses if inst else 0) or 0)
    except (TypeError, ValueError):
        return None, 'مقادیر عددی نامعتبر است'
    if kind == 'pct' and not 1 <= value <= 100:
        return None, 'درصد تخفیف باید بین ۱ تا ۱۰۰ باشد'
    if kind == 'cash' and value < 1:
        return None, 'مبلغ تخفیف باید بیشتر از صفر باشد'
    if min(value, min_total, max_uses) < 0:
        return None, 'مقدار منفی مجاز نیست'
    exp = pick('expiresAt', inst.expires_at if inst else None)
    if isinstance(exp, str):
        exp = exp.strip()
        if not exp:
            exp = None
        else:
            d = parse_date(exp) if len(exp) == 10 else None
            parsed = timezone.datetime(d.year, d.month, d.day, 23, 59, 59) if d else parse_datetime(exp)   # فقط تاریخ → پایان همان روز
            if not parsed:
                return None, 'تاریخ انقضا نامعتبر است'
            exp = timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
    elif exp is not None and not hasattr(exp, 'year'):
        return None, 'تاریخ انقضا نامعتبر است'
    return {'code': code, 'kind': kind, 'value': value if kind in ('pct', 'cash') else 0, 'min_total': min_total,
            'first_only': bool(pick('first', pick('first_only', inst.first_only if inst else False))),
            'label': str(pick('label', inst.label if inst else ''))[:120],
            'active': bool(pick('active', inst.active if inst else True)), 'max_uses': max_uses,
            'expires_at': exp}, None


class AdminCouponsView(APIView):
    """GET فهرست / POST ساخت — فقط مدیر"""
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'coupons': [_coupon_row(c) for c in Coupon.objects.all()]})

    def post(self, request):
        fields, err = _coupon_from(request.data)
        if err:
            return fail(err, 400)
        if Coupon.objects.filter(code=fields['code']).exists():
            return fail('این کد قبلاً ساخته شده است', 400)
        return ok({'coupon': _coupon_row(Coupon.objects.create(**fields))})


class AdminCouponDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        c = Coupon.objects.filter(pk=pk).first()
        if not c:
            return fail('کد تخفیف پیدا نشد', 404)
        fields, err = _coupon_from(request.data, c)
        if err:
            return fail(err, 400)
        if Coupon.objects.filter(code=fields['code']).exclude(pk=c.pk).exists():
            return fail('این کد قبلاً ساخته شده است', 400)
        for k, v in fields.items():
            setattr(c, k, v)
        c.save()
        return ok({'coupon': _coupon_row(c)})

    def delete(self, request, pk):
        n, _ = Coupon.objects.filter(pk=pk).delete()
        return ok({'deleted': bool(n)}) if n else fail('کد تخفیف پیدا نشد', 404)


class AdminSmsLogView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        try:
            limit = min(100, max(1, int(request.query_params.get('limit', 50))))
        except ValueError:
            limit = 50
        rows = [{
            'ts': int(r.ts.timestamp() * 1000), 'provider': r.provider, 'to': r.to,
            'text': r.text, 'tag': r.tag, 'ok': r.ok, 'detail': r.detail[:200],
        } for r in SmsLog.objects.all()[:limit]]
        return ok({'provider': provider_status(), 'results': rows})


class AdminSmsTestView(APIView):
    """تست اتصال پنل پیامک — پیامک آزمایشی به شمارهٔ دلخواه"""
    permission_classes = [IsShopAdmin]

    def post(self, request):
        to = normalize_phone(request.data.get('to') or settings.SHOP_NOTIFY_PHONE)
        if not to:
            return fail('شمارهٔ گیرندهٔ تست را وارد کنید (۰۹…)')
        text = (request.data.get('text') or '').strip() or f'تست اتصال پنل پیامک {settings.SHOP_NAME}'
        sent, detail = send_sms(to, text, tag='test')
        return ok({'sent': sent, 'to': to, 'detail': str(detail)[:300]})


# ================= محتوای سایت، ارسال، کارت شانس، مشاوره =================
import re as _re
import secrets as _secrets

from .defaults import INFO as DEFAULT_INFO, LUCKY_SETTINGS as DEFAULT_LUCKY, SHIPPING_SETTINGS as DEFAULT_SHIPPING


def _setting(key, default):
    rec = SiteSetting.objects.filter(key=key).first()
    return {**default, **(rec.value if rec and isinstance(rec.value, dict) else {})}


def _int(v, lo, hi, name):
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise ValueError(f'{name} باید عدد باشد')
    if not lo <= n <= hi:
        raise ValueError(f'{name} باید بین {lo} تا {hi} باشد')
    return n


def _page_brief(p):
    return {'slug': p.slug, 'title': p.title, 'kind': p.kind, 'group': p.group}


def _page_full(p):
    return {**_page_brief(p), 'body': p.body, 'items': p.items if isinstance(p.items, list) else [],
            'updatedAt': p.updated_at.isoformat()}


def _shipping_public():
    s = _setting('shipping', DEFAULT_SHIPPING)
    return {'methods': [m.public for m in ShippingMethod.objects.filter(active=True)],
            'freeFrom': int(s.get('freeFrom') or 0), 'freeEnabled': bool(s.get('freeEnabled', True))}


def _cats_public():
    """دسته‌های فعال منو (هدر و منوی موبایل) — از دادهٔ مدیریتی NavCat"""
    return [c.public for c in NavCat.objects.filter(active=True)]


def _menu_public():
    """پیوندهای فعال منو (پایین منوی موبایل) — از دادهٔ مدیریتی NavLink"""
    return [m.public for m in NavLink.objects.filter(active=True, location='drawer')]


class SiteView(APIView):
    """GET /site — همهٔ محتوای عمومی در یک درخواست: اطلاعات تماس/متن‌ها، ارسال، فهرست صفحات، کارت شانس،
    دسته‌های منو (هدر/موبایل) و پیوندهای منو"""
    permission_classes = [AllowAny]

    def get(self, request):
        ensure_seed()
        lucky = _setting('lucky', DEFAULT_LUCKY)
        return ok({'info': _setting('info', DEFAULT_INFO), 'shipping': _shipping_public(), **_home_public(),
                   'pages': [_page_brief(p) for p in Page.objects.filter(active=True)],
                   'cats': _cats_public(), 'menu': _menu_public(),
                   'lucky': {'enabled': bool(lucky.get('enabled')), 'cooldownHours': lucky.get('cooldownHours')}})


class PageDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        p = Page.objects.filter(slug=slug, active=True).first()
        return ok({'page': _page_full(p)}) if p else fail('صفحه پیدا نشد', 404)


# ---------------- مشاوره ----------------

class ConsultThrottle(AnonRateThrottle):
    scope = 'consult'


class ConsultView(APIView):
    """POST /consult {name, phone, topic} — ثبت درخواست مشاورهٔ تلفنی (عمومی، با سقف نرخ)"""
    permission_classes = [AllowAny]
    throttle_classes = [ConsultThrottle]

    def post(self, request):
        name = str(request.data.get('name') or '').strip()[:120]
        phone = normalize_phone(request.data.get('phone') or '')
        topic = str(request.data.get('topic') or '').strip()[:80]
        if len(name) < 2:
            return fail('نام را وارد کنید', 400)
        if not phone:
            return fail('شماره موبایل معتبر وارد کنید (۰۹…)', 400)
        ConsultRequest.objects.create(name=name, phone=phone, topic=topic)
        return ok({})


# ---------------- کارت شانس (روی حساب، سمت سرور) ----------------

_CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def _lucky_state(user):
    """(فعال?, می‌تواند بچرخاند?, زمان مجاز بعدی ms یا None)"""
    cfg = _setting('lucky', DEFAULT_LUCKY)
    if not cfg.get('enabled'):
        return cfg, False, None
    mx = int(cfg.get('maxSpins') or 0)                    # 0 = بدون سقف تعداد
    if user and mx and LuckyWin.objects.filter(user=user).count() >= mx:
        return cfg, False, None
    last = LuckyWin.objects.filter(user=user).first() if user else None
    if last:
        nxt = last.created_at + timezone.timedelta(hours=int(cfg.get('cooldownHours') if cfg.get('cooldownHours') is not None else 24))
        if timezone.now() < nxt:
            return cfg, False, int(nxt.timestamp() * 1000)
    return cfg, True, None


class LuckyStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        cfg, can, nxt = _lucky_state(user)
        return ok({'enabled': bool(cfg.get('enabled')), 'loggedIn': bool(user),
                   'canSpin': bool(user and can), 'nextAt': nxt, 'cooldownHours': cfg.get('cooldownHours'),
                   'maxSpins': int(cfg.get('maxSpins') or 0),
                   'spinsUsed': LuckyWin.objects.filter(user=user).count() if user else 0})


class LuckySpinView(APIView):
    """POST /lucky/spin — فقط با حساب؛ هر N ساعت یک‌بار. جایزه همین‌جا تعیین و به‌صورت کد شخصی یک‌بارمصرف ساخته می‌شود."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [CouponThrottle]

    def post(self, request):
        with transaction.atomic():
            user = ShopUser.objects.select_for_update().get(pk=request.user.pk)   # جلوگیری از دو چرخش هم‌زمان
            cfg, can, nxt = _lucky_state(user)
            if not cfg.get('enabled'):
                return fail('کارت شانس فعلاً غیرفعال است')
            if not can:
                if nxt is None:
                    return fail('سقف دفعات استفادهٔ شما از کارت شانس تمام شده است')
                return Response({'ok': False, 'msg': 'کارت شانس بعدی شما هنوز فعال نشده است', 'nextAt': nxt})
            prizes = list(LuckyPrize.objects.filter(active=True))
            if not prizes:
                return fail('جایزه‌ای تعریف نشده است')
            total = sum(max(1, p.weight) for p in prizes)
            r = _secrets.randbelow(total)
            prize = prizes[-1]
            for p in prizes:
                r -= max(1, p.weight)
                if r < 0:
                    prize = p
                    break
            for _ in range(20):
                code = 'LK-' + ''.join(_secrets.choice(_CODE_ALPHABET) for _ in range(8))
                if not Coupon.objects.filter(code=code).exists():
                    break
            days = int(cfg.get('validDays') or 30)
            c = Coupon.objects.create(code=code, kind=prize.kind, value=prize.value, min_total=prize.min_total,
                                      label=prize.title, owner=user, max_uses=1,
                                      expires_at=timezone.now() + timezone.timedelta(days=days))
            LuckyWin.objects.create(user=user, prize_title=prize.title, coupon=c)
        return ok({'prize': {'title': prize.title, 'desc': prize.desc, 'icon': prize.icon},
                   'code': c.code, 'expiresAt': c.expires_at.isoformat(),
                   'nextAt': int((timezone.now() + timezone.timedelta(hours=int(cfg.get('cooldownHours') if cfg.get('cooldownHours') is not None else 24))).timestamp() * 1000)})


class LuckyMineView(APIView):
    """GET /lucky/mine — کدهای جایزهٔ حساب من"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = []
        for w in LuckyWin.objects.filter(user=request.user).select_related('coupon')[:50]:
            c = w.coupon
            rows.append({'title': w.prize_title, 'code': c.code if c else '', 'at': int(w.created_at.timestamp() * 1000),
                         'used': bool(c and c.used >= 1), 'expiresAt': c.expires_at.isoformat() if c and c.expires_at else None,
                         'status': (c.problem(request.user) if c else None) or 'قابل استفاده'})
        return ok({'wins': rows})


# ---------------- مدیر: اطلاعات و محتوا ----------------

_INFO_KEYS = {'shopName': 80, 'phone': 40, 'phoneTel': 20, 'phone2': 40, 'phone2Tel': 20, 'whatsapp': 20, 'email': 120, 'address': 300, 'hours': 120,
              'instagram': 200, 'telegram': 200, 'topbarMsg': 160, 'footerAbout': 600, 'heroTag': 80, 'heroTitle': 120,
              'heroTitleEm': 60, 'heroText': 300, 'consultText': 400, 'returnsNote': 160}


class AdminInfoView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'info': _setting('info', DEFAULT_INFO)})

    def put(self, request):
        cur = _setting('info', DEFAULT_INFO)
        for k, mx in _INFO_KEYS.items():
            if k in request.data:
                v = str(request.data[k] if request.data[k] is not None else '').strip()
                if len(v) > mx:
                    return fail(f'«{k}» حداکثر {mx} کاراکتر است', 400)
                if k in ('instagram', 'telegram') and v and not v.startswith('https://'):
                    return fail('نشانی شبکهٔ اجتماعی باید با https:// شروع شود', 400)
                if k in ('phoneTel', 'whatsapp') and v and not _re.fullmatch(r'\+?\d{5,18}', v):
                    return fail(f'«{k}» فقط عدد انگلیسی باشد (مثلاً 02191092000 / 989120000000)', 400)
                cur[k] = v
        SiteSetting.objects.update_or_create(key='info', defaults={'value': cur})
        return ok({'info': cur})


_SLUG = _re.compile(r'^[a-z0-9][a-z0-9-]{1,59}$')


def _page_from(data, inst=None):
    def pick(k, d):
        return data[k] if k in data else d
    slug = str(pick('slug', inst.slug if inst else '')).strip().lower()
    title = str(pick('title', inst.title if inst else '')).strip()
    kind = pick('kind', inst.kind if inst else 'text')
    group = pick('group', inst.group if inst else 'guide')
    body = str(pick('body', inst.body if inst else ''))
    if not _SLUG.match(slug):
        return None, 'نشانی صفحه باید ۲ تا ۶۰ حرف انگلیسی کوچک، عدد یا - باشد'
    if not 1 <= len(title) <= 120:
        return None, 'عنوان صفحه را وارد کنید (حداکثر ۱۲۰ کاراکتر)'
    if kind not in ('text', 'faq', 'shipping', 'contact') or group not in ('guide', 'about', 'legal'):
        return None, 'نوع یا گروه صفحه نامعتبر است'
    if len(body) > 20000:
        return None, 'متن صفحه حداکثر ۲۰٬۰۰۰ کاراکتر است'
    items = pick('items', inst.items if inst else [])
    if not isinstance(items, list) or len(items) > 60:
        return None, 'فهرست سوال و جواب نامعتبر است'
    clean = []
    for it in items:
        q, a = str((it or {}).get('q', '')).strip(), str((it or {}).get('a', '')).strip()
        if not q and not a:
            continue
        if not q or not a or len(q) > 250 or len(a) > 3000:
            return None, 'هر سوال و جواب باید پر باشد (سوال ≤۲۵۰، جواب ≤۳۰۰۰ کاراکتر)'
        clean.append({'q': q, 'a': a})
    try:
        sort = _int(pick('sort', inst.sort if inst else 0), 0, 999, 'ترتیب')
    except ValueError as e:
        return None, str(e)
    return {'slug': slug, 'title': title, 'kind': kind, 'group': group, 'body': body, 'items': clean,
            'sort': sort, 'active': bool(pick('active', inst.active if inst else True))}, None


class AdminPagesView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'pages': [{**_page_full(p), 'active': p.active, 'sort': p.sort, 'id': p.id} for p in Page.objects.all()]})

    def post(self, request):
        fields, err = _page_from(request.data)
        if err:
            return fail(err, 400)
        if Page.objects.filter(slug=fields['slug']).exists():
            return fail('این نشانی قبلاً استفاده شده است', 400)
        p = Page.objects.create(**fields)
        return ok({'page': {**_page_full(p), 'active': p.active, 'sort': p.sort, 'id': p.id}})


class AdminPageDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        p = Page.objects.filter(pk=pk).first()
        if not p:
            return fail('صفحه پیدا نشد', 404)
        fields, err = _page_from(request.data, p)
        if err:
            return fail(err, 400)
        if Page.objects.filter(slug=fields['slug']).exclude(pk=p.pk).exists():
            return fail('این نشانی قبلاً استفاده شده است', 400)
        for k, v in fields.items():
            setattr(p, k, v)
        p.save()
        return ok({'page': {**_page_full(p), 'active': p.active, 'sort': p.sort, 'id': p.id}})

    def delete(self, request, pk):
        n, _ = Page.objects.filter(pk=pk).delete()
        return ok({'deleted': True}) if n else fail('صفحه پیدا نشد', 404)


# ---------------- مدیر: هزینه‌های ارسال ----------------

_SHIP_KEY = _re.compile(r'^[a-z0-9][a-z0-9_-]{1,19}$')


def _ship_row(m):
    return {**m.public, 'id': m.id, 'active': m.active, 'sort': m.sort}


def _ship_from(data, inst=None):
    def pick(k, d):
        return data[k] if k in data else d
    key = str(pick('type', pick('key', inst.key if inst else ''))).strip().lower()
    label = str(pick('label', inst.label if inst else '')).strip()
    if not _SHIP_KEY.match(key):
        return None, 'شناسه باید ۲ تا ۲۰ حرف انگلیسی کوچک/عدد/-/_ باشد'
    if not 2 <= len(label) <= 120:
        return None, 'عنوان روش ارسال را وارد کنید'
    try:
        cost = _int(pick('cost', inst.cost if inst else 0), 0, 50_000_000, 'هزینه')
        sort = _int(pick('sort', inst.sort if inst else 0), 0, 999, 'ترتیب')
    except ValueError as e:
        return None, str(e)
    return {'key': key, 'label': label, 'cost': cost, 'sort': sort,
            'days': str(pick('days', inst.days if inst else ''))[:60].strip(),
            'hint': str(pick('hint', inst.hint if inst else ''))[:120].strip(),
            'active': bool(pick('active', inst.active if inst else True))}, None


class AdminShippingView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        s = _setting('shipping', DEFAULT_SHIPPING)
        return ok({'methods': [_ship_row(m) for m in ShippingMethod.objects.all()],
                   'freeFrom': int(s.get('freeFrom') or 0), 'freeEnabled': bool(s.get('freeEnabled', True))})

    def post(self, request):
        fields, err = _ship_from(request.data)
        if err:
            return fail(err, 400)
        if ShippingMethod.objects.filter(key=fields['key']).exists():
            return fail('این شناسه قبلاً ساخته شده است', 400)
        return ok({'method': _ship_row(ShippingMethod.objects.create(**fields))})


class AdminShippingDetailView(APIView):
    permission_classes = [IsShopAdmin]

    @staticmethod
    def _last_active(m):
        return m.active and not ShippingMethod.objects.filter(active=True).exclude(pk=m.pk).exists()

    def put(self, request, pk):
        m = ShippingMethod.objects.filter(pk=pk).first()
        if not m:
            return fail('روش ارسال پیدا نشد', 404)
        fields, err = _ship_from(request.data, m)
        if err:
            return fail(err, 400)
        if ShippingMethod.objects.filter(key=fields['key']).exclude(pk=m.pk).exists():
            return fail('این شناسه قبلاً ساخته شده است', 400)
        if self._last_active(m) and not fields['active']:
            return fail('حداقل یک روش ارسال باید فعال بماند', 400)
        for k, v in fields.items():
            setattr(m, k, v)
        m.save()
        return ok({'method': _ship_row(m)})

    def delete(self, request, pk):
        m = ShippingMethod.objects.filter(pk=pk).first()
        if not m:
            return fail('روش ارسال پیدا نشد', 404)
        if self._last_active(m):
            return fail('حداقل یک روش ارسال باید فعال بماند', 400)
        m.delete()
        return ok({'deleted': True})


class AdminShippingSettingsView(APIView):
    """PUT /admin/shipping/settings {freeFrom, freeEnabled} — سقف ارسال رایگان"""
    permission_classes = [IsShopAdmin]

    def put(self, request):
        try:
            free_from = _int(request.data.get('freeFrom', 0), 0, 1_000_000_000, 'سقف ارسال رایگان')
        except ValueError as e:
            return fail(str(e), 400)
        SiteSetting.objects.update_or_create(key='shipping', defaults={
            'value': {'freeFrom': free_from, 'freeEnabled': bool(request.data.get('freeEnabled', True))}})
        return ok({'freeFrom': free_from, 'freeEnabled': bool(request.data.get('freeEnabled', True))})


# ---------------- مدیر: کارت شانس ----------------

def _prize_row(p):
    return {'id': p.id, 'title': p.title, 'desc': p.desc, 'type': p.kind, 'val': p.value, 'min': p.min_total,
            'weight': p.weight, 'icon': p.icon, 'active': p.active}


def _prize_from(data, inst=None):
    def pick(k, d):
        return data[k] if k in data else d
    title = str(pick('title', inst.title if inst else '')).strip()
    kind = pick('type', pick('kind', inst.kind if inst else 'pct'))
    if not 2 <= len(title) <= 80:
        return None, 'عنوان جایزه را وارد کنید'
    if kind not in ('pct', 'cash', 'ship', 'day'):
        return None, 'نوع جایزه نامعتبر است'
    try:
        value = _int(pick('val', inst.value if inst else 0), 0, 1_000_000_000, 'مقدار')
        mn = _int(pick('min', inst.min_total if inst else 0), 0, 1_000_000_000, 'حداقل خرید')
        weight = _int(pick('weight', inst.weight if inst else 10), 1, 100, 'وزن')
    except ValueError as e:
        return None, str(e)
    if kind == 'pct' and not 1 <= value <= 100:
        return None, 'درصد باید بین ۱ تا ۱۰۰ باشد'
    if kind == 'cash' and value < 1:
        return None, 'مبلغ باید بیشتر از صفر باشد'
    icon = str(pick('icon', inst.icon if inst else 'i-gift')).strip()
    if not _re.fullmatch(r'i-[a-z0-9-]{1,20}', icon):
        icon = 'i-gift'
    return {'title': title, 'desc': str(pick('desc', inst.desc if inst else ''))[:200].strip(), 'kind': kind,
            'value': value if kind in ('pct', 'cash') else 0, 'min_total': mn, 'weight': weight, 'icon': icon,
            'active': bool(pick('active', inst.active if inst else True))}, None


class AdminLuckyView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        wins = [{'user': w.user.name, 'phone': w.user.phone, 'prize': w.prize_title, 'code': w.coupon.code if w.coupon else '',
                 'used': bool(w.coupon and w.coupon.used >= 1), 'at': int(w.created_at.timestamp() * 1000)}
                for w in LuckyWin.objects.select_related('user', 'coupon')[:60]]
        return ok({'settings': _setting('lucky', DEFAULT_LUCKY), 'prizes': [_prize_row(p) for p in LuckyPrize.objects.all()],
                   'wins': wins, 'totalWins': LuckyWin.objects.count()})

    def put(self, request):
        try:
            cfg = {'enabled': bool(request.data.get('enabled', True)),
                   'cooldownHours': _int(request.data.get('cooldownHours', 24), 0, 24 * 90, 'فاصلهٔ چرخش (ساعت)'),
                   'maxSpins': _int(request.data.get('maxSpins', 0), 0, 1000, 'سقف دفعات هر کاربر'),
                   'validDays': _int(request.data.get('validDays', 30), 1, 365, 'اعتبار جایزه (روز)')}
        except ValueError as e:
            return fail(str(e), 400)
        SiteSetting.objects.update_or_create(key='lucky', defaults={'value': cfg})
        return ok({'settings': cfg})

    def post(self, request):
        fields, err = _prize_from(request.data)
        if err:
            return fail(err, 400)
        return ok({'prize': _prize_row(LuckyPrize.objects.create(**fields))})


class AdminLuckyPrizeView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        p = LuckyPrize.objects.filter(pk=pk).first()
        if not p:
            return fail('جایزه پیدا نشد', 404)
        fields, err = _prize_from(request.data, p)
        if err:
            return fail(err, 400)
        for k, v in fields.items():
            setattr(p, k, v)
        p.save()
        return ok({'prize': _prize_row(p)})

    def delete(self, request, pk):
        n, _ = LuckyPrize.objects.filter(pk=pk).delete()
        return ok({'deleted': True}) if n else fail('جایزه پیدا نشد', 404)


# ---------------- مدیر: درخواست‌های مشاوره ----------------

class AdminConsultsView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        rows = [{'id': c.id, 'name': c.name, 'phone': c.phone, 'topic': c.topic, 'done': c.done,
                 'at': int(c.created_at.timestamp() * 1000)} for c in ConsultRequest.objects.all()[:200]]
        return ok({'consults': rows, 'pending': ConsultRequest.objects.filter(done=False).count()})


class AdminConsultDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def patch(self, request, pk):
        c = ConsultRequest.objects.filter(pk=pk).first()
        if not c:
            return fail('درخواست پیدا نشد', 404)
        c.done = bool(request.data.get('done', True))
        c.save(update_fields=['done'])
        return ok({})

    def delete(self, request, pk):
        n, _ = ConsultRequest.objects.filter(pk=pk).delete()
        return ok({'deleted': True}) if n else fail('درخواست پیدا نشد', 404)


# ================= صفحهٔ اصلی: بنر، پک‌ها، خرید اطمینان، بخش‌ها + تصاویر =================
import os as _os

from django.http import FileResponse, Http404
from rest_framework.parsers import MultiPartParser

from .bundles import MARK as VIRTUAL_MARK, drop_virtual, sync_virtual
from .defaults import HOME as DEFAULT_HOME

_IMG_OK = _re.compile(r'^(?:|img/[\w.-]{1,80}|media/[0-9a-f]{12}\.(?:jpg|png|webp|gif)|https://[^\s<>"\']{3,280}|/[\w./-]{1,200})$')
_LINK_OK = _re.compile(r'^(?:|/[\w./#?=&%-]{0,190}|https://[^\s<>"\']{3,190})$')


def _check_img(v):
    v = str(v or '').strip()
    return v if _IMG_OK.match(v) else None


def _check_link(v):
    v = str(v or '').strip()
    return v if _LINK_OK.match(v) else None


def _pack_end(p):
    """پایان شمارش معکوس پک (ms). چرخه‌ای: پس از پایان خودکار تمدید می‌شود؛ تاریخ ثابت: پس از پایان None (پنهان)"""
    now = timezone.now()
    end = p.ends_at or now + timezone.timedelta(hours=p.cycle_hours or 24)
    if end > now:
        return end
    if p.cycle_hours:
        step = timezone.timedelta(hours=p.cycle_hours)
        k = int((now - end) / step) + 1
        return end + k * step
    return None


def _vstock(pid, default):
    pr = Product.objects.filter(pk=pid).first() if pid else None
    return pr.stock if pr else default


def _pack_row(p, admin=False):
    end = _pack_end(p)
    row = {'id': p.id, 'name': p.name, 'sub': p.sub, 'image': p.image, 'old': p.old_price, 'now': p.now_price,
           'pid': p.product_id, 'stock': _vstock(p.product_id, 0), 'endsAt': int(end.timestamp() * 1000) if end else None}
    if admin:
        row.update({'active': p.active, 'cycleHours': p.cycle_hours, 'sort': p.sort,
                    'fixedEnd': p.ends_at.isoformat() if (p.ends_at and not p.cycle_hours) else None})
    return row


def _trust_row(t, admin=False):
    row = {'id': t.id, 'day': t.day, 'name': t.name, 'image': t.image, 'old': t.old_price, 'price': t.price,
           'pid': t.product_id, 'stock': _vstock(t.product_id, 0)}
    if admin:
        row['active'] = t.active
    return row


def _banner_row(b):
    return {'id': b.id, 'image': b.image, 'tag': b.tag, 'title': b.title, 'titleEm': b.title_em, 'text': b.text,
            'cta1': {'label': b.cta1_label, 'link': b.cta1_link}, 'cta2': {'label': b.cta2_label, 'link': b.cta2_link},
            'active': b.active, 'sort': b.sort}


def _home_cfg():
    cfg = {**DEFAULT_HOME, **_setting('home', DEFAULT_HOME)}
    order = [k for k in cfg.get('order', []) if k in DEFAULT_HOME['order']]
    cfg['order'] = order + [k for k in DEFAULT_HOME['order'] if k not in order]
    return cfg


def _home_public():
    packs = [r for r in (_pack_row(p) for p in Pack.objects.filter(active=True)) if r['endsAt']]
    return {'home': _home_cfg(),
            'banners': [_banner_row(b) for b in Banner.objects.filter(active=True)],
            'packs': packs,
            'trust': [_trust_row(t) for t in TrustItem.objects.filter(active=True)]}


# ---------------- آپلود و کتابخانهٔ تصاویر ----------------

_MAX_UPLOAD = 4 * 1024 * 1024
_MAGIC = {b'\xff\xd8\xff': 'jpg', b'\x89PNG\r\n\x1a\n': 'png', b'GIF87a': 'gif', b'GIF89a': 'gif'}


def _sniff(head):
    for sig, ext in _MAGIC.items():
        if head.startswith(sig):
            return ext
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return 'webp'
    return None


def _media_dir():
    d = settings.MEDIA_ROOT
    _os.makedirs(d, exist_ok=True)
    return d


class MediaServeView(APIView):
    """GET /media/<نام> — سرو تصویر آپلودشده (نام فقط ۱۲ هگز + پسوند مجاز؛ مسیر دلخواه ممکن نیست)"""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def get(self, request, name):
        if not _re.fullmatch(r'[0-9a-f]{12}\.(?:jpg|png|webp|gif)', name):
            raise Http404()
        path = _os.path.join(settings.MEDIA_ROOT, name)
        if not _os.path.isfile(path):
            raise Http404()
        ctype = {'jpg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp', 'gif': 'image/gif'}[name.rsplit('.', 1)[1]]
        resp = FileResponse(open(path, 'rb'), content_type=ctype)
        resp['Cache-Control'] = 'public, max-age=31536000, immutable'
        resp['X-Content-Type-Options'] = 'nosniff'
        return resp


class AdminMediaView(APIView):
    permission_classes = [IsShopAdmin]
    parser_classes = [MultiPartParser]

    def get(self, request):
        return ok({'files': [{'id': m.id, 'path': 'media/' + m.name, 'original': m.original, 'size': m.size,
                              'at': int(m.created_at.timestamp() * 1000)} for m in MediaFile.objects.all()[:300]]})

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return fail('فایلی انتخاب نشده است', 400)
        if f.size > _MAX_UPLOAD:
            return fail('حجم تصویر حداکثر ۴ مگابایت است', 400)
        head = f.read(16)
        ext = _sniff(head)
        if not ext:
            return fail('فقط تصویر JPG، PNG، WebP یا GIF مجاز است', 400)
        f.seek(0)
        name = _secrets.token_hex(6) + '.' + ext
        with open(_os.path.join(_media_dir(), name), 'wb') as out:
            for chunk in f.chunks():
                out.write(chunk)
        m = MediaFile.objects.create(name=name, original=_os.path.basename(f.name or '')[:120], size=f.size)
        return ok({'file': {'id': m.id, 'path': 'media/' + m.name, 'original': m.original, 'size': m.size}})


class AdminMediaDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def delete(self, request, pk):
        m = MediaFile.objects.filter(pk=pk).first()
        if not m:
            return fail('تصویر پیدا نشد', 404)
        try:
            _os.remove(_os.path.join(settings.MEDIA_ROOT, m.name))
        except OSError:
            pass
        m.delete()
        return ok({'deleted': True})


# ---------------- مدیر: تنظیم بخش‌های صفحهٔ اصلی ----------------

_HOME_TEXT_KEYS = {'title': 80, 'titleEm': 60, 'titleTail': 80, 'sub': 200, 'text': 200, 'badge': 40, 'why': 500, 'kicker': 80}


class AdminHomeView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'home': _home_cfg()})

    def put(self, request):
        cur = _home_cfg()
        data = request.data if isinstance(request.data, dict) else {}
        if 'order' in data:
            o = data['order']
            if not isinstance(o, list) or sorted(o) != sorted(DEFAULT_HOME['order']):
                return fail('ترتیب بخش‌ها نامعتبر است', 400)
            cur['order'] = o
        for sec in DEFAULT_HOME['order']:
            src = data.get(sec)
            if not isinstance(src, dict):
                continue
            dst = dict(cur.get(sec, {}))
            if 'on' in src:
                dst['on'] = bool(src['on'])
            if 'countdown' in src:
                dst['countdown'] = bool(src['countdown'])
            for k, mx in _HOME_TEXT_KEYS.items():
                if k in src:
                    v = str(src[k] or '').strip()
                    if len(v) > mx:
                        return fail(f'«{k}» حداکثر {mx} کاراکتر است', 400)
                    dst[k] = v
            if 'limit' in src:
                try:
                    dst['limit'] = _int(src['limit'], 1, 24, 'تعداد نمایش')
                except ValueError as e:
                    return fail(str(e), 400)
            if sec == 'why' and 'items' in src:
                items = src['items']
                if not isinstance(items, list) or len(items) > 8:
                    return fail('حداکثر ۸ مورد برای «چرا ما» مجاز است', 400)
                clean = []
                for it in items:
                    t_, x_ = str((it or {}).get('title', '')).strip(), str((it or {}).get('text', '')).strip()
                    ic = str((it or {}).get('icon', 'i-leaf')).strip()
                    if not t_ or len(t_) > 80 or len(x_) > 300 or not _re.fullmatch(r'i-[a-z0-9-]{1,20}', ic):
                        return fail('هر مورد «چرا ما» باید عنوان (≤۸۰) و متن (≤۳۰۰) معتبر داشته باشد', 400)
                    clean.append({'icon': ic, 'title': t_, 'text': x_})
                dst['items'] = clean
            cur[sec] = dst
        SiteSetting.objects.update_or_create(key='home', defaults={'value': cur})
        return ok({'home': _home_cfg()})


# ---------------- مدیر: بنرها ----------------

def _banner_from(data, inst=None):
    def pick(k, d):
        return data[k] if k in data else d
    img = _check_img(pick('image', inst.image if inst else ''))
    if img is None:
        return None, 'نشانی تصویر نامعتبر است (آپلودشده، img/… یا https://…)'
    links = {}
    for n in ('cta1', 'cta2'):
        src = pick(n, {'label': getattr(inst, n + '_label', '') if inst else '', 'link': getattr(inst, n + '_link', '') if inst else ''})
        src = src if isinstance(src, dict) else {}
        link = _check_link(src.get('link', ''))
        if link is None:
            return None, 'پیوند دکمه باید با / یا https:// شروع شود'
        links[n] = (str(src.get('label', '')).strip()[:40], link)
    try:
        sort = _int(pick('sort', inst.sort if inst else 0), 0, 99, 'ترتیب')
    except ValueError as e:
        return None, str(e)
    fields = {'image': img, 'tag': str(pick('tag', inst.tag if inst else ''))[:80].strip(),
              'title': str(pick('title', inst.title if inst else ''))[:120].strip(),
              'title_em': str(pick('titleEm', inst.title_em if inst else ''))[:60].strip(),
              'text': str(pick('text', inst.text if inst else ''))[:300].strip(),
              'cta1_label': links['cta1'][0], 'cta1_link': links['cta1'][1], 'cta2_label': links['cta2'][0], 'cta2_link': links['cta2'][1],
              'sort': sort, 'active': bool(pick('active', inst.active if inst else True))}
    if not (fields['image'] or fields['title']):
        return None, 'حداقل تصویر یا عنوان لازم است'
    return fields, None


class AdminBannersView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'banners': [_banner_row(b) for b in Banner.objects.all()]})

    def post(self, request):
        fields, err = _banner_from(request.data)
        if err:
            return fail(err, 400)
        return ok({'banner': _banner_row(Banner.objects.create(**fields))})


class AdminBannerDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        b = Banner.objects.filter(pk=pk).first()
        if not b:
            return fail('بنر پیدا نشد', 404)
        fields, err = _banner_from(request.data, b)
        if err:
            return fail(err, 400)
        for k, v in fields.items():
            setattr(b, k, v)
        b.save()
        return ok({'banner': _banner_row(b)})

    def delete(self, request, pk):
        n, _ = Banner.objects.filter(pk=pk).delete()
        return ok({'deleted': True}) if n else fail('بنر پیدا نشد', 404)


# ---------------- مدیر: منو و دسته‌ها (هدر و منوی موبایل) ----------------

_SLUG_OK = _re.compile(r'^[a-z0-9][a-z0-9-]{0,39}$')
_ICON_OK = _re.compile(r'^i-[a-z0-9-]{1,24}$')


def _nav_cat_row(c, counts=None):
    return {'id': c.id, 'slug': c.slug, 'name': c.name, 'icon': c.icon,
            'subs': c.subs if isinstance(c.subs, list) else [],
            'feat': {'img': c.feat_img, 't': c.feat_title, 's': c.feat_sub},
            'hot': c.hot, 'active': c.active, 'sort': c.sort,
            'products': (counts or {}).get(c.slug, 0)}


def _nav_cat_from(data, inst=None):
    """اعتبارسنجی ورودی دستهٔ منو — الگوبرداری از _banner_from"""
    def pick(k, d):
        return data[k] if k in data else d
    slug = str(pick('slug', inst.slug if inst else '')).strip().lower()
    if not _SLUG_OK.match(slug):
        return None, 'شناسه دسته باید انگلیسی، کوچک و با حرف/عدد شروع شود (مثلاً pistachio)'
    name = str(pick('name', inst.name if inst else '')).strip()
    if not name or len(name) > 60:
        return None, 'عنوان دسته الزامی است (حداکثر ۶۰ کاراکتر)'
    icon = str(pick('icon', inst.icon if inst else 'i-nut')).strip()
    if not _ICON_OK.match(icon):
        return None, 'آیکن معتبر نیست (مثلاً i-nut)'
    subs_in = pick('subs', inst.subs if inst else [])
    if not isinstance(subs_in, list) or len(subs_in) > 12:
        return None, 'زیرشاخه‌ها باید فهرستی با حداکثر ۱۲ مورد باشد'
    subs = []
    for s in subs_in:
        s = str(s or '').strip()
        if len(s) > 60:
            return None, 'هر زیرشاخه حداکثر ۶۰ کاراکتر است'
        if s:
            subs.append(s)
    feat = pick('feat', {}) if isinstance(pick('feat', {}), dict) else {}
    img = _check_img(feat.get('img', inst.feat_img if inst else ''))
    if img is None:
        return None, 'نشانی تصویر ویژه نامعتبر است (آپلودشده، img/… یا https://…)'
    try:
        sort = _int(pick('sort', inst.sort if inst else 0), 0, 99, 'ترتیب')
    except ValueError as e:
        return None, str(e)
    fields = {'slug': slug, 'name': name, 'icon': icon, 'subs': subs,
              'feat_img': img, 'feat_title': str(feat.get('t', inst.feat_title if inst else ''))[:80].strip(),
              'feat_sub': str(feat.get('s', inst.feat_sub if inst else ''))[:120].strip(),
              'hot': bool(pick('hot', inst.hot if inst else False)),
              'active': bool(pick('active', inst.active if inst else True)), 'sort': sort}
    return fields, None


class AdminCatsView(APIView):
    """GET/POST /admin/cats — فهرست دسته‌های منو (با شمارش محصولات) و ساخت دستهٔ جدید"""
    permission_classes = [IsShopAdmin]

    def get(self, request):
        from django.db.models import Count
        counts = {row['cat']: row['n'] for row in
                  Product.objects.values('cat').annotate(n=Count('id'))}
        return ok({'cats': [_nav_cat_row(c, counts) for c in NavCat.objects.all()]})

    def post(self, request):
        fields, err = _nav_cat_from(request.data)
        if err:
            return fail(err, 400)
        if NavCat.objects.filter(slug=fields['slug']).exists():
            return fail('دسته‌ای با این شناسه از قبل وجود دارد', 400)
        return ok({'cat': _nav_cat_row(NavCat.objects.create(**fields))})


class AdminCatDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        c = NavCat.objects.filter(pk=pk).first()
        if not c:
            return fail('دسته پیدا نشد', 404)
        fields, err = _nav_cat_from(request.data, c)
        if err:
            return fail(err, 400)
        old_slug = c.slug
        with transaction.atomic():
            if fields['slug'] != old_slug:
                if NavCat.objects.filter(slug=fields['slug']).exclude(pk=c.pk).exists():
                    return fail('دسته‌ای با این شناسه از قبل وجود دارد', 400)
                # تغییر شناسه دسته، محصولات مرتبط را هم خودکار جابه‌جا می‌کند
                Product.objects.filter(cat=old_slug).update(cat=fields['slug'])
            for k, v in fields.items():
                setattr(c, k, v)
            c.save()
        return ok({'cat': _nav_cat_row(c)})

    def delete(self, request, pk):
        c = NavCat.objects.filter(pk=pk).first()
        if not c:
            return fail('دسته پیدا نشد', 404)
        used = Product.objects.filter(cat=c.slug).count()
        if used:
            return fail(f'{used} محصول در این دسته است؛ اول محصولات را به دستهٔ دیگری منتقل یا حذف کنید', 400)
        c.delete()
        return ok({'deleted': True})


def _nav_link_row(m):
    return {'id': m.id, 'label': m.label, 'icon': m.icon, 'link': m.link,
            'location': m.location, 'active': m.active, 'sort': m.sort}


def _nav_link_from(data, inst=None):
    def pick(k, d):
        return data[k] if k in data else d
    label = str(pick('label', inst.label if inst else '')).strip()
    if not label or len(label) > 60:
        return None, 'عنوان پیوند الزامی است (حداکثر ۶۰ کاراکتر)'
    icon = str(pick('icon', inst.icon if inst else 'i-leaf')).strip()
    if not _ICON_OK.match(icon):
        return None, 'آیکن معتبر نیست (مثلاً i-leaf)'
    link = _check_link(pick('link', inst.link if inst else ''))
    if not link:
        return None, 'پیوند باید با / یا https:// شروع شود (مثلاً /track)'
    try:
        sort = _int(pick('sort', inst.sort if inst else 0), 0, 99, 'ترتیب')
    except ValueError as e:
        return None, str(e)
    return {'label': label, 'icon': icon, 'link': link, 'location': 'drawer',
            'active': bool(pick('active', inst.active if inst else True)), 'sort': sort}, None


class AdminMenuView(APIView):
    """GET/POST /admin/menu — فهرست و ساخت پیوندهای منو (پایین منوی موبایل)"""
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'menu': [_nav_link_row(m) for m in NavLink.objects.all()]})

    def post(self, request):
        fields, err = _nav_link_from(request.data)
        if err:
            return fail(err, 400)
        return ok({'link': _nav_link_row(NavLink.objects.create(**fields))})


class AdminMenuDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        m = NavLink.objects.filter(pk=pk).first()
        if not m:
            return fail('پیوند پیدا نشد', 404)
        fields, err = _nav_link_from(request.data, m)
        if err:
            return fail(err, 400)
        for k, v in fields.items():
            setattr(m, k, v)
        m.save()
        return ok({'link': _nav_link_row(m)})

    def delete(self, request, pk):
        n, _ = NavLink.objects.filter(pk=pk).delete()
        return ok({'deleted': True}) if n else fail('پیوند پیدا نشد', 404)


# ---------------- مدیر: پک‌ها ----------------

def _pack_from(data, inst=None):
    def pick(k, d):
        return data[k] if k in data else d
    name = str(pick('name', inst.name if inst else '')).strip()
    if not 2 <= len(name) <= 80:
        return None, 'نام پک را وارد کنید'
    img = _check_img(pick('image', inst.image if inst else ''))
    if img is None:
        return None, 'نشانی تصویر نامعتبر است'
    try:
        old = _int(pick('old', inst.old_price if inst else 0), 0, 1_000_000_000, 'قیمت قبل')
        now = _int(pick('now', inst.now_price if inst else 0), 1, 1_000_000_000, 'قیمت فعلی')
        hours = _int(pick('cycleHours', inst.cycle_hours if inst else 24), 0, 24 * 30, 'چرخهٔ شمارش (ساعت)')
        stock = _int(pick('stock', _vstock(inst.product_id, 20) if inst else 20), 0, 1_000_000, 'موجودی')
        sort = _int(pick('sort', inst.sort if inst else 0), 0, 99, 'ترتیب')
    except ValueError as e:
        return None, str(e)
    if old and now > old:
        return None, 'قیمت فعلی نباید بیشتر از قیمت قبل باشد'
    fixed = pick('fixedEnd', inst.ends_at.isoformat() if (inst and inst.ends_at and not inst.cycle_hours) else None)
    ends = inst.ends_at if inst else None
    if hours == 0:
        from django.utils.dateparse import parse_datetime
        parsed = parse_datetime(str(fixed)) if fixed else None
        if not parsed:
            return None, 'برای پک بدون چرخه، تاریخ و ساعت پایان را مشخص کنید'
        ends = timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
    elif ends is None or (inst is not None and hours != inst.cycle_hours):
        ends = timezone.now() + timezone.timedelta(hours=hours)        # فقط وقتی چرخه عوض شد/برای پک جدید؛ ویرایش‌های دیگر شمارش را ریست نمی‌کنند
    return {'name': name, 'sub': str(pick('sub', inst.sub if inst else ''))[:160].strip(), 'image': img, 'old_price': old,
            'now_price': now, 'cycle_hours': hours, 'ends_at': ends, 'sort': sort,
            'active': bool(pick('active', inst.active if inst else True))}, {'stock': stock}


def _save_pack(p, fields, extra):
    for k, v in fields.items():
        setattr(p, k, v)
    p.product_id = sync_virtual(Product, p.product_id, name=p.name, image=p.image, price=p.now_price,
                                stock=extra['stock'], active=p.active, kind='پک تخفیفی')
    p.save()
    return p


class AdminPacksView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'packs': [_pack_row(p, True) for p in Pack.objects.all()]})

    def post(self, request):
        fields, extra = _pack_from(request.data)
        if extra is None or isinstance(extra, str):
            return fail(extra or fields, 400)
        if fields is None:
            return fail(extra, 400)
        return ok({'pack': _pack_row(_save_pack(Pack(), fields, extra), True)})


class AdminPackDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        p = Pack.objects.filter(pk=pk).first()
        if not p:
            return fail('پک پیدا نشد', 404)
        fields, extra = _pack_from(request.data, p)
        if fields is None:
            return fail(extra, 400)
        return ok({'pack': _pack_row(_save_pack(p, fields, extra), True)})

    def delete(self, request, pk):
        p = Pack.objects.filter(pk=pk).first()
        if not p:
            return fail('پک پیدا نشد', 404)
        drop_virtual(Product, p.product_id)
        p.delete()
        return ok({'deleted': True})

    def post(self, request, pk):
        """راه‌اندازی مجدد شمارش معکوس از همین لحظه"""
        p = Pack.objects.filter(pk=pk).first()
        if not p:
            return fail('پک پیدا نشد', 404)
        if not p.cycle_hours:
            return fail('پک با تاریخ ثابت چرخه ندارد؛ تاریخ پایان را ویرایش کنید', 400)
        p.ends_at = timezone.now() + timezone.timedelta(hours=p.cycle_hours)
        p.save(update_fields=['ends_at'])
        return ok({'pack': _pack_row(p, True)})


# ---------------- مدیر: خرید اطمینان ----------------

def _trust_from(data, inst=None):
    def pick(k, d):
        return data[k] if k in data else d
    name = str(pick('name', inst.name if inst else '')).strip()
    if not 2 <= len(name) <= 160:
        return None, 'نام کالا را وارد کنید'
    img = _check_img(pick('image', inst.image if inst else ''))
    if img is None:
        return None, 'نشانی تصویر نامعتبر است'
    try:
        day = _int(pick('day', inst.day if inst else 0), 0, 6, 'روز هفته')
        old = _int(pick('old', inst.old_price if inst else 0), 0, 1_000_000_000, 'قیمت قبل')
        price = _int(pick('price', inst.price if inst else 0), 1, 1_000_000_000, 'قیمت ویژه')
        stock = _int(pick('stock', _vstock(inst.product_id, 8) if inst else 8), 0, 1_000_000, 'موجودی')
    except ValueError as e:
        return None, str(e)
    if old and price > old:
        return None, 'قیمت ویژه نباید بیشتر از قیمت قبل باشد'
    return {'day': day, 'name': name, 'image': img, 'old_price': old, 'price': price,
            'active': bool(pick('active', inst.active if inst else True))}, {'stock': stock}


def _save_trust(t, fields, extra):
    for k, v in fields.items():
        setattr(t, k, v)
    t.product_id = sync_virtual(Product, t.product_id, name=t.name, image=t.image, price=t.price,
                                stock=extra['stock'], active=t.active, kind='خرید اطمینان')
    t.save()
    return t


class AdminTrustView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        return ok({'items': [_trust_row(t, True) for t in TrustItem.objects.all()]})

    def post(self, request):
        fields, extra = _trust_from(request.data)
        if fields is None:
            return fail(extra, 400)
        if TrustItem.objects.filter(day=fields['day']).exists():
            return fail('برای این روز هفته قبلاً کالا تعریف شده است (آن را ویرایش کنید)', 400)
        return ok({'item': _trust_row(_save_trust(TrustItem(), fields, extra), True)})


class AdminTrustDetailView(APIView):
    permission_classes = [IsShopAdmin]

    def put(self, request, pk):
        t = TrustItem.objects.filter(pk=pk).first()
        if not t:
            return fail('کالا پیدا نشد', 404)
        fields, extra = _trust_from(request.data, t)
        if fields is None:
            return fail(extra, 400)
        if TrustItem.objects.filter(day=fields['day']).exclude(pk=t.pk).exists():
            return fail('برای این روز هفته قبلاً کالا تعریف شده است', 400)
        return ok({'item': _trust_row(_save_trust(t, fields, extra), True)})

    def delete(self, request, pk):
        t = TrustItem.objects.filter(pk=pk).first()
        if not t:
            return fail('کالا پیدا نشد', 404)
        drop_virtual(Product, t.product_id)
        t.delete()
        return ok({'deleted': True})


# ---------------- درگاه پرداخت آنلاین زیبال ----------------
#
# جریان: «پرداخت» → POST /pay/start (ساخت تراکنش در زیبال) → ریدایرکت به
# gateway.zibal.ir/start/{trackId} → بازگشت کاربر به صفحهٔ /pay فرانت (callbackUrl)
# → فرانت POST /pay/verify را صدا می‌زند → تأیید مبلغ + ثبت وضعیت قطعی.
# مبلغ سفارش تومان است و زیبال «ریال» می‌پذیرد (×۱۰). کد ۱۰۰/۲۰۱ = تأیید موفق.

class PayThrottle(AnonRateThrottle):
    scope = 'pay'


def _zibal_post(path, payload, timeout=15):
    """POST به زیبال؛ خروجی dict یا None — هیچ استثنایی به بیرون نمی‌رود"""
    import json as _json
    import urllib.error
    import urllib.request
    from django.conf import settings as _s
    try:
        req = urllib.request.Request(
            _s.ZIBAL_API_BASE + path,
            data=_json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _json.loads(resp.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as e:
        try:
            return _json.loads(e.read().decode('utf-8') or '{}')
        except Exception:                                          # noqa: BLE001
            return {'result': -999, 'message': f'خطای HTTP {e.code} از زیبال'}
    except Exception as e:                                         # noqa: BLE001
        return {'result': -998, 'message': f'اتصال به زیبال برقرار نشد ({e})'}


def _front_base(request):
    """ریشهٔ فرانت برای بازگشت از درگاه — همان دامنهٔ درخواست جاری (بدون زیرمسیر بک‌اند)"""
    if settings.ZIBAL_CALLBACK_URL:
        return settings.ZIBAL_CALLBACK_URL.rstrip('/')
    # API معمولاً روی ساب‌دامین (api.دامنه) است ولی زیبال فقط دامنهٔ ثبت‌شدهٔ سایت را می‌پذیرد (کد ۱۰۶)؛
    # پس دامنهٔ فرانت: Origin درخواست (مرورگر) ← SHOP_URL (اگر GitHub Pages نیست) ← هاست درخواست
    origin = (request.headers.get('Origin') or '').rstrip('/')
    if origin.startswith(('http://', 'https://')):
        return origin
    shop = (settings.SHOP_URL or '').rstrip('/')
    if shop and 'github.io' not in shop:
        return shop
    https = request.is_secure() or request.headers.get('X-Forwarded-Proto') == 'https'
    return ('https' if https else 'http') + '://' + request.get_host()


def _pay_find_order(code, user=None):
    """سفارش را با کد پیدا می‌کند؛ اگر user داده شود فقط سفارش خودش (کد یا موبایل حساب)"""
    o = Order.objects.filter(code=(code or '').strip().upper()).first()
    if not o:
        return None, 'سفارشی با این کد پیدا نشد'
    if user is not None and (o.user_id != user.id and o.a_phone != user.phone):
        return None, 'این سفارش متعلق به حساب شما نیست'
    return o, None


class PayConfigView(APIView):
    """GET: فعال‌بودن درگاه پرداخت برای فرانت (بدون دادهٔ حساس — فقط بله/خیر)"""
    permission_classes = [AllowAny]

    def get(self, request):
        return ok({'enabled': bool(settings.ZIBAL_MERCHANT), 'gateway': 'zibal'})


class PayStartView(APIView):
    """POST {code}: ساخت تراکنش زیبال برای سفارش کاربر → {trackId, payUrl, amount}"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [PayThrottle]

    def post(self, request):
        if not settings.ZIBAL_MERCHANT:
            return fail('درگاه پرداخت هنوز فعال نشده است؛ سفارش شما ثبت شد و به‌صورت تلفنی هماهنگ می‌شود')
        code = (request.data.get('code') or '').strip()
        o, err = _pay_find_order(code, request.user)
        if not o:
            return fail(err, 404)
        if o.pay_status == 'paid':
            return fail('این سفارش قبلاً پرداخت شده است ✅')
        if o.status == 4:
            return fail('این سفارش لغو شده است')
        if o.total <= 0:
            return fail('مبلغ قابل پرداخت این سفارش نامعتبر است')

        # هر تلاش پرداخت یک ردیف تراکنش تازه (زیبال برای هر trackId یک پرداخت مستقل می‌سازد)
        callback = f'{_front_base(request)}/pay?order={o.code}'
        resp = _zibal_post('request', {
            'merchant': settings.ZIBAL_MERCHANT,
            'amount': o.total * settings.ZIBAL_TOMAN_TO_RIAL,
            'callbackUrl': callback,
            'description': f'سفارش {o.code} — {settings.SHOP_NAME}',
            'orderId': o.code,
            'mobile': o.a_phone,
        })
        track_id = str(resp.get('trackId') or '').strip()
        if resp.get('result') == 100 and track_id:
            Payment.objects.create(order=o, track_id=track_id, amount=o.total, state='pending',
                                   result=100, message=resp.get('message') or '')
            o.pay_status = 'pending'
            o.save(update_fields=['pay_status'])
            return ok({'trackId': track_id, 'amount': o.total,
                       'payUrl': f'https://gateway.zibal.ir/start/{track_id}',
                       'sandbox': settings.ZIBAL_MERCHANT.lower() == 'zibal'})
        msg = resp.get('message') or 'ساخت تراکنش در زیبال انجام نشد'
        Payment.objects.create(order=o, track_id=track_id or '-', amount=o.total, state='failed',
                               result=resp.get('result'), message=msg[:200])
        return fail(f'پرداخت آنلاین در دسترس نیست: {msg}')


class PayVerifyView(APIView):
    """POST {code, trackId}: تأیید تراکنش پس از بازگشت از درگاه (idempotent)"""
    permission_classes = [AllowAny]
    throttle_classes = [PayThrottle]

    def post(self, request):
        if not settings.ZIBAL_MERCHANT:
            return fail('درگاه پرداخت فعال نیست')
        track_id = str(request.data.get('trackId') or '').strip()
        code = (request.data.get('code') or '').strip().upper()
        if not track_id:
            return fail('شناسهٔ تراکنش یافت نشد', 400)
        p = Payment.objects.select_related('order').filter(track_id=track_id).order_by('-id').first()
        if not p:
            return fail('تراکنشی با این شناسه ثبت نشده است', 404)
        if code and p.order.code != code:
            return fail('شناسهٔ تراکنش با سفارش مطابقت ندارد')
        o = p.order

        # قبلاً تأیید شده → همان نتیجهٔ قبلی (خنثی بودن نسبت به refresh صفحه)
        if p.state == 'paid':
            return ok({'state': 'paid', 'order': {'code': o.code, 'pay_status': o.pay_status,
                      'total': o.total}, 'amount': p.amount})

        resp = _zibal_post('verify', {'merchant': settings.ZIBAL_MERCHANT, 'trackId': track_id})
        result = resp.get('result')
        p.result = result if isinstance(result, int) else None
        p.message = str(resp.get('message') or '')[:200]

        if result in (100, 201):
            # کنترل مبلغ: زیبال ریال برمی‌گرداند؛ مبلغ باید دقیقاً با سفارش بخواند
            paid_rial = int(resp.get('amount') or 0)
            if paid_rial and paid_rial != p.amount * settings.ZIBAL_TOMAN_TO_RIAL:
                p.state = 'failed'
                p.message = 'مبلغ تراکنش با سفارش مطابقت ندارد'
                p.save()
                o.pay_status = 'failed'
                o.save(update_fields=['pay_status'])
                return fail('مبلغ پرداخت‌شده با مبلغ سفارش مطابقت ندارد؛ با پشتیبانی تماس بگیرید')
            p.state = 'paid'
            p.ref_number = str(resp.get('refNumber') or '')
            p.card_number = str(resp.get('cardNumber') or '')[:30]
            p.save()
            o.pay_status = 'paid'
            o.save(update_fields=['pay_status'])
            OrderEvent.objects.create(order=o, status=o.status,
                                      note=f'پرداخت آنلاین با زیبال تأیید شد (کد پیگیری درگاه: {track_id})',
                                      by='zibal')
            _fmt = f'{p.amount:,}'
            _async(notify_payment_paid, o, f'{settings.SHOP_NAME}: پرداخت سفارش {o.code} به مبلغ {_fmt} تومان با موفقیت انجام شد. 🌰')
            return ok({'state': 'paid', 'order': {'code': o.code, 'pay_status': o.pay_status,
                      'total': o.total}, 'amount': p.amount})

        if result in (202, 203):                                # پرداخت‌نشده/لغو‌شده یا trackId نامعتبر
            p.state = 'cancelled' if result == 202 else 'failed'
            p.save()
            if o.pay_status == 'pending':
                o.pay_status = 'failed'
                o.save(update_fields=['pay_status'])
            return fail('پرداخت انجام نشد یا لغو شد؛ می‌توانید دوباره تلاش کنید')

        p.state = 'failed'
        p.save()
        return fail(p.message or 'تأیید تراکنش انجام نشد')


def notify_payment_paid(order, text):
    """پیامک موفقیت پرداخت به مشتری و مدیر (پس‌زمینه)"""
    from .sms import _safe_send
    _async(_safe_send, order.a_phone, text, 'pay-customer')
    if settings.SHOP_NOTIFY_PHONE:
        _async(_safe_send, settings.SHOP_NOTIFY_PHONE,
               f'پرداخت سفارش {order.code} ({order.total:,} تومان) تأیید شد ✅', 'pay-admin')
