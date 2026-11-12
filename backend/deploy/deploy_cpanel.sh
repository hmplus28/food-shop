#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  فروشگاه خانم گل (backend) — اسکریپت استقرار روی هاست اشتراکی cPanel
#  Django + DRF + پنل پیامکی (کاوه‌نگار / SMS.ir / قاصدک / ملی پیامک)
#
#  کارهایی که انجام می‌دهد:
#    ۱. یافتن پایتون مناسب (≥3.10؛ ترجیحاً 3.11+) — از جمله مسیرهای
#       ‎/opt/alt/python3XX‎ کلودلینوکس (پایتون پیش‌فرضِ ترمینال cPanel معمولاً
#       قدیمی است؛ نسخهٔ واقعی هر کاندید اجرا و بررسی می‌شود)
#    ۲. تشخیص خودکار venv سی‌پنل (‎~/virtualenv/...‎ اگر از «Setup Python App»
#       استفاده کرده باشید؛ در این استقرار: ‎~/virtualenv/public_html/food-shop/3.11‎)
#       و در نبودش، ساخت ‎.venv-host‎
#    ۳. نصب وابستگی‌ها از ‎deploy/requirements-cpanel.txt‎ (شامل PyMySQL برای
#       دیتابیس MySQL؛ بدون gunicorn — زیر Passenger نیازی به آن نیست)
#    ۴. ساخت/تکمیل فایل ‎.env‎ — SECRET_KEY و ADMIN_PASSWORD تصادفی + کلیدهای
#       دیتابیس MySQL، فروشگاه و پنل پیامکی (کلیدهای غایب اضافه می‌شوند و مقادیر
#       موجود بازنویسی نمی‌شوند) و کنترل سخت‌گیرانهٔ پیکربندی MySQL:
#       DB_ENGINE=mysql الزامی است (دیتابیس از cPanel → MySQL® Databases ساخته می‌شود)
#    ۵. اجرای مایگریشن‌ها روی MySQL، درج اولیهٔ محصولات (seed_shop) و جمع‌آوری استاتیک
#    ۶. ساخت/به‌روزرسانی ‎passenger_wsgi.py‎ (Startup File برای Passenger سی‌پنل)
#       — دو حالت: venv سی‌پنل (بدون re-exec) و venv معمولی (با re-exec)
#    ۷. افزودن قواعد امنیتی به ‎.htaccess‎ (جلوی دانلود ‎.env‎، دیتابیس و سورس
#       از وب + سرو مستقیم ‎/static/‎ توسط Apache)
#    ۸. ری‌استارت برنامه (tmp/restart.txt) و نمایش چک‌لیست قدم‌های بعدی
#
#  نحوه اجرا (از ترمینال cPanel یا SSH، داخل پوشهٔ backend):
#      bash deploy/deploy_cpanel.sh
#
#  گزینه‌ها:
#      --venv <مسیر>    استفاده از محیط مجازی مشخص
#                       (مثلاً ‎--venv ~/virtualenv/public_html/food-shop/3.11‎)
#      --python <مسیر>  استفاده از پایتون مشخص برای ساخت venv
#                       (مثلاً ‎--python /opt/alt/python311/bin/python3.11‎)
#      -h | --help      نمایش راهنما
#
#  متغیرهای محیطی جایگزین: KHANOMGOL_VENV و KHANOMGOL_PYTHON
#
#  برای به‌روزرسانی‌های بعدی: git pull && bash deploy/deploy_cpanel.sh
#  (اسکریپت idempotent است و قابل اجرای مکرر.)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ------------------------------------------------------------- تنظیمات ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SETTINGS_MODULE="config.settings"
FRONT_ORIGIN="https://hmplus28.github.io"

# رنگ‌ها (در ترمینال‌های بدون رنگ مشکلی ایجاد نمی‌کنند)
if [ -t 1 ]; then
    C_GREEN='\033[0;32m'; C_YELLOW='\033[1;33m'; C_RED='\033[0;31m'; C_BLUE='\033[0;34m'; C_OFF='\033[0m'
else
    C_GREEN=''; C_YELLOW=''; C_RED=''; C_BLUE=''; C_OFF=''
fi
say()  { echo -e "${C_GREEN}✔${C_OFF} $*"; }
info() { echo -e "${C_BLUE}ℹ${C_OFF} $*"; }
warn() { echo -e "${C_YELLOW}⚠${C_OFF} $*" >&2; }
die()  { echo -e "${C_RED}✘ خطا:${C_OFF} $*" >&2; exit 1; }

echo ""
echo -e "${C_BLUE}═══════════════════════════════════════════════════════════════${C_OFF}"
echo -e "${C_BLUE}  فروشگاه خانم گل (backend) — استقرار روی cPanel${C_OFF}"
echo -e "${C_BLUE}═══════════════════════════════════════════════════════════════${C_OFF}"
info "پوشهٔ پروژه: $PROJECT_DIR"
info "پروفایل تنظیمات: $SETTINGS_MODULE (همه‌چیز از ‎.env‎ خوانده می‌شود)"

[ -f "$PROJECT_DIR/manage.py" ] || die "فایل manage.py در «$PROJECT_DIR» پیدا نشد؛ اسکریپت باید داخل پوشهٔ deploy پروژهٔ backend اجرا شود."

# ----------------------------------------------- آرگومان‌های خط فرمان ----
while [ $# -gt 0 ]; do
    case "$1" in
        --venv)   [ $# -ge 2 ] || die "گزینه --venv نیاز به مسیر دارد"; VENV_DIR="$2"; shift 2 ;;
        --venv=*) VENV_DIR="${1#*=}"; shift ;;
        --python) [ $# -ge 2 ] || die "گزینه --python نیاز به مسیر دارد"; PYTHON_BIN="$2"; shift 2 ;;
        --python=*) PYTHON_BIN="${1#*=}"; shift ;;
        -h|--help) awk 'NR>1 { if ($0 ~ /^#/) { sub(/^# ? ?/, ""); print } else exit }' "$0"; exit 0 ;;
        *) warn "آرگومان ناشناخته: $1 (نادیده گرفته شد)" ; shift ;;
    esac
done

VENV_DIR="${KHANOMGOL_VENV:-${VENV_DIR:-}}"
PYTHON_BIN="${KHANOMGOL_PYTHON:-${PYTHON_BIN:-}}"

# گسترش ~ در مسیرهای داده‌شده (برای وقتی که کوتیشن‌شده پاس داده شده باشد)
expand_tilde() {
    case "$1" in
        "~")  echo "$HOME" ;;
        "~/"*) echo "$HOME${1#\~}" ;;
        *)    echo "$1" ;;
    esac
}
[ -n "$VENV_DIR" ]   && VENV_DIR="$(expand_tilde "$VENV_DIR")"
[ -n "$PYTHON_BIN" ] && PYTHON_BIN="$(expand_tilde "$PYTHON_BIN")"

# ------------------------------------------------------------- فایل .env ----
ENV_FILE="$PROJECT_DIR/.env"
CPANEL_USER="$(id -un)"

# خواندن مقدار یک کلید از .env (آخرین occurrence؛ خطوط کامنت نادیده می‌شوند)
env_value() {
    sed -n -E "s/^[[:space:]]*(export[[:space:]]+)?$1=//p" "$ENV_FILE" 2>/dev/null \
        | tail -n 1 | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | tr -d '\r' || true
}

# پاک‌سازی .env دست‌کاری‌شده — فاصله ابتدای خط، فاصله انتهای خط و CR حذف می‌شود
# تا python-dotenv خط را «Invalid line» نخواند. نسخهٔ اصلی یک‌بار نگه داشته می‌شود.
sanitize_env_file() {
    local tmp="$ENV_FILE.sanitize.$$"
    sed -E \
        -e 's/\r$//' \
        -e 's/^[[:space:]]*//' \
        -e 's/[[:space:]]*$//' \
        -e 's/^export[[:space:]]+([A-Za-z_][A-Za-z_0-9]*)=/export \1=/' \
        -e 's/^([A-Za-z_][A-Za-z_0-9]*)=[[:space:]]+/\1=/' \
        "$ENV_FILE" > "$tmp" 2>/dev/null || {
        rm -f "$tmp"; return 0;
    }
    if ! cmp -s "$ENV_FILE" "$tmp"; then
        [ -f "$ENV_FILE.kg-backup" ] || cp "$ENV_FILE" "$ENV_FILE.kg-backup"
        cat "$tmp" > "$ENV_FILE"
        say "فایل ‎.env‎ پاک‌سازی شد (فاصله‌ها و CR حذف شد — نسخهٔ قبلی: ‎.env.kg-backup‎)."
    fi
    rm -f "$tmp"
    return 0
}

# تولید کلید تصادفی امن (بدون کاراکترهای خاص برای سازگاری با .env)
random_key() {
    head -c 96 /dev/urandom | base64 | tr -d '\n=+/' | cut -c1-80
}

# افزودن کلیدهای غایب به .env — مقادیر موجود هرگز بازنویسی نمی‌شوند
merge_app_keys() {
    local key val merged=0
    while IFS='|' read -r key val; do
        [ -n "$key" ] || continue
        case "$key" in \#*) continue ;; esac   # خطوط کامنت داخل فهرست نادیده گرفته شوند
        if ! grep -Eq "^[[:space:]]*(export[[:space:]]+)?${key}=" "$ENV_FILE"; then
            if [ "$merged" -eq 0 ]; then
                printf '\n# کلیدهای خودکار افزوده‌شده توسط deploy/deploy_cpanel.sh\n' >> "$ENV_FILE"
                merged=1
            fi
            printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
        fi
    done <<APPEOF
DEBUG|False
ALLOWED_HOSTS|*
CORS_ORIGINS|${FRONT_ORIGIN}
CSRF_TRUSTED_ORIGINS|
TOKEN_TTL_DAYS|30
DB_ENGINE|mysql
DB_NAME|khanomgo_foodshop
DB_USER|khanomgo_shop
DB_PASSWORD|
DB_HOST|localhost
DB_PORT|3306
SECURE_SSL_REDIRECT|False
SECURE_HSTS_SECONDS|0
SECURE_PROXY_SSL_HEADER|False
FORCE_SCRIPT_NAME|/food-shop
STATIC_URL|/food-shop/static/
ADMIN_USERNAME|admin
ADMIN_PHONE|09120000000
SHOP_NAME|فروشگاه خانم گل
SHOP_URL|https://hmplus28.github.io/food-shop/
SHOP_NOTIFY_PHONE|
SMS_ORDER_TO_CUSTOMER|true
SMS_STATUS_TO_CUSTOMER|true
SMS_PROVIDER|console
SMS_SENDER|
KAVENEGAR_API_KEY|
KAVENEGAR_OTP_TEMPLATE|
SMSIR_API_KEY|
SMSIR_OTP_TEMPLATE_ID|
SMSIR_LINE|
GHASEDAK_API_KEY|
GHASEDAK_OTP_TEMPLATE|
GHASEDAK_LINE|
MELIPAYAMAK_USERNAME|
MELIPAYAMAK_PASSWORD|
MELIPAYAMAK_FROM|
OTP_TTL|120
OTP_COOLDOWN|90
OTP_HOURLY|5
OTP_MAX_ATTEMPTS|5
APPEOF
    if ! grep -Eq "^[[:space:]]*(export[[:space:]]+)?SECRET_KEY=" "$ENV_FILE"; then
        printf '\n# کلید امنیتی توکن‌ها (تولیدشده توسط deploy/deploy_cpanel.sh — تغییر ندهید)\nSECRET_KEY=%s\n' "$(random_key)" >> "$ENV_FILE"
        say "کلید تصادفی ‎SECRET_KEY‎ به ‎.env‎ اضافه شد."
    fi
    return 0
}

ADMIN_PASS_RANDOM=0
ensure_admin_password() {
    local pass
    pass="$(env_value ADMIN_PASSWORD)"
    if [ -z "$pass" ]; then
        printf 'ADMIN_PASSWORD=%s\n' "$(random_key | cut -c1-16)" >> "$ENV_FILE"
        ADMIN_PASS_RANDOM=1
        say "‎ADMIN_PASSWORD‎ تصادفی ساخته شد — در پایانِ خروجی نمایش داده می‌شود؛ آن را ذخیره کنید!"
    elif [ "$pass" = "admin1234" ] || [ "$pass" = "CHANGE_ME" ]; then
        warn "‎ADMIN_PASSWORD‎ هنوز پیش‌فرض/placeholder است — در ‎.env‎ عوض کنید و دوباره اجرا بگیرید."
    fi
    return 0
}

if [ -f "$ENV_FILE" ]; then
    say "فایل ‎.env‎ موجود است."
    sanitize_env_file
    merge_app_keys
else
    say "فایل ‎.env‎ وجود ندارد؛ در حال ساخت با مقادیر امن ..."
    SECRET_KEY="$(random_key)"
    cat > "$ENV_FILE" << EOF
# فروشگاه خانم گل — تنظیمات محیط cPanel (بک‌اند Django)
# (توسط deploy/deploy_cpanel.sh ساخته شده؛ مقادیر placeholder را ویرایش کنید)

# کلید امنیتی توکن‌ها (تصادفی تولید شده — تغییر ندهید)
SECRET_KEY=$SECRET_KEY

# حالت دیباگ — در محیط عملیاتی False بماند
DEBUG=False

# دامنه‌های مجاز — دامنهٔ خود را جایگزین * کنید (با کاما)
ALLOWED_HOSTS=*

# ---------- دیتابیس MySQL (از cPanel → MySQL® Databases) ----------
# نام دیتابیس و کاربر در cPanel پیشوند حساب می‌گیرند: khanomgo_foodshop / khanomgo_shop
DB_ENGINE=mysql
DB_NAME=khanomgo_foodshop
DB_USER=khanomgo_shop
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306

# ---------- CORS (دامنهٔ فرانت — فروشگاه روی GitHub Pages) ----------
CORS_ORIGINS=${FRONT_ORIGIN}

# دامنه‌های مورد اعتماد CSRF برای فرم‌های پنل ادمین جنگو (اختیاری):
# CSRF_TRUSTED_ORIGINS=https://دامنه-بک‌اند-شما.ir

# ---------- حساب مدیر پنل ----------
ADMIN_USERNAME=admin
ADMIN_PHONE=09120000000

# ---------- فروشگاه ----------
SHOP_NAME=فروشگاه خانم گل
SHOP_URL=https://hmplus28.github.io/food-shop/
# موبایل مدیر برای پیامک «سفارش جدید» (خالی = ارسال نشود)
SHOP_NOTIFY_PHONE=
SMS_ORDER_TO_CUSTOMER=true
SMS_STATUS_TO_CUSTOMER=true

# ---------- پنل پیامک ----------
# console = حالت توسعه (پیامک واقعی نمی‌رود، فقط ثبت می‌شود)
# kavenegar | smsir | ghasedak | melipayamak
SMS_PROVIDER=console
SMS_SENDER=
KAVENEGAR_API_KEY=
KAVENEGAR_OTP_TEMPLATE=
SMSIR_API_KEY=
SMSIR_OTP_TEMPLATE_ID=
SMSIR_LINE=
GHASEDAK_API_KEY=
GHASEDAK_OTP_TEMPLATE=
GHASEDAK_LINE=
MELIPAYAMAK_USERNAME=
MELIPAYAMAK_PASSWORD=
MELIPAYAMAK_FROM=

# ---------- محدودیت‌های کد یکبار مصرف ----------
OTP_TTL=120
OTP_COOLDOWN=90
OTP_HOURLY=5
OTP_MAX_ATTEMPTS=5

# ---------- زیرمسیر Passenger (Application URL = /food-shop) ----------
# اگر برنامه را در Setup Python App روی مسیر دیگری سرو می‌کنید، هر دو را
# با همان مسیر هم‌اهنگ کنید؛ در غیر این صورت CSS پنل ادمین از دست می‌رود.
FORCE_SCRIPT_NAME=/food-shop
STATIC_URL=/food-shop/static/

# ---------- امنیت TLS (بعد از فعال‌شدن https روی هاست) ----------
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SECURE_PROXY_SSL_HEADER=False
EOF
    say "فایل ‎.env‎ ساخته شد: $ENV_FILE"
    warn "ALLOWED_HOSTS را در ‎.env‎ به دامنهٔ واقعی خود محدود کنید."
fi
ensure_admin_password
_pass="$(env_value ADMIN_PASSWORD)"
if [ -z "$_pass" ] || [ "$_pass" = "admin1234" ]; then
    warn "رمز مدیر پیش‌فرض است؛ پس از استقرار حتماً در ‎.env‎ عوض کنید و اسکریپت را دوباره اجرا کنید."
fi
# ---------------------------------------------- کنترل دیتابیس MySQL ----
# دیتابیس فروشگاه روی هاست MySQL است (نه SQLite). مقادیر را از cPanel →
# «MySQL® Databases» بگیرید؛ نام دیتابیس/کاربر پیشوند حساب دارد (khanomgo_…).
DB_ENGINE_VAL="$(env_value DB_ENGINE)"
DB_NAME_VAL="$(env_value DB_NAME)"
DB_USER_VAL="$(env_value DB_USER)"
DB_PASS_VAL="$(env_value DB_PASSWORD)"
DB_HOST_VAL="$(env_value DB_HOST)";  DB_HOST_VAL="${DB_HOST_VAL:-localhost}"
DB_PORT_VAL="$(env_value DB_PORT)";  DB_PORT_VAL="${DB_PORT_VAL:-3306}"

case "$(echo "$DB_ENGINE_VAL" | tr '[:upper:]' '[:lower:]')" in
    mysql|mariadb) ;;
    *)
        if [ "${KHANOMGOL_ALLOW_SQLITE:-0}" = "1" ]; then
            warn "KHANOMGOL_ALLOW_SQLITE=1 — مایگریشن‌ها روی SQLite اجرا می‌شود (فقط برای تست محلی)."
            export DB_ENGINE=sqlite3   # تنظیمات جنگو از متغیر محیطی پیروی می‌کند
            KHANOMGOL_DB_SKIP=1
        else
            die "دیتابیس باید MySQL باشد؛ در ‎.env‎ مقدار DB_ENGINE=mysql را بگذارید.
(تست محلی بدون MySQL:  KHANOMGOL_ALLOW_SQLITE=1 bash deploy/deploy_cpanel.sh)"
        fi
        ;;
esac
if [ -z "${KHANOMGOL_DB_SKIP:-}" ]; then
    if [ -z "$DB_NAME_VAL" ] || [ -z "$DB_USER_VAL" ] || [ -z "$DB_PASS_VAL" ]; then
        die "پیکربندی دیتابیس MySQL در ‎.env‎ ناقص است (DB_NAME/DB_USER/DB_PASSWORD خالی).
قدم‌های دقیق:
  ۱) cPanel → «MySQL® Databases» → Create New Database → نام: foodshop
     (نام کامل با پیشوند حساب: khanomgo_foodshop)
  ۲) در همان صفحه → MySQL Users → Add New User → نام: shop (کامل: khanomgo_shop) + رمز قوی
  ۳) «Add User To Database» → تیک ALL PRIVILEGES → Make Changes
  ۴) در ‎.env‎ همین پوشه وارد کنید:
       DB_ENGINE=mysql
       DB_NAME=khanomgo_foodshop
       DB_USER=khanomgo_shop
       DB_PASSWORD=رمزی-که-ساختید
  ۵) دوباره اجرا کنید: bash deploy/deploy_cpanel.sh"
    fi
    say "دیتابیس MySQL: $DB_NAME_VAL روی $DB_HOST_VAL:$DB_PORT_VAL (کاربر: $DB_USER_VAL)"
fi

# ----------------------------------------------------- ابزار یافتن پایتون ----
# پایتون ≥3.10 لازم است (Django 5.x). نسخهٔ «واقعی» هر کاندید اجرا و بررسی
# می‌شود تا پایتون قدیمی سیستمی هرگز انتخاب نشود.
python_ok() {
    local v
    v="$("$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)" || return 1
    case "$v" in
        3.10|3.1[1-9]|3.[2-9][0-9]) return 0 ;;
        *) return 1 ;;
    esac
}

find_python() {
    local candidate
    local -a candidates=()
    [ -n "$PYTHON_BIN" ] && candidates+=("$PYTHON_BIN")
    candidates+=(
        python3.11
        /opt/alt/python311/bin/python3.11
        /opt/alt/python311/bin/python3
        /opt/alt/python311/bin/python
        /usr/local/bin/python3.11
        /usr/bin/python3.11
        python3.12
        /opt/alt/python312/bin/python3.12
        /opt/alt/python312/bin/python3
        python3.13
        /opt/alt/python313/bin/python3.13
        python3.10
        /opt/alt/python310/bin/python3.10
        /opt/alt/python310/bin/python3
        python3
    )
    # اسکن عمومی پایتون‌های کلودلینوکس — جدیدترین اول
    # (در شل jailed برخی هاست‌های cPanel به‌دلیل نبود /dev/fd، process substitution
    #  با خطای «/dev/fd/62: No such file or directory» شکست می‌خورد؛ از حلقهٔ ساده استفاده می‌کنیم)
    for candidate in $(ls /opt/alt/python3*/bin/python3 2>/dev/null | sort -rV || true); do
        candidates+=("$candidate")
    done

    for candidate in "${candidates[@]}"; do
        [ -n "$candidate" ] || continue
        if { [ -x "$candidate" ] || command -v "$candidate" >/dev/null 2>&1; } && python_ok "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# ------------------------------------------ یافتن محیط مجازی (اولویت‌دار) ----
# ترتیب: ۱) --venv صریح   ۲) venv سی‌پنلِ همین پروژه (‎~/virtualenv/<مسیر>/<نسخه>‎)
#         ۳) .venv-host موجود   ۴) ساخت .venv-host با پایتونِ پیدا شده
if [ -z "$VENV_DIR" ] && [ -d "$HOME/virtualenv" ]; then
    proj_base="$(basename "$PROJECT_DIR")"
    cpanel_roots=( "$HOME/virtualenv/$proj_base" )
    case "$PROJECT_DIR" in
        "$HOME"/*)
            rel="${PROJECT_DIR#${HOME}/}"
            if [ -n "$rel" ] && [ "$rel" != "$PROJECT_DIR" ]; then
                cpanel_roots+=( "$HOME/virtualenv/$rel" )
                # الگوی رایج: ریپو در ‎~/public_html/food-shop‎ و کد Django در
                # زیرپوشهٔ backend؛ در cPanel → Setup Python App، Application root
                # همان پوشهٔ والد (public_html/food-shop) است و venv در
                # ‎~/virtualenv/public_html/food-shop/<نسخه>‎ ساخته می‌شود؛ پس
                # والدِ backend هم امتحان می‌شود.
                case "$rel" in
                    */backend) cpanel_roots+=( "$HOME/virtualenv/${rel%/backend}" ) ;;
                esac
            fi
            ;;
    esac
    app_venv_root=""
    for root in "${cpanel_roots[@]}"; do
        if [ -d "$root" ]; then app_venv_root="$root"; break; fi
    done
    if [ -d "$app_venv_root" ]; then
        for ver_dir in $(ls -1d "$app_venv_root"/*/ 2>/dev/null | sort -rV); do
            if [ -x "${ver_dir%/}/bin/python" ] && python_ok "${ver_dir%/}/bin/python"; then
                VENV_DIR="${ver_dir%/}"
                break
            fi
        done
        if [ -n "$VENV_DIR" ]; then
            say "محیط مجازی سی‌پنل برای همین پروژه پیدا شد: $VENV_DIR"
        else
            warn "در ‎$app_venv_root‎ محیط قابل استفاده (پایتون ≥3.10) پیدا نشد."
        fi
    else
        info "در ‎~/virtualenv‎ محیطی متعلق به این پروژه پیدا نشد؛ نادیده گرفته شد."
    fi
fi

if [ -z "$VENV_DIR" ]; then
    VENV_DIR="$PROJECT_DIR/.venv-host"
fi

NEED_VENV_CREATE=0
if [ ! -x "$VENV_DIR/bin/python" ]; then
    NEED_VENV_CREATE=1
elif ! python_ok "$VENV_DIR/bin/python"; then
    die "پایتون محیط مجازی «$VENV_DIR» قدیمی است (<3.10).
محیط جدیدی بسازید یا مسیر درست را با ‎--venv‎ مشخص کنید."
fi

if [ "$NEED_VENV_CREATE" -eq 1 ]; then
    PYTHON_BIN="$(find_python)" || die "پایتون ≥3.10 پیدا نشد.
مسیرهای بررسی‌شده: python3.10 تا python3.13 در PATH و ‎/opt/alt/python3XX/bin/‎ (کلودلینوکس).
راه‌حل ۱ (پیشنهادی): در cPanel → «Setup Python App» یک برنامه با Python 3.11 بسازید و
  Application root را روی پوشهٔ همین پروژه (backend) بگذارید؛ سی‌پنل venv می‌سازد و
  این اسکریپت در اجرای بعدی خودش آن را پیدا و استفاده می‌کند.
راه‌حل ۲: مسیر دقیق پایتون را بدهید، مثلاً:
  bash deploy/deploy_cpanel.sh --python /opt/alt/python311/bin/python3.11"
    info "پایتون انتخاب‌شده: $PYTHON_BIN (نسخه $("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'))"
    say "محیط مجازی وجود ندارد؛ در حال ساخت در «$VENV_DIR» ..."
    mkdir -p "$(dirname "$VENV_DIR")"
    if ! "$PYTHON_BIN" -m venv "$VENV_DIR" 2>/dev/null; then
        warn "ماژول venv در دسترس نیست؛ تلاش با virtualenv ..."
        if ! "$PYTHON_BIN" -m virtualenv "$VENV_DIR" 2>/dev/null; then
            die "ساخت محیط مجازی ناموفق بود.
راه‌حل: در cPanel بخش «Setup Python App» یک برنامه با Python 3.11 بسازید
(Application root = پوشهٔ backend) تا سی‌پنل خودش venv را بسازد، سپس این
اسکریپت را دوباره اجرا کنید."
        fi
    fi
    say "محیط مجازی ساخته شد: $VENV_DIR"
else
    say "محیط مجازی موجود: $VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
[ -x "$VENV_PY" ] || die "پایتون محیط مجازی در $VENV_PY قابل اجرا نیست."

VENV_PY_VERSION="$("$VENV_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
info "پایتون محیط مجازی: $VENV_PY_VERSION"

REQUIREMENTS="$PROJECT_DIR/deploy/requirements-cpanel.txt"
[ -f "$REQUIREMENTS" ] || REQUIREMENTS="$PROJECT_DIR/requirements.txt"
[ -f "$REQUIREMENTS" ] || die "فایل نیازمندی‌ها پیدا نشد."

# ------------------------------------------------------ نصب وابستگی‌ها ----
say "به‌روزرسانی pip ..."
"$VENV_PIP" install --quiet --upgrade pip wheel setuptools

say "نصب وابستگی‌ها (چند دقیقه صبر کنید) از $REQUIREMENTS ..."
"$VENV_PIP" install --quiet -r "$REQUIREMENTS"

# ------------------------------------------------------------- دستورات جنگو ----
export DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE"

say "اجرای مایگریشن‌ها ..."
"$VENV_PY" "$PROJECT_DIR/manage.py" migrate --noinput

say "درج اولیهٔ محصولات و حساب مدیر (seed_shop — idempotent) ..."
"$VENV_PY" "$PROJECT_DIR/manage.py" seed_shop

say "جمع‌آوری فایل‌های استاتیک (برای پنل ادمین جنگو) ..."
"$VENV_PY" "$PROJECT_DIR/manage.py" collectstatic --noinput

# ------------------------------------------------------------ passenger_wsgi ----
# فایل هر بار بازسازی می‌شود. دو حالت:
#   • venv «Setup Python App» سی‌پنل (زیر ~/virtualenv یا دارای bin/lswsgi)
#     → wsgi ساده بدون re-exec؛ Passenger خودش با پایتون همان venv اسپاون می‌کند.
#     re-exec (os.execl) با لودر CloudLinux (lswsgi) سازگار نیست و 503 می‌دهد.
#   • venv معمولی (ساختهٔ همین اسکریپت) → wsgi دارای بلوک re-exec.
WSGI_FILE="$PROJECT_DIR/passenger_wsgi.py"
WSGI_MARKER="# KHANOMGOL-PASSENGER-WSGI"
if [ -f "$WSGI_FILE" ] && ! grep -q "$WSGI_MARKER" "$WSGI_FILE" 2>/dev/null; then
    if [ ! -f "$WSGI_FILE.kg-backup" ]; then
        cp "$WSGI_FILE" "$WSGI_FILE.kg-backup"
        info "نسخهٔ قبلی passenger_wsgi.py در ‎passenger_wsgi.py.kg-backup‎ نگه داشته شد."
    fi
fi
say "ساخت/به‌روزرسانی ‎passenger_wsgi.py‎ (Startup File برای Passenger سی‌پنل) ..."
IS_SELECTOR_VENV=0
case "$VENV_DIR" in
    "$HOME"/virtualenv/*) IS_SELECTOR_VENV=1 ;;
esac
if [ -x "$VENV_DIR/bin/lswsgi" ]; then IS_SELECTOR_VENV=1; fi

if [ "$IS_SELECTOR_VENV" -eq 1 ]; then
    # venv «Setup Python App» سی‌پنل: Passenger خودش با پایتون همین venv اجرا می‌کند
    cat > "$WSGI_FILE" << 'KGWSGI'
# KHANOMGOL-PASSENGER-WSGI — نقطه ورود WSGI برای cPanel/Passenger
# این فایل توسط deploy/deploy_cpanel.sh ساخته می‌شود؛ آن را دستی ویرایش نکنید.
#
# venv از نوع «Setup Python App» سی‌پنل است؛ Passenger خودش با پایتون همین
# venv اجرا می‌کند، پس عمداً هیچ re-exec ای این‌جا نیست (re-exec با لودر
# lswsgi سی‌پنل سازگار نیست و 503 می‌دهد).

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
KGWSGI
    say "passenger_wsgi.py آماده شد (Setup Python App سی‌پنل — بدون re-exec)."
else
    cat > "$WSGI_FILE" << KGWSGI
# KHANOMGOL-PASSENGER-WSGI — نقطه ورود WSGI برای cPanel/Passenger
# این فایل توسط deploy/deploy_cpanel.sh ساخته می‌شود؛ آن را دستی ویرایش نکنید.
# (اجرای دوبارهٔ اسکریپت، آن را با مسیرهای به‌روز بازسازی می‌کند.)

import os
import sys

# Passenger ممکن است این فایل را با پایتون سیستمی (قدیمی) اجرا کند؛ در آن
# صورت با پایتونِ محیط مجازی دوباره اجرا می‌شویم.
INTERP = r"$VENV_DIR/bin/python"
if os.path.realpath(os.path.dirname(sys.executable)) != os.path.realpath(os.path.dirname(INTERP)):
    os.execl(INTERP, INTERP, *sys.argv)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
KGWSGI
    say "passenger_wsgi.py آماده شد (اجرای برنامه با: $VENV_DIR/bin/python)."
fi

# ------------------------------------ passenger_wsgi در ریشهٔ برنامهٔ سی‌پنل ----
# اگر کد Django داخل زیرپوشهٔ backend باشد ولی Application root سی‌پنل پوشهٔ والد
# باشد (الگوی همین استقرار: ‎~/public_html/food-shop‎ + backend/)، Passenger فایل
# Startup را در «والد» جست‌وجو می‌کند؛ اگر نباشد صفحهٔ پیش‌فرض «It works! Python»
# نشان داده می‌شود. پس همان‌جا هم نسخهٔ درست نوشته می‌شود.
PARENT_DIR="$(dirname "$PROJECT_DIR")"
# پوشهٔ «برنامهٔ سی‌پنل» (Application Root در Setup Python App):
#   ۱) اگر با KHANOMGOL_APP_ROOT صریحاً داده شده، همان ملاک است — حتی اگر
#      اسکریپت از کلونِ ریپو (مثل ~/food-shop-repo/backend) اجرا شود؛
#   ۲) در الگوی رایج، والدِ backend (مثل ~/public_html/food-shop)؛
#   ۳) اگر backend زیر public_html نیست و flag هم داده نشده، بی‌اثر.
if [ -n "${KHANOMGOL_APP_ROOT:-}" ]; then
    ROOT_APP_DIR="${KHANOMGOL_APP_ROOT/#\~/$HOME}"
elif [ "$(basename "$PROJECT_DIR")" = "backend" ] && [ -d "$PARENT_DIR" ]; then
    ROOT_APP_DIR="$PARENT_DIR"
else
    ROOT_APP_DIR=""
fi
if [ -n "$ROOT_APP_DIR" ] && [ -d "$ROOT_APP_DIR" ] && [ "$(cd "$ROOT_APP_DIR" && pwd)" != "$(cd "$PROJECT_DIR" && pwd)" ]; then
    ROOT_WSGI_FILE="$ROOT_APP_DIR/passenger_wsgi.py"
    mkdir -p "$ROOT_APP_DIR/tmp"
    # اگر نسخهٔ موجود فایل ما نبود (مثل passenger_wsgi.py نمایشی سی‌پنل) پشتیبان بگیر
    if [ -f "$ROOT_WSGI_FILE" ] && ! grep -q "KHANOMGOL-PASSENGER-WSGI-ROOT" "$ROOT_WSGI_FILE" 2>/dev/null; then
        if [ ! -f "$ROOT_WSGI_FILE.kg-backup" ]; then
            cp "$ROOT_WSGI_FILE" "$ROOT_WSGI_FILE.kg-backup"
            info "نسخهٔ قبلی ‎$ROOT_WSGI_FILE‎ در ‎passenger_wsgi.py.kg-backup‎ نگه داشته شد."
        fi
    fi
    if [ "$IS_SELECTOR_VENV" -eq 1 ]; then
        cat > "$ROOT_WSGI_FILE" << 'KGROOTWSGI'
# KHANOMGOL-PASSENGER-WSGI-ROOT — Startup File برنامهٔ cPanel
# (Application root = والدِ backend) — توسط backend/deploy/deploy_cpanel.sh ساخته می‌شود؛ دستی ویرایش نکنید.

import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
KGROOTWSGI
        say "passenger_wsgi.py در ریشهٔ برنامهٔ سی‌پنل ساخته شد: $ROOT_WSGI_FILE"
    else
        cat > "$ROOT_WSGI_FILE" << KGROOTWSGI
# KHANOMGOL-PASSENGER-WSGI-ROOT — Startup File برنامهٔ cPanel
# (Application root = والدِ backend) — توسط backend/deploy/deploy_cpanel.sh ساخته می‌شود؛ دستی ویرایش نکنید.
# venv خودمان (.venv-host) است؛ Passenger با پایتون venv سی‌پنل اجرا می‌کند که
# وابستگی‌ها را ندارد، پس با پایتونِ .venv-host دوباره اجرا می‌شویم.

import os
import sys

INTERP = r"$VENV_DIR/bin/python"
if os.path.realpath(os.path.dirname(sys.executable)) != os.path.realpath(os.path.dirname(INTERP)):
    os.execl(INTERP, INTERP, *sys.argv)

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
KGROOTWSGI
        warn "passenger_wsgi.py ریشه با re-exec ساخته شد؛ برای پایداری بیشتر در cPanel → Setup Python App نسخهٔ Python همان ۳.۱۱ را نگه دارید و وابستگی‌ها را در venv سی‌پنل هم نصب کنید (اجرای دوبارهٔ همین اسکریپت پس از پیدا شدن venv سی‌پنل، خودش این کار را می‌کند)."
    fi
    touch "$ROOT_APP_DIR/tmp/restart.txt"
    say "Startup File ریشهٔ برنامهٔ سی‌پنل نوشته شد: $ROOT_WSGI_FILE"
fi

# ------------------------------------------------- قواعد امنیتی .htaccess ----
# اگر پروژه داخل public_html است، بدون این قواعد فایل‌های حساس (.env،
# db.sqlite3، سورس‌ها) از وب قابل دانلود هستند. سرو ‎/static/‎ هم مستقیم
# توسط Apache انجام می‌شود (سریع‌تر؛ Whitenoise هم به‌عنوان پشتیبان فعال است).
HTACCESS_FILE="$PROJECT_DIR/.htaccess"
HT_MARKER="# BEGIN KHANOMGOL-PROTECT"
write_htaccess_block() {
    cat << 'HTACCESS'
# BEGIN KHANOMGOL-PROTECT
# ── محافظت از فایل‌های حساس فروشگاه خانم گل (تولیدشده توسط deploy/deploy_cpanel.sh) ──
Options -Indexes

# فایل‌های محیط، دیتابیس و پشتیبان — هرگز از وب قابل دانلود نباشند
<FilesMatch "\.env(\.[a-zA-Z0-9_.]+)?$|\.(sqlite3|sqlite3-journal|log|bak|backup|old|orig|swp|kg-backup)$">
    Require all denied
</FilesMatch>

# سورس پایتون، تنظیمات و مستندات پروژه
<FilesMatch "\.(py|pyc|pyo|md|txt|sh|toml|cfg|ini|json|ya?ml|lock|example|gitignore|gitattributes)$">
    Require all denied
</FilesMatch>

<IfModule mod_rewrite.c>
    RewriteEngine On

    # سرو استاتیک مستقیم توسط Apache (فایل واقعی زیر همین پوشه است)
    RewriteRule ^static/(.*)$ staticfiles/$1 [L]

    # پوشه‌های حساس (نسبت به همین پوشه) — شامل سورس و ابزارهای استقرار
    RewriteRule (^|/)(\.git|\.venv-host|\.venv|venv|deploy|shop|config|logs|tmp)(/|$) - [F]
</IfModule>
# END KHANOMGOL-PROTECT
HTACCESS
}
if [ ! -f "$HTACCESS_FILE" ]; then
    write_htaccess_block > "$HTACCESS_FILE"
    say ".htaccess ساخته شد (محافظت از فایل‌های حساس + سرو استاتیک)."
elif grep -q "$HT_MARKER" "$HTACCESS_FILE" 2>/dev/null; then
    say "قواعد امنیتی .htaccess از قبل فعال است."
else
    if [ ! -f "$HTACCESS_FILE.kg-backup" ]; then
        cp "$HTACCESS_FILE" "$HTACCESS_FILE.kg-backup"
        info "نسخهٔ قبلی .htaccess در ‎.htaccess.kg-backup‎ نگه داشته شد."
    fi
    printf '\n' >> "$HTACCESS_FILE"
    write_htaccess_block >> "$HTACCESS_FILE"
    say "قواعد امنیتی به .htaccess موجود افزوده شد."
fi
case "$PROJECT_DIR" in
    */public_html/*) warn "پروژه داخل public_html است؛ قواعد امنیتی نصب شد اما توصیه می‌شود در بلندمدت برنامه را خارج از public_html نگه دارید." ;;
esac

# ------------------------------------------------- پشتیبان‌گیری اولیه ----
# MySQL: با mysqldump؛ رمز با MYSQL_PWD پاس داده می‌شود تا در لیست پروسه‌ها دیده نشود.
BACKUPS_DIR="$PROJECT_DIR/backups"
if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
    mkdir -p "$BACKUPS_DIR"
    if [ ! -f "$BACKUPS_DIR/db-first-deploy.sqlite3" ]; then
        cp "$PROJECT_DIR/db.sqlite3" "$BACKUPS_DIR/db-first-deploy.sqlite3"
        say "پشتیبان اولیهٔ دیتابیس SQLite: backups/db-first-deploy.sqlite3"
    fi
fi
DUMP_BIN=""
if [ -z "${KHANOMGOL_DB_SKIP:-}" ]; then
    # روی برخی هاست‌ها فقط mariadb-dump هست (mysqldump حذف شده)
    if command -v mysqldump >/dev/null 2>&1; then DUMP_BIN="$(command -v mysqldump)"
    elif command -v mariadb-dump >/dev/null 2>&1; then DUMP_BIN="$(command -v mariadb-dump)"
    fi
fi
if [ -n "$DUMP_BIN" ]; then
    mkdir -p "$BACKUPS_DIR"
    if [ ! -s "$BACKUPS_DIR/db-first-deploy.sql.gz" ]; then
        # --no-defaults: فایل‌های پیش‌فرضِ ناقص (مثل /etc/mysql/releem.conf.d)
        # باعث «Fatal error in defaults handling» می‌شوند؛ با این گزینه خوانده نمی‌شوند
        if MYSQL_PWD="$DB_PASS_VAL" "$DUMP_BIN" --no-defaults -h "$DB_HOST_VAL" -P "$DB_PORT_VAL" \
            -u "$DB_USER_VAL" "$DB_NAME_VAL" | gzip > "$BACKUPS_DIR/db-first-deploy.sql.gz"; then
            say "پشتیبان اولیهٔ دیتابیس MySQL: backups/db-first-deploy.sql.gz"
        else
            warn "پشتیبان‌گیری اولیهٔ MySQL ناموفق بود؛ استقرار ادامه می‌یابد."
        fi
    fi
fi

# ------------------------------------------------- فایل‌های کمکی و ری‌استارت ----
mkdir -p "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"

say "ری‌استارت برنامه (Passenger) ..."
touch "$PROJECT_DIR/tmp/restart.txt"

# ------------------------------------------------------------------ خلاصه ----
echo ""
echo -e "${C_GREEN}═══════════════════════════════════════════════════════════════${C_OFF}"
say "استقرار کامل شد."
echo -e "${C_GREEN}═══════════════════════════════════════════════════════════════${C_OFF}"
if [ "$ADMIN_PASS_RANDOM" -eq 1 ]; then
    echo ""
    warn "رمز مدیر پنل (همین حالا ذخیره کنید): ADMIN_PASSWORD = $(env_value ADMIN_PASSWORD)"
fi
echo ""
echo "قدم‌های بعدی (اگر برای اولین بار استقرار می‌کنید):"
echo ""
echo -e "  ۱. ${C_YELLOW}cPanel → Setup Python App${C_OFF} را باز کنید و بررسی/ایجاد کنید:"
echo "     • Python version: 3.11 (یا بالاتر)"
echo "     • Application root: public_html/food-shop (همین پوشه)"
echo "     • Application URL: /food-shop (برنامه زیر دامنهٔ اصلی سرو می‌شود)"
echo "     • Startup File: passenger_wsgi.py (خودکار شناسایی می‌شود)"
echo -e "     • اگر venv را سی‌پنل ساخته، اسکریپت در اجرای بعدی خودش آن را پیدا می‌کند؛"
echo -e "       در همین استقرار venv سی‌پنل خودکار پیدا می‌شود: ${C_YELLOW}~/virtualenv/public_html/food-shop/3.11${C_OFF}"
echo -e "     • ${C_YELLOW}Application URL حتماً /food-shop باشد (نه /)${C_OFF} — اگر «/» است در پنل ویرایش و"
echo "       بعد از هر تغییر، دکمهٔ Restart پنل را بزنید؛ وگرنه صفحهٔ «It works! Python» می‌بینید."
echo ""
echo "  ۲. فایل ‎.env‎ را ویرایش کنید:"
echo "     • ALLOWED_HOSTS=دامنه-شما.ir"
echo "     • DB_NAME / DB_USER / DB_PASSWORD  (دیتابیس MySQL از cPanel → MySQL® Databases)"
echo "     • CORS_ORIGINS=https://hmplus28.github.io  (همان دامنهٔ فروشگاه)"
echo "     • ADMIN_PASSWORD=یک-رمز-قوی  (اگر تصادفی ساخته شده، بالا را کپی کنید)"
echo "     • SHOP_NOTIFY_PHONE=موبایل-خودتان  (پیامک سفارش جدید)"
echo "     • SMS_PROVIDER و کلیدهای پنل پیامکی (کاوه‌نگار / SMS.ir / قاصدک / ملی پیامک)"
echo "     • بعد از نصب SSL: SECURE_SSL_REDIRECT=True و SECURE_HSTS_SECONDS=31536000"
echo "     سپس: touch tmp/restart.txt  (یا دوباره: bash deploy/deploy_cpanel.sh)"
echo ""
echo "  ۳. تست سلامت سرویس:"
echo "     • https://دامنه-شما/food-shop/api/v1/health   → باید {\"ok\":true,...} بدهد"
echo "     • پنل ادمین جنگو: https://دامنه-شما/food-shop/dj-admin/"
echo ""
echo "  ۴. اتصال فرانت Vue به این بک‌اند (بیلد مجدد و انتشار در ریپو):"
echo "     cd app && VITE_API_ENABLED=true VITE_API_BASE=https://دامنه-شما/food-shop/api/v1 \\"
echo "       VITE_BASE=/food-shop/ npm run build && cp -r dist/. .."
echo ""
echo "  ۵. تست اتصال پنل پیامکی: در پنل مدیریت فرانت، تب «پنل پیامک» → ارسال پیامک آزمایشی."
echo ""
echo "  ۶. پشتیبان‌گیری دوره‌ای دیتابیس MySQL — یک‌بار فایل ‎~/.my.cnf‎ بسازید:"
echo "       [client]"
echo "       user=${DB_USER_VAL:-DB_USER}"
echo "       password=رمز-دیتابیس"
echo "     سپس در cPanel → Cron Jobs (روزانه ساعت ۳ صبح، نگهداری ۳۰ روز):"
echo "     0 3 * * * mysqldump --no-defaults -h $DB_HOST_VAL $DB_NAME_VAL | gzip > $BACKUPS_DIR/db-\$(date +\\%F).sql.gz && find $BACKUPS_DIR -name 'db-*.sql.gz' -mtime +30 -delete"
echo ""
echo "  ۷. راهنمای کامل گام‌به‌گام: backend/README.md و deploy/GUIDE-CPANEL-FA.md"
echo ""
echo -e "  برای به‌روزرسانی‌های بعدی: ${C_YELLOW}git pull && bash deploy/deploy_cpanel.sh${C_OFF}"
echo ""
