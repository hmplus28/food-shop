"""ثبت مدل‌ها در پنل ادمین جنگو (dj-admin/) — برای مدیریت کامل دستی"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Order, Banner, ConsultRequest, Coupon, MediaFile, OrderEvent, Pack, Payment, TrustItem, LuckyPrize, LuckyWin, OrderItem, Page, Product, ShippingMethod, ShopUser, SiteSetting, SmsLog


@admin.register(ShopUser)
class ShopUserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'name', 'role', 'date_joined')
    search_fields = ('phone', 'name', 'username')
    list_filter = ('role',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'thumb', 'name', 'cat', 'price', 'consumer_price', 'disc', 'stock', 'hide')
    list_editable = ('price', 'consumer_price', 'stock', 'disc', 'hide')
    list_filter = ('cat', 'hide')
    search_fields = ('name',)

    @admin.display(description='تصویر')
    def thumb(self, obj):
        return format_html('<img src="{}" style="width:34px;height:34px;border-radius:8px">', obj.img) if obj.img else '—'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('pid', 'name', 'img', 'w', 'qty', 'unit_price', 'cost')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('code', 'a_name', 'a_phone', 'total', 'status', 'pay_status', 'created_at')
    list_filter = ('status', 'pay_status')
    search_fields = ('code', 'client_code', 'a_phone', 'a_name')
    inlines = [OrderItemInline]
    readonly_fields = ('code', 'client_code')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'kind', 'value', 'min_total', 'active', 'used', 'max_uses', 'expires_at')
    list_filter = ('kind', 'active')
    search_fields = ('code', 'label')


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('label', 'key', 'cost', 'days', 'active', 'sort')


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'group', 'kind', 'active', 'sort')


@admin.register(LuckyPrize)
class LuckyPrizeAdmin(admin.ModelAdmin):
    list_display = ('title', 'kind', 'value', 'weight', 'active')


@admin.register(LuckyWin)
class LuckyWinAdmin(admin.ModelAdmin):
    list_display = ('user', 'prize_title', 'created_at')


@admin.register(ConsultRequest)
class ConsultRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'topic', 'done', 'created_at')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'active', 'sort')


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ('name', 'now_price', 'cycle_hours', 'active', 'sort')


@admin.register(TrustItem)
class TrustItemAdmin(admin.ModelAdmin):
    list_display = ('day', 'name', 'price', 'active')


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'original', 'size', 'created_at')


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ('ts', 'provider', 'to', 'tag', 'ok')
    list_filter = ('provider', 'ok', 'tag')
    search_fields = ('to', 'text')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('track_id', 'order', 'amount', 'state', 'result', 'ref_number', 'created_at')
    list_filter = ('state', 'gateway')
    search_fields = ('track_id', 'order__code', 'ref_number')
    readonly_fields = ('order', 'gateway', 'track_id', 'amount', 'ref_number', 'card_number',
                       'state', 'result', 'message', 'created_at', 'updated_at')
