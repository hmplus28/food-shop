"""سریالایزرهای فروشگاه خانم گل

نکتهٔ قرارداد: فرانت برای خطاهای منطقی (رمز اشتباه، شماره تکراری و…) پاسخ
200 با {ok:false, msg} را انتظار دارد؛ خطاهای اعتبارسنجی ساختاری هم با
{ok:false, msg} و کد 400 برمی‌گردند تا پیام فارسی مستقیم نمایش داده شود.
"""
from django.contrib.auth.password_validation import validate_password  # noqa: F401 (مرجع مستندات)
from rest_framework import serializers

from .models import Order, OrderItem, Product, ShopUser


# ---------------- کاربران ----------------

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3, max_length=120, error_messages={
        'min_length': 'نام و نام خانوادگی را کامل وارد کنید',
        'required': 'نام و نام خانوادگی را وارد کنید',
        'blank': 'نام و نام خانوادگی را وارد کنید',
    })
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(min_length=4, max_length=128, write_only=True, error_messages={
        'min_length': 'رمز عبور حداقل ۴ کاراکتر باشد',
        'required': 'رمز عبور را وارد کنید',
        'blank': 'رمز عبور را وارد کنید',
    })

    def validate_phone(self, v):
        from .sms import normalize_phone
        p = normalize_phone(v)
        if not p:
            raise serializers.ValidationError('شماره موبایل معتبر وارد کنید (۰۹…)')
        return p


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(max_length=128, write_only=True)


# ---------------- محصولات (فیلدها = قرارداد normalizeProduct فرانت) ----------------

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'cat', 'img', 'price', 'weights', 'stock', 'disc',
                  'grade', 'rate', 'sold', 'tags', 'sec', 'desc', 'hide']


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'cat', 'img', 'price', 'weights', 'stock', 'disc',
                  'grade', 'rate', 'sold', 'tags', 'sec', 'desc', 'hide']

    def validate_price(self, v):
        if v is None or v <= 0:
            raise serializers.ValidationError('قیمت پایه معتبر وارد کنید')
        return v

    def validate_disc(self, v):
        if v and not (0 <= v <= 90):
            raise serializers.ValidationError('تخفیف بین ۰ تا ۹۰ درصد است')
        return v or 0

    def validate_weights(self, v):
        if not v:
            return [500]
        try:
            out = sorted({int(w) for w in v if int(w) > 0})
        except (TypeError, ValueError):
            raise serializers.ValidationError('وزن‌ها باید عدد باشند')
        return out or [500]


# ---------------- سفارش‌ها ----------------

class OrderItemInputSerializer(serializers.Serializer):
    pid = serializers.IntegerField(min_value=1)
    w = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1, max_value=20)


class OrderCreateSerializer(serializers.Serializer):
    """بدنهٔ ارسالی از stores/orders.js — فیلدهای مالی سمت سرور دوباره محاسبه می‌شوند."""
    items = OrderItemInputSerializer(many=True)
    coupon = serializers.CharField(max_length=40, required=False, allow_blank=True, default='')
    shipType = serializers.CharField(required=False, allow_blank=True, default='')
    ship_type = serializers.CharField(required=False, allow_blank=True, default='')
    client_code = serializers.CharField(required=False, allow_blank=True, default='')
    note = serializers.CharField(required=False, allow_blank=True, default='', max_length=1000)
    addr = serializers.DictField(child=serializers.CharField(allow_blank=True))

    def validate_addr(self, v):
        from .sms import normalize_phone
        name = (v.get('name') or '').strip()
        phone = normalize_phone(v.get('phone'))
        city = (v.get('city') or '').strip()
        addr = (v.get('addr') or '').strip()
        if len(name) < 3:
            raise serializers.ValidationError('نام و نام خانوادگی گیرنده را کامل وارد کنید')
        if not phone:
            raise serializers.ValidationError('شماره موبایل گیرنده معتبر نیست (۰۹…)')
        if not city:
            raise serializers.ValidationError('شهر را وارد کنید')
        if len(addr) < 10:
            raise serializers.ValidationError('آدرس کامل پستی را وارد کنید')
        return {'name': name, 'phone': phone, 'prov': (v.get('prov') or '').strip(),
                'city': city, 'addr': addr}

    def validate_items(self, v):
        if not v or len(v) > 30:
            raise serializers.ValidationError('سبد خرید خالی است یا بیش از حد بزرگ است')
        return v


class OrderItemOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['pid', 'name', 'img', 'w', 'qty', 'unit_price', 'cost']


class OrderOutSerializer(serializers.ModelSerializer):
    ts = serializers.SerializerMethodField()
    items = OrderItemOutSerializer(many=True, read_only=True)
    addr = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['code', 'client_code', 'status', 'ts', 'items', 'sub', 'off', 'coupon',
                  'ship_cost', 'ship_type', 'ship_label', 'ship_days', 'total', 'addr', 'note']

    def get_ts(self, obj):
        return int(obj.created_at.timestamp() * 1000)

    def get_addr(self, obj):
        return {'name': obj.a_name, 'phone': obj.a_phone, 'prov': obj.a_prov,
                'city': obj.a_city, 'addr': obj.a_addr}


class OrderTrackSerializer(serializers.ModelSerializer):
    """پاسخ عمومی پیگیری — حداقلِ اطلاعاتی که صفحهٔ پیگیری لازم دارد"""
    ts = serializers.SerializerMethodField()
    items = OrderItemOutSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['code', 'status', 'ts', 'total', 'ship_label', 'ship_days', 'items']

    def get_ts(self, obj):
        return int(obj.created_at.timestamp() * 1000)


class OrderStatusPatchSerializer(serializers.Serializer):
    status = serializers.IntegerField(min_value=0, max_value=3)
