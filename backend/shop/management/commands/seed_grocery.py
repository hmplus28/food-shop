"""سید یک‌بارمصرف کالاهای خواربار:  python manage.py seed_grocery

- دسته‌های منوی خواربار (روغن پخت‌وپز، سرخ‌کردنی، تن‌ماهی، چای، رب) — اگر نبود می‌سازد
- ۱۹ محصول با عکس واقعی (از shop/seed_media/ ریپو → کتابخانهٔ تصاویر سرور)
- قیمت ۰ = «تماس بگیرید» در فروشگاه
- روش ارسال «تحویل حضوری در فروشگاه» (هزینهٔ صفر)
اجرای دوباره ایمن است (ایمپوتنت) و چیزی را دوباره نمی‌سازد.
"""
from django.core.management.base import BaseCommand

from shop.grocery import seed_grocery


class Command(BaseCommand):
    help = 'درج کالاهای خواربار (روغن، تن‌ماهی، چای، رب، زعفران و زرشک) با تصویر + روش ارسال حضوری — ایمپوتنت'

    def handle(self, *args, **options):
        r = seed_grocery()
        self.stdout.write(self.style.SUCCESS(
            f"تصاویر: {r['images']['new']} جدید / {r['images']['kept']} از قبل — در MEDIA_ROOT و کتابخانهٔ ادمین"))
        self.stdout.write(self.style.SUCCESS(
            f"دسته‌های منو: {r['categories']['new']} جدید / {r['categories']['kept']} از قبل"))
        if r['products']['new']:
            self.stdout.write(self.style.SUCCESS(f"محصولات جدید ({len(r['products']['new'])}):"))
            for n in r['products']['new']:
                self.stdout.write(f'  + {n}')
        self.stdout.write(self.style.SUCCESS(f"محصولات از قبل بوده: {r['products']['kept']}"
                                             + (f" — برچسب صفحهٔ اصلی (best) برای {r['products']['home_updated']} مورد اضافه شد" if r['products'].get('home_updated') else '')))
        self.stdout.write(self.style.SUCCESS(
            'روش ارسال «تحویل حضوری»: ' + ('ساخته شد' if r['hadir_created'] else 'از قبل بوده')))
        self.stdout.write(self.style.SUCCESS(f"جمع محصولات فروشگاه: {r['products_total']}"))
