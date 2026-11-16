"""تست سرتاسری منوی قابل مدیریت — /site (عمومی) + CRUD ادمین (cats/menu)"""
import os
import sys

BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, os.path.abspath(BACKEND))
os.chdir(os.path.abspath(BACKEND))

os.environ['DB_ENGINE'] = 'sqlite3'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.test import Client  # noqa: E402
from shop.models import NavCat, NavLink, Product  # noqa: E402
from shop.seed import ensure_admin, ensure_nav, seed_products  # noqa: E402
from django.conf import settings  # noqa: E402

c = Client()

# 1) seed منو (تولید هم فعال است) + دمو محصول برای تست گارد حذف
settings.SEED_FAKE = True
ensure_nav()
seed_products()
ensure_admin()

# 2) /site عمومی
r = c.get('/api/v1/site')
assert r.status_code == 200, r.status_code
d = r.json()
cats, menu = d.get('cats'), d.get('menu')
assert isinstance(cats, list) and len(cats) == 13, f'cats={len(cats or [])}'
assert cats[0]['id'] == 'ajil' and cats[0]['name'] == 'آجیل و مغزها', cats[0]
assert cats[0]['icon'] == 'i-nut' and cats[0]['subs'], cats[0]
assert cats[12]['hot'] is True and cats[12]['feat']['img'], cats[12]
assert menu and menu[0]['label'] == 'مشاوره خرید' and menu[1]['link'] == '/track', menu
print(f"OK /site → cats={len(cats)}, menu={len(menu)}")

# 3) ورود مدیر
admin, _ = ensure_admin()
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402
tok = str(RefreshToken.for_user(admin).access_token)
H = {'HTTP_AUTHORIZATION': f'Bearer {tok}'}

# 4) GET /admin/cats با شمارش محصولات
r = c.get('/api/v1/admin/cats', **H)
assert r.status_code == 200, r.status_code
rows = r.json()['cats']
assert len(rows) == 13
pist = next(x for x in rows if x['slug'] == 'pistachio')
assert pist['products'] == 4, pist
assert {k: v for k, v in pist.items() if k in ('name', 'icon', 'sort', 'hot', 'active', 'feat', 'subs')}
print(f"OK /admin/cats → 13 rows, pistachio products={pist['products']}")

# 5) POST دستهٔ جدید
r = c.post('/api/v1/admin/cats', {'slug': 'coffee', 'name': 'قهوه و کاکائو', 'icon': 'i-star',
                                  'subs': ['قهوه اسپرسو'], 'feat': {'img': 'img/2c259b7044c5.jpg', 't': 'قهوه', 's': 'تازه'},
                                  'hot': True, 'active': True, 'sort': 90},
           content_type='application/json', **H)
assert r.status_code == 200, (r.status_code, r.content)
cid = r.json()['cat']['id']
assert r.json()['cat']['hot'] is True
print(f"OK POST /admin/cats → id={cid}")

# 6) slug تکراری → خطای فارسی
r = c.post('/api/v1/admin/cats', {'slug': 'coffee', 'name': 'دوباره', 'icon': 'i-nut', 'subs': []},
           content_type='application/json', **H)
assert r.json().get('ok') is False and 'از قبل' in r.json()['msg'], r.json()

# 7) PUT تغییر نام + تغییر slug با جابه‌جایی محصولات (coffee خالی است؛ تست slug-change با pistachio)
pid = next(x for x in rows if x['slug'] == 'pistachio')['id']
r = c.put(f'/api/v1/admin/cats/{pid}', {'slug': 'pistachio2', 'name': 'پسته و مغز پسته', 'icon': 'i-leaf',
                                        'subs': ['پسته اکبری'], 'feat': {'img': 'img/ec01895c5c0b.jpg', 't': 'x', 's': 'y'},
                                        'sort': 3, 'hot': False, 'active': True},
          content_type='application/json', **H)
assert r.status_code == 200, (r.status_code, r.content)
assert Product.objects.filter(cat='pistachio2').count() == 4
assert Product.objects.filter(cat='pistachio').count() == 0
print("OK PUT slug-change → products migrated to 'pistachio2'")
# برگرداندن
r = c.put(f'/api/v1/admin/cats/{pid}', {'slug': 'pistachio', 'name': 'پسته', 'icon': 'i-nut',
                                        'subs': ['پسته اکبری'], 'feat': {'img': 'img/ec01895c5c0b.jpg', 't': 'x', 's': 'y'},
                                        'sort': 1, 'hot': False, 'active': True},
          content_type='application/json', **H)
assert r.status_code == 200 and Product.objects.filter(cat='pistachio').count() == 4

# 8) حذف دستهٔ پر از محصول → گارد
r = c.delete(f'/api/v1/admin/cats/{pid}', **H)
assert r.json().get('ok') is False and 'محصول' in r.json()['msg'], r.json()
print(f"OK delete guard → {r.json()['msg']}")

# 9) حذف دستهٔ خالی جدید
r = c.delete(f'/api/v1/admin/cats/{cid}', **H)
assert r.json().get('ok') is True, r.json()

# 10) پیوندهای منو: POST + PUT + DELETE
r = c.post('/api/v1/admin/menu', {'label': 'باشگاه مشتریان', 'icon': 'i-gift', 'link': '/account', 'sort': 5},
           content_type='application/json', **H)
assert r.status_code == 200, r.content
lid = r.json()['link']['id']
r = c.put(f'/api/v1/admin/menu/{lid}', {'label': 'باشگاه مشتریان', 'icon': 'i-tag', 'link': 'https://example.com', 'sort': 5, 'active': True},
          content_type='application/json', **H)
assert r.status_code == 200 and r.json()['link']['icon'] == 'i-tag', r.content
r = c.post('/api/v1/admin/menu', {'label': 'بدون لینک', 'icon': 'i-tag', 'link': ''},
           content_type='application/json', **H)
assert r.json().get('ok') is False, r.json()
r = c.delete(f'/api/v1/admin/menu/{lid}', **H)
assert r.json().get('ok') is True

# 11) غیرفعال کردن یک دسته → از /site حذف می‌شود
r = c.put(f'/api/v1/admin/cats/{pid}', {'slug': 'pistachio', 'name': 'پسته', 'icon': 'i-nut', 'subs': [],
                                        'feat': {'img': '', 't': '', 's': ''}, 'sort': 1, 'active': False},
          content_type='application/json', **H)
assert r.status_code == 200
cats2 = c.get('/api/v1/site').json()['cats']
assert len(cats2) == 12 and all(x['id'] != 'pistachio' for x in cats2)
print("OK hide cat → /site cats=12 (بدون pistachio)")

# 12) دسترسی بدون توکن → 401/403
r = c.get('/api/v1/admin/cats')
assert r.status_code in (401, 403), r.status_code
print("OK auth guard →", r.status_code)

# cleanup سندباکس: برگرداندن وضعیت فعال
r = c.put(f'/api/v1/admin/cats/{pid}', {'slug': 'pistachio', 'name': 'پسته', 'icon': 'i-nut', 'subs': ['پسته اکبری'],
                                        'feat': {'img': 'img/ec01895c5c0b.jpg', 't': 'پسته اکبری', 's': 'ملکه پسته‌ها'},
                                        'sort': 1, 'active': True}, content_type='application/json', **H)
assert r.status_code == 200
print("\nALL BACKEND TESTS PASSED ✅")
