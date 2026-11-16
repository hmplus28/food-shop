"""دستور مدیریتی آماده‌سازی فروشگاه: python manage.py seed_shop

حالت‌ها:
- بدون پرچم: فقط ساخت/به‌روزرسانی حساب مدیر (در تولید همین کافی است؛ بدون محصول فیک)
- ‎--fake‎: درج ۲۸ محصول نمونه + محتوای نمونهٔ صفحهٔ اصلی (فقط توسعه/دمو؛ معادل SEED_FAKE=1)
- ‎--purge‎: حذف همهٔ محصولات از دیتابیس (شروع از صفر؛ با ‎--yes‎ بدون پرسش)
"""
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from shop.seed import purge_all_products, seed_all


class Command(BaseCommand):
    help = 'مدیریت دادهٔ فروشگاه: حساب مدیر (همیشه) + محصولات نمونه (فقط با --fake) + پاک‌سازی کاتالوگ (--purge)'

    def add_arguments(self, parser):
        parser.add_argument('--fake', action='store_true', help='درج ۲۸ محصول نمونه و محتوای نمونهٔ صفحهٔ اصلی (فقط توسعه/دمو)')
        parser.add_argument('--purge', action='store_true', help='حذف همهٔ محصولات از دیتابیس (سفارش‌های قبلی سالم می‌مانند)')
        parser.add_argument('--yes', action='store_true', help='با --purge: بدون پرسش تأیید (برای اسکریپت/SSH)')

    def handle(self, *args, **options):
        if options['purge']:
            if not options['yes'] and sys.stdin is not None and sys.stdin.isatty():
                self.stdout.write(self.style.WARNING('همهٔ محصولات برای همیشه حذف می‌شوند؛ سفارش‌های قبلی سالم می‌مانند.'))
                a = input('تأیید: بنویسید «حذف»: ').strip()
                if a != 'حذف':
                    raise CommandError('تأیید نشد؛ انصراف.')
            n = purge_all_products()
            self.stdout.write(self.style.SUCCESS(f'{n} محصول از دیتابیس حذف شد.'))
        if options['fake']:
            os.environ['SEED_FAKE'] = '1'                       # فقط برای همین اجرا؛ فایل .env را تغییر نمی‌دهد
            settings.SEED_FAKE = True
        r = seed_all()
        if options['fake'] or r['seed_fake']:
            self.stdout.write(self.style.SUCCESS(
                f"محصولات نمونه: {r['products_total']} مورد (درج اولیه: {'بله' if r['products_seeded'] else 'خیر — قبلاً بوده'})"
            ))
        else:
            self.stdout.write('درج محصولات نمونه: خاموش است (پیش‌فرض تولید). برای دمو: ‎seed_shop --fake‎ یا SEED_FAKE=1 در .env')
        self.stdout.write(self.style.SUCCESS(
            f"مدیر فروشگاه: {r['admin_username']} / موبایل {r['admin_phone']} (ساخته شد: {'بله' if r['admin_created'] else 'خیر'})"
        ))
        if settings.ADMIN_PASSWORD == 'admin1234':
            self.stdout.write(self.style.WARNING('هشدار: رمز مدیر هنوز پیش‌فرض است — در backend/.env عوض کنید (ADMIN_PASSWORD=…)'))
