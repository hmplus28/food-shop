"""دستور مدیریتی آماده‌سازی فروشگاه: python manage.py seed_shop"""
from django.conf import settings
from django.core.management.base import BaseCommand

from shop.seed import seed_all


class Command(BaseCommand):
    help = 'ساخت حساب مدیر و درج ۲۸ محصول پایهٔ فروشگاه خانم گل'

    def handle(self, *args, **options):
        r = seed_all()
        self.stdout.write(self.style.SUCCESS(
            f"محصولات: {r['products_total']} مورد (درج اولیه: {'بله' if r['products_seeded'] else 'خیر — قبلاً بوده'})"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"مدیر فروشگاه: {r['admin_username']} / موبایل {r['admin_phone']} (ساخته شد: {'بله' if r['admin_created'] else 'خیر'})"
        ))
        if settings.ADMIN_PASSWORD == 'admin1234':
            self.stdout.write(self.style.WARNING('هشدار: رمز مدیر هنوز پیش‌فرض است — در backend/.env عوض کنید (ADMIN_PASSWORD=…)'))
