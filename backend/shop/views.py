"""نمای‌های API فروشگاه خانم گل

قرارداد با فرانت (app/src/services/api.js):
- خطاهای منطقی → 200 با {ok:false, msg} (فرانت پیام فارسی را مستقیم نشان می‌دهد)
- خطاهای ساختاری/اعتبارسنجی → 400 با {ok:false, msg}
- نقاط پایانی محافظت‌شده → هدر Authorization: Bearer <jwt>
"""
import random

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Order, Product, ShopUser, SiteSetting, SmsLog
from .permissions import IsShopAdmin
from .pricing import STATUS_LABELS, MAX_QTY_PER_LINE, compute_order, js_round, line_unit_price
from .seed import ensure_seed
from .serializers import (LoginSerializer, OrderCreateSerializer, OrderOutSerializer,
                          OrderStatusPatchSerializer, OrderTrackSerializer, ProductSerializer, ProductWriteSerializer,
                          RegisterSerializer)
from .sms import notify_new_order, notify_status_change, normalize_phone, provider_status, send_sms

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


def _weight_text(w):
    return 'عدد' if w == 1 else (f'{w // 1000} کیلوگرم' if w % 1000 == 0 else f'{w} گرم')


def torob_item(p):
    """یک محصول در قالب API ترب — قیمت و وزنِ پیش‌فرض همان است که صفحهٔ محصول نشان می‌دهد
    (وزن دوم فهرست)، تا قیمت فید و صفحه همیشه یکی باشد. قیمت‌ها به تومان."""
    ws = p.weights or [1]
    w = ws[min(1, len(ws) - 1)]
    price = line_unit_price(p, w)
    old = js_round(p.price * w / 1000) if p.disc else 0
    base = settings.SHOP_URL.rstrip('/')
    img = p.img or ''
    return {
        'title': f'{p.name} - {_weight_text(w)}',
        'subtitle': p.grade or '',
        'page_unique': str(p.id),
        'current_price': price,
        'old_price': old if old > price else 0,
        'availability': 'instock' if p.stock > 0 else 'outofstock',
        'category_name': CAT_NAMES.get(p.cat, p.cat),
        'image_link': img,
        'image_links': [img] if img else [],
        'page_url': f'{base}/product/{p.id}/',
        'short_desc': (p.desc or '')[:300],
        'spec': {'وزن': _weight_text(w), 'درجه': p.grade or '', 'دسته': CAT_NAMES.get(p.cat, p.cat)},
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
        return Response({'count': total, 'max_pages': pages,
                         'products': [torob_item(p) for p in qs[start:start + TOROB_PAGE_SIZE]]})

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


# ---------------- سفارش‌ها ----------------

class OrderCreateListView(APIView):
    """POST: ثبت سفارش (مهمان هم مجاز) — GET: فهرست سفارش‌ها (فقط مدیر)"""
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsShopAdmin()]
        return [AllowAny()]

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

        first_order = not Order.objects.filter(a_phone=addr['phone']).exists()
        try:
            money = compute_order(pairs, d.get('coupon'), d.get('shipType') or d.get('ship_type'), first_order)
        except ValueError as e:
            return fail(str(e))

        client_code = (d.get('client_code') or request.data.get('code') or '').strip().upper()
        user = request.user if (request.user.is_authenticated and request.user.phone == addr['phone']) else None

        with transaction.atomic():
            code = self._unique_code()
            order = Order.objects.create(
                code=code, client_code=client_code, user=user, status=0,
                a_name=addr['name'], a_phone=addr['phone'], a_prov=addr['prov'],
                a_city=addr['city'], a_addr=addr['addr'], note=d.get('note', ''), **money)
            for p, w, qty in pairs:
                unit = line_unit_price(p, w)
                order.items.create(pid=p.id, name=p.name, img=p.img, w=w, qty=qty,
                                   unit_price=unit, cost=unit * qty)

        notify_new_order(order)          # پیامک مشتری + مدیر (پس‌زمینه)
        return ok({'code': order.code, 'status': order.status, 'total': order.total,
                   'sub': order.sub, 'off': order.off, 'ship_cost': order.ship_cost})

    @staticmethod
    def _unique_code():
        for _ in range(50):
            code = f'KG-{random.randint(10000, 99999)}'
            if not Order.objects.filter(code=code).exists():
                return code
        return f'KG-{int(timezone.now().timestamp()) % 100000}'

    def get(self, request):
        qs = Order.objects.prefetch_related('items').all()
        st = request.query_params.get('status')
        if st not in (None, ''):
            if st not in ('0', '1', '2', '3'):
                return fail('وضعیت باید عددی ۰ تا ۳ باشد', 400)
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
        o = self._find(code)
        if not o:
            return fail('سفارشی با این کد پیدا نشد', 404)
        s = OrderStatusPatchSerializer(data=request.data)
        if not s.is_valid():
            return fail(first_msg(s.errors), 400)
        o.status = s.validated_data['status']
        o.save(update_fields=['status', 'updated_at'])
        notify_status_change(o, o.status)
        return ok({'code': o.code, 'status': o.status, 'status_label': STATUS_LABELS[o.status]})


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


class AdminStatsView(APIView):
    permission_classes = [IsShopAdmin]

    def get(self, request):
        orders = Order.objects.all()
        revenue = sum(orders.values_list('total', flat=True) or [0])
        st = provider_status()
        last_sms = SmsLog.objects.first()
        return ok({
            'products': Product.objects.count(),
            'orders': orders.count(),
            'users': ShopUser.objects.filter(role='user').count(),
            'revenue': revenue,
            'lowStock': Product.objects.filter(stock__lt=10, hide=False).count(),
            'statusLabels': STATUS_LABELS,
            'sms': {**st, 'sent': SmsLog.objects.count(),
                    'last': int(last_sms.ts.timestamp() * 1000) if last_sms else None},
        })


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
