"""ثبت مدل‌ها در پنل ادمین جنگو (dj-admin/) — برای مدیریت کامل دستی"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem, OtpCode, Product, ShopUser, SmsLog


@admin.register(ShopUser)
class ShopUserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'name', 'role', 'date_joined')
    search_fields = ('phone', 'name', 'username')
    list_filter = ('role',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'thumb', 'name', 'cat', 'price', 'disc', 'stock', 'hide')
    list_editable = ('price', 'stock', 'disc', 'hide')
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
    list_display = ('code', 'a_name', 'a_phone', 'total', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('code', 'client_code', 'a_phone', 'a_name')
    inlines = [OrderItemInline]
    readonly_fields = ('code', 'client_code')


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'attempts', 'used', 'expires_at', 'last_sent')
    list_filter = ('used',)


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ('ts', 'provider', 'to', 'tag', 'ok')
    list_filter = ('provider', 'ok', 'tag')
    search_fields = ('to', 'text')
