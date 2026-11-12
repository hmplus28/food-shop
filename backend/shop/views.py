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

from .models import (Banner, ConsultRequest, MediaFile, OrderEvent, Pack, TrustItem, Coupon, LuckyPrize, LuckyWin, Order, OrderItem, Page, Product, ShippingMethod,
                     ShopUser, SiteSetting, SmsLog)
from .permissions import IsShopAdmin
from .pricing import CANCELLED, STATUS_LABELS, MAX_QTY_PER_LINE, compute_order, js_round, line_unit_price
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


def torob_item(p):
    """یک محصول در قالب API ترب — قیمت و وزنِ پیش‌فرض همان است که صفحهٔ محصول نشان می‌دهد
    (وزن دوم فهرست)، تا قیمت فید و صفحه همیشه یکی باشد. قیمت‌ها به تومان."""
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
                for it in o.items.all():                       # بازگرداندن موجودی و آمار فروش
                    Product.objects.filter(id=it.pid).update(stock=F('stock') + it.qty)
                    Product.objects.filter(id=it.pid, sold__gte=it.qty).update(sold=F('sold') - it.qty)
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


def _dashboard_extras():
    """داده‌های نمودار/لیست داشبورد: فروش ۷ روز اخیر، پرفروش‌ها، وضعیت سفارش‌ها، کم‌موجودی‌ها"""
    from django.db.models import Count, Sum
    from django.db.models.functions import TruncDate
    today = timezone.localdate()
    since = today - timezone.timedelta(days=6)
    rows = {r['d']: r for r in Order.objects.filter(created_at__date__gte=since)
            .exclude(status=CANCELLED).annotate(d=TruncDate('created_at')).values('d').annotate(n=Count('id'), s=Sum('total'))}
    daily = []
    for i in range(7):
        d = since + timezone.timedelta(days=i)
        r = rows.get(d, {})
        daily.append({'date': d.isoformat(), 'orders': r.get('n', 0), 'revenue': r.get('s') or 0})
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
        revenue = sum(orders.exclude(status=CANCELLED).values_list('total', flat=True) or [0])
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


class SiteView(APIView):
    """GET /site — همهٔ محتوای عمومی در یک درخواست: اطلاعات تماس/متن‌ها، ارسال، فهرست صفحات، کارت شانس"""
    permission_classes = [AllowAny]

    def get(self, request):
        lucky = _setting('lucky', DEFAULT_LUCKY)
        ensure_seed()
        return ok({'info': _setting('info', DEFAULT_INFO), 'shipping': _shipping_public(), **_home_public(),
                   'pages': [_page_brief(p) for p in Page.objects.filter(active=True)],
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
    last = LuckyWin.objects.filter(user=user).first() if user else None
    if last:
        nxt = last.created_at + timezone.timedelta(hours=int(cfg.get('cooldownHours') or 24))
        if timezone.now() < nxt:
            return cfg, False, int(nxt.timestamp() * 1000)
    return cfg, True, None


class LuckyStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        cfg, can, nxt = _lucky_state(user)
        return ok({'enabled': bool(cfg.get('enabled')), 'loggedIn': bool(user),
                   'canSpin': bool(user and can), 'nextAt': nxt, 'cooldownHours': cfg.get('cooldownHours')})


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
                   'nextAt': int((timezone.now() + timezone.timedelta(hours=int(cfg.get('cooldownHours') or 24))).timestamp() * 1000)})


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

_INFO_KEYS = {'shopName': 80, 'phone': 40, 'phoneTel': 20, 'whatsapp': 20, 'email': 120, 'address': 300, 'hours': 120,
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
                   'cooldownHours': _int(request.data.get('cooldownHours', 24), 1, 24 * 90, 'فاصلهٔ چرخش (ساعت)'),
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
