"""مسیرهای اصلی پروژه — فروشگاه خانم گل"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from shop.seed import ensure_seed


def api_root(request):
    ensure_seed()
    return JsonResponse({
        'ok': True,
        'name': 'khanom-gol-api',
        'version': '1.0.0',
        'docs': 'README در پوشهٔ backend',
        'endpoints': [
            'api/v1/health', 'api/v1/auth/register', 'api/v1/auth/login',
            'api/v1/auth/otp/request', 'api/v1/auth/otp/verify', 'api/v1/auth/me',
            'api/v1/products', 'api/v1/orders', 'api/v1/orders/<code>',
            'api/v1/admin/login', 'api/v1/admin/stats', 'api/v1/admin/sms',
        ],
    })


urlpatterns = [
    path('', api_root),
    path('dj-admin/', admin.site.urls),      # پنل ادمین جنگو (اختیاری، برای مدیریت کامل)
    path('api/v1/', include('shop.urls')),
]
