"""تنظیمات جنگو — فروشگاه خانم گل (بک‌اند REST + پنل پیامک)

همهٔ تنظیمات محیطی از فایل backend/.env یا متغیرهای محیطی خوانده می‌شود؛
نمونهٔ کامل در backend/.env.example هست. در نبود هر تنظیم، مقدار پیش‌فرضِ
امن و «آماده‌اجرا» گذاشته می‌شود تا پروژه با دستور ساده بالا بیاید.
"""
from pathlib import Path
import os
import secrets

from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent.parent
# .env را خودمان می‌خوانیم و عمداً داخل os.environ نمی‌ریزیم: زیر Passenger/cPanel پایتون
# با locale ‏ASCII اجرا می‌شود و os.environ[k]=«مقدار فارسی» (مثل SHOP_NAME) با
# UnicodeEncodeError می‌میرد (۵۰۰ روی همهٔ مسیرها). متغیرهای واقعیِ محیط همچنان اولویت دارند.
try:
    _ENV_FILE = {k: v for k, v in dotenv_values(os.environ.get('KHANOMGOL_ENV_FILE') or (BASE_DIR / '.env'), encoding='utf-8').items() if v is not None}
except OSError:
    _ENV_FILE = {}


def _say(msg):
    """چاپ امن: stdout زیر Passenger ممکن است ASCII باشد"""
    try:
        print(msg)
    except (UnicodeEncodeError, OSError):
        pass


def env(name, default=''):
    v = os.environ.get(name)
    if v in (None, ''):
        v = _ENV_FILE.get(name)
    return v if v not in (None, '') else default

def env_int(name, default):
    try:
        return int(env(name, str(default)))
    except (TypeError, ValueError):
        return default

def env_bool(name, default=False):
    return env(name, 'true' if default else 'false').strip().lower() in ('1', 'true', 'yes', 'on', 'بله')

# ---------- کلید امنیتی ----------
# اگر SECRET_KEY تنظیم نشده باشد یک‌بار ساخته و در backend/.env ذخیره می‌شود
# تا بین ری‌استارت‌ها ثابت بماند (توکن‌ها و سشن‌ها باطل نشوند).
def _ensure_secret_key():
    key = env('SECRET_KEY')
    if key:
        return key
    key = secrets.token_urlsafe(64)
    try:
        env_file = BASE_DIR / '.env'
        prefix = ''
        if env_file.exists():
            content = env_file.read_text(encoding='utf-8')
            if 'SECRET_KEY=' in content:
                return key          # فایل هست ولی کلید خالی است؛ ثابت نمی‌ماند
            prefix = content.rstrip() + '\n'
        env_file.write_text(prefix + f'SECRET_KEY={key}\n', encoding='utf-8')
        _say('[خانم گل] SECRET_KEY ساخته شد و در backend/.env ذخیره شد.')
    except OSError:
        _say('[خانم گل] هشدار: SECRET_KEY ذخیره نشد؛ پس از هر ری‌استارت عوض می‌شود.')
    return key

SECRET_KEY = _ensure_secret_key()
DEBUG = env_bool('DEBUG', False)
ALLOWED_HOSTS = [h.strip() for h in env('ALLOWED_HOSTS', '*').split(',') if h.strip()]

# ---------- اپلیکیشن‌ها ----------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

# ---------- پایگاه داده ----------
# توسعهٔ محلی: پیش‌فرض SQLite (بدون نیاز به سرور جدا).
# هاست cPanel: با DB_ENGINE=mysql و کلیدهای DB_* دیتابیس MySQL فعال می‌شود
# (نمونهٔ کامل در backend/.env.example؛ دیتابیس از cPanel → MySQL® Databases ساخته می‌شود).
DB_ENGINE = env('DB_ENGINE', 'sqlite3').strip().lower()

if DB_ENGINE in ('mysql', 'mariadb'):
    # درایور ترجیحی mysqlclient است؛ اگر نصب نبود PyMySQL (خالص‌پایتون، بدون
    # نیاز به کامپایل — روی هاست اشتراکی مطمئن‌تر) خودکار جایگزین می‌شود.
    try:
        import MySQLdb  # noqa: F401
    except ImportError:
        try:
            import pymysql
            pymysql.install_as_MySQLdb()
        except ImportError as exc:
            raise RuntimeError(
                'DB_ENGINE=mysql است اما درایور MySQL پیدا نشد؛ '
                'در محیط مجازی اجرا کنید: pip install PyMySQL'
            ) from exc
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST', 'localhost'),
            'PORT': env_int('DB_PORT', 3306),
            'OPTIONS': {
                'charset': 'utf8mb4',
                # داده‌های ناقص را بپذیر نما؛ رفتار یکسان با توسعه
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            # اتصال ماندگار برای پاسخ سریع‌تر زیر Passenger
            'CONN_MAX_AGE': env_int('DB_CONN_MAX_AGE', 60),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------- احراز هویت ----------
AUTH_USER_MODEL = 'shop.ShopUser'

AUTH_PASSWORD_VALIDATORS = []   # اعتبارسنجی رمز در سریالایزر خودمان انجام می‌شود (حداقل ۴ کاراکتر)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',   # فقط JSON — بدون نیاز به collectstatic برای API
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '300/hour',
        'auth': '60/hour',
        'otp': '20/hour',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': __import__('datetime').timedelta(days=env_int('TOKEN_TTL_DAYS', 30)),
    'REFRESH_TOKEN_LIFETIME': __import__('datetime').timedelta(days=env_int('TOKEN_TTL_DAYS', 30) * 2),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'uid',
}

# ---------- CORS ----------
# CORS_ORIGINS=* برای شروع راحت است؛ در تولید حتماً دامنهٔ فرانت را بدهید:
# CORS_ORIGINS=https://hmplus28.github.io,https://example.ir
_cors = [o.strip() for o in env('CORS_ORIGINS', '*').split(',') if o.strip()]
if _cors == ['*']:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = _cors
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type', 'origin',
    'user-agent', 'x-csrftoken', 'x-requested-with',
]

# ---------- زبان و زمان ----------
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# ---------- استاتیک (برای پنل ادمین جنگو) ----------
# زیر Passenger وقتی برنامه روی زیرمسیر سرو می‌شود (الگوی همین پروژه:
# Application URL = /food-shop)، این دو مقدار در .env لازم است تا لینک‌های
# پنل ادمین و CSS آن درست کار کنند:
#   FORCE_SCRIPT_NAME=/food-shop
#   STATIC_URL=/food-shop/static/
# (Whitenoise خودش بخش مسیرِ اسکریپت را از STATIC_URL جدا می‌کند و به
#  path_info — که Passenger بدون پیشوند /food-shop می‌دهد — تطبیق می‌دهد.)
STATIC_URL = env('STATIC_URL', 'static/')
FORCE_SCRIPT_NAME = env('FORCE_SCRIPT_NAME') or None
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    # فشرده‌سازی بدون «manifest»: اگر collectstatic فراموش شود، پنل ادمین
    # به‌جای خطای ۵۰۰ فقط CSS از دست می‌دهد (مقاوم در استقرار دستی)
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------- لاگ خطاها ----------
# خطاهای ۵۰۰ (traceback کامل) در backend/logs/django-error.log ثبت می‌شوند؛
# زیر Passenger/cPanel این تنها راه ساده برای دیدن علت واقعی خطای ۵۰۰ است.
LOG_DIR = BASE_DIR / 'logs'
_handlers = {'console': {'class': 'logging.StreamHandler', 'level': 'ERROR'}}
try:
    LOG_DIR.mkdir(exist_ok=True)
    _handlers['file'] = {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': str(LOG_DIR / 'django-error.log'),
        'maxBytes': 1_000_000, 'backupCount': 3, 'encoding': 'utf-8',
        'level': 'ERROR',
    }
except OSError:
    pass
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'std': {'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'}},
    'handlers': {k: {**v, 'formatter': 'std'} for k, v in _handlers.items()},
    'loggers': {
        'django.request': {'handlers': list(_handlers), 'level': 'ERROR', 'propagate': False},   # فقط ۵xx (۴xx/۴۲۹ لاگ را شلوغ می‌کند)
        'shop': {'handlers': list(_handlers), 'level': 'ERROR', 'propagate': False},
    },
}

# ---------- امنیت در حالت تولید ----------
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'same-origin'

# ---------- امنیت TLS (پس از فعال‌شدن https روی هاست روشن کنید) ----------
# در backend/.env.example مستند شده؛ تا قبل از نصب SSL همه پیش‌فرض خاموش‌اند
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)
SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS', 0)
if env_bool('SECURE_PROXY_SSL_HEADER', False):
    # فقط وقتی https واقعی از هدر X-Forwarded-Proto می‌آید (پشت پروکسی/Passenger)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ---------- CSRF ----------
# برای POST فرم‌های پنل ادمین جنگو از دامنهٔ اصلی؛ API جنگو (JSON) تحت‌تأثیر نیست
_csrf = [o.strip() for o in env('CSRF_TRUSTED_ORIGINS').split(',') if o.strip()]
if _csrf:
    CSRF_TRUSTED_ORIGINS = _csrf

# ---------- فروشگاه و پنل پیامک ----------
SHOP_NAME = env('SHOP_NAME', 'فروشگاه خانم گل')
SHOP_URL = env('SHOP_URL', 'https://hmplus28.github.io/food-shop/')
SHOP_NOTIFY_PHONE = env('SHOP_NOTIFY_PHONE')
SMS_ORDER_TO_CUSTOMER = env_bool('SMS_ORDER_TO_CUSTOMER', True)
SMS_STATUS_TO_CUSTOMER = env_bool('SMS_STATUS_TO_CUSTOMER', True)

# --- سرویس‌دهندهٔ پیامک: console | kavenegar | smsir | ghasedak | melipayamak ---
SMS_PROVIDER = env('SMS_PROVIDER', 'console').strip().lower()
SMS_SENDER = env('SMS_SENDER')
KAVENEGAR_API_KEY = env('KAVENEGAR_API_KEY')
KAVENEGAR_OTP_TEMPLATE = env('KAVENEGAR_OTP_TEMPLATE')
SMSIR_API_KEY = env('SMSIR_API_KEY')
SMSIR_OTP_TEMPLATE_ID = env('SMSIR_OTP_TEMPLATE_ID')
SMSIR_LINE = env('SMSIR_LINE')
GHASEDAK_API_KEY = env('GHASEDAK_API_KEY')
GHASEDAK_OTP_TEMPLATE = env('GHASEDAK_OTP_TEMPLATE')
GHASEDAK_LINE = env('GHASEDAK_LINE')
MELIPAYAMAK_USERNAME = env('MELIPAYAMAK_USERNAME')
MELIPAYAMAK_PASSWORD = env('MELIPAYAMAK_PASSWORD')
MELIPAYAMAK_FROM = env('MELIPAYAMAK_FROM')

ADMIN_USERNAME = env('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = env('ADMIN_PASSWORD', 'admin1234')
ADMIN_PHONE = env('ADMIN_PHONE', '09120000000')

OTP_TTL = env_int('OTP_TTL', 120)
OTP_COOLDOWN = env_int('OTP_COOLDOWN', 90)
OTP_HOURLY = env_int('OTP_HOURLY', 5)
OTP_MAX_ATTEMPTS = env_int('OTP_MAX_ATTEMPTS', 5)
