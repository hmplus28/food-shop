"""مسیرهای API فروشگاه — پیشوند /api/v1/"""
from django.urls import path

from . import views

urlpatterns = [
    path('health', views.HealthView.as_view()),

    # کد تخفیف (عمومی)
    path('coupons/check', views.CouponCheckView.as_view()),

    # ظاهر سایت (تم/رنگ)
    path('settings', views.SiteSettingsView.as_view()),
    path('admin/settings', views.AdminSiteSettingsView.as_view()),

    # فید ترب
    path('torob/products', views.TorobProductsView.as_view()),

    # حساب کاربری
    path('auth/register', views.RegisterView.as_view()),
    path('auth/login', views.LoginView.as_view()),
    path('auth/me', views.MeView.as_view()),

    # محصولات
    path('products', views.ProductListCreateView.as_view()),
    path('products/<int:pk>', views.ProductDetailView.as_view()),

    # سفارش‌ها (mine قبل از <code> باشد)
    path('orders', views.OrderCreateListView.as_view()),
    path('orders/mine', views.MyOrdersView.as_view()),
    path('orders/<str:code>', views.OrderTrackPatchView.as_view()),

    # مدیر فروشگاه
    path('admin/login', views.AdminLoginView.as_view()),
    path('admin/stats', views.AdminStatsView.as_view()),
    path('admin/users', views.AdminUsersView.as_view()),
    path('admin/users/<int:pk>', views.AdminUserDetailView.as_view()),
    path('admin/coupons', views.AdminCouponsView.as_view()),
    path('admin/coupons/<int:pk>', views.AdminCouponDetailView.as_view()),
    path('admin/sms', views.AdminSmsLogView.as_view()),
    path('admin/sms/test', views.AdminSmsTestView.as_view()),
]
