"""مجوزهای سفارشی — دسترسی مدیر فروشگاه"""
from rest_framework.permissions import BasePermission


class IsShopAdmin(BasePermission):
    """کاربر احراز هویت‌شده با نقش admin (توکن JWT پنل مدیر)"""
    message = 'دسترسی فقط برای مدیر فروشگاه'

    def has_permission(self, request, view):
        u = getattr(request, 'user', None)
        return bool(u and u.is_authenticated and (u.role == 'admin' or u.is_staff))
