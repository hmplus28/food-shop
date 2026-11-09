#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  فروشگاه اینترنتی خانم گل (خشکبار) — اسکریپت استقرار روی هاست اشتراکی cPanel
#  ریپو: hmplus28/food-shop — فرانت Vue 3 + Vite
#
#  کارهایی که انجام می‌دهد:
#    ۱. استقرار خروجی بیلدِ commit‌شده در ریشهٔ ریپو (index.html + assets/) —
#       پیش‌فرض، بدون نیاز به Node روی هاست. بیلد در گیت نگه‌داری می‌شود تا
#       روی هاست فقط کپی شود (همان سیاست انتشار GitHub Pages).
#    ۲. خواندن آدرس بک‌اندِ bake‌شده داخل باندل و هشدار اگر هنوز روی
#       localhost/placeholder است (VITE_API_BASE در زمان بیلد داخل assets می‌رود).
#    ۳. کنترل مسیرِ پایه (VITE_BASE): بیلدِ ریشهٔ ریپو برای GitHub Pages با
#       ‎/food-shop/‎ بسته شده؛ برای دامنهٔ اختصاصی cPanel باید با --build و
#       VITE_BASE=/ دوباره بیلد شود (اسکریپت خودکار تشخیص و راهنمایی می‌کند).
#    ۴. (فقط با ‎--build‎) یافتن Node ≥18، مدیریت ‎app/.env‎، نصب وابستگی‌ها
#       و بیلد Vite — برای بیلد روی خود هاست.
#    ۵. همگام‌سازی غیرمخرب فایل‌های انتشار با ریشهٔ وب (پیش‌فرض ‎~/public_html‎):
#       پوشهٔ ‎assets/‎ هش‌شده کاملاً جایگزین می‌شود و فایل‌های سطح‌بالای بیلد
#       (index.html، 404.html، robots.txt، sitemap.xml، .nojekyll) کپی می‌شوند؛
#       سایر فایل‌های ریشهٔ وب دست نمی‌خورند.
#    ۶. ساخت/به‌روزرسانی ‎.htaccess‎ در ریشهٔ وب:
#       • fallback مسیریابی SPA (تا ‎/products‎، ‎/product/1‎ و ‎/track‎ با رفرش کار کنند)
#       • فشرده‌سازی gzip (mod_deflate)
#       • هدرهای کش: دارایی‌های هش‌شده یک سال، index.html بدون کش
#       • محافظت از مسیرهای حساس ریپو (‎.git‎، ‎app/‎، ‎deploy/‎، ‎scripts/‎،
#         ‎download/‎، ‎upload/‎، ‎skills/‎، ‎.env‎ و …)
#    ۷. نمایش خلاصه + قدم‌های بعدی
#
#  نحوه اجرا (از داخل پوشه پروژه، در ترمینال cPanel یا SSH):
#      bash deploy/deploy_cpanel.sh
#
#  گزینه‌ها:
#      --webroot <مسیر>    ریشهٔ وب مقصد (پیش‌فرض ‎~/public_html‎)
#                          (مثلاً ‎--webroot ~/public_html/shop‎ یا ‎--webroot ~/shop.example.ir‎)
#      --build             بیلد روی خود هاست (نیاز به Node ≥18). پیش‌فرض خاموش است
#                          چون بیلد از قبل commit شده است.
#      --base <مسیر>       (فقط با --build) مسیر پایهٔ Vite؛ پیش‌فرض ‎/‎ (مناسب cPanel).
#                          برای شبیه‌سازی GitHub Pages: ‎--base /food-shop/‎
#      --api-base <url>    (فقط با --build) آدرس بک‌اند نوشته می‌شود در ‎app/.env‎:
#                          VITE_API_BASE (مثلاً ‎--api-base https://api.example.ir/api/v1‎)
#      --api-enabled       (فقط با --build) VITE_API_ENABLED=true در ‎app/.env‎
#      --node <مسیر>       (فقط با --build) استفاده از Node مشخص
#                          (مثلاً ‎--node /opt/alt/alt-nodejs18/bin/node‎)
#      --clean             پاک‌سازی کامل ریشهٔ وب قبل از کپی (احتیاط!
#                          سایر فایل‌های ریشهٔ وب را پاک می‌کند)
#      -h | --help         نمایش راهنما
#
#  متغیرهای محیطی جایگزین: KHANOMGOL_WEBROOT و KHANOMGOL_NODE و
#  KHANOMGOL_API_BASE و KHANOMGOL_BASE
#
#  برای به‌روزرسانی‌های بعدی: git pull && bash deploy/deploy_cpanel.sh
#  (اسکریپت idempotent است و قابل اجرای مکرر.)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ------------------------------------------------------------- تنظیمات ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WEBROOT="${KHANOMGOL_WEBROOT:-}"
NODE_BIN="${KHANOMGOL_NODE:-}"
API_BASE_CLI="${KHANOMGOL_API_BASE:-}"
BASE_CLI="${KHANOMGOL_BASE:-/}"
DO_BUILD=0
API_ENABLED_CLI=0
CLEAN_WEBROOT=0

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
echo -e "${C_BLUE}  فروشگاه خانم گل — استقرار روی cPanel${C_OFF}"
echo -e "${C_BLUE}═══════════════════════════════════════════════════════════════${C_OFF}"
info "پوشه پروژه: $PROJECT_DIR"

[ -f "$PROJECT_DIR/app/package.json" ] || die "پوشهٔ app/ پروژه پیدا نشد؛ اسکریپت باید داخل پوشهٔ deploy همان ریپو اجرا شود."

# ----------------------------------------------- آرگومان‌های خط فرمان ----
while [ $# -gt 0 ]; do
    case "$1" in
        --webroot)    [ $# -ge 2 ] || die "گزینه --webroot نیاز به مسیر دارد"; WEBROOT="$2"; shift 2 ;;
        --webroot=*)  WEBROOT="${1#*=}"; shift ;;
        --api-base)   [ $# -ge 2 ] || die "گزینه --api-base نیاز به url دارد"; API_BASE_CLI="$2"; shift 2 ;;
        --api-base=*) API_BASE_CLI="${1#*=}"; shift ;;
        --base)       [ $# -ge 2 ] || die "گزینه --base نیاز به مسیر دارد"; BASE_CLI="$2"; shift 2 ;;
        --base=*)     BASE_CLI="${1#*=}"; shift ;;
        --node)       [ $# -ge 2 ] || die "گزینه --node نیاز به مسیر دارد"; NODE_BIN="$2"; shift 2 ;;
        --node=*)     NODE_BIN="${1#*=}"; shift ;;
        --build)      DO_BUILD=1; shift ;;
        --api-enabled) API_ENABLED_CLI=1; shift ;;
        --skip-build) DO_BUILD=0; shift ;;   # پشتیبان (no-op): بیلد پیش‌فرض خاموش است
        --clean)      CLEAN_WEBROOT=1; shift ;;
        -h|--help) awk 'NR>1 { if ($0 ~ /^#/) { sub(/^# ? ?/, ""); print } else exit }' "$0"; exit 0 ;;
        *) warn "آرگومان ناشناخته: $1 (نادیده گرفته شد)" ; shift ;;
    esac
done

# گسترش ~ در مسیرهای داده‌شده (برای وقتی که کوتیشن‌شده پاس داده شده باشد)
expand_tilde() {
    case "$1" in
        "~")  echo "$HOME" ;;
        "~/"*) echo "$HOME${1#\~}" ;;
        *)    echo "$1" ;;
    esac
}
[ -n "$WEBROOT" ]  && WEBROOT="$(expand_tilde "$WEBROOT")"
[ -n "$NODE_BIN" ] && NODE_BIN="$(expand_tilde "$NODE_BIN")"

# --------------------------------------------- فایل .env سورس (app/) ----
# Vite متغیرهای VITE_* را در زمان build داخل باندل می‌بافد؛ پس .env فقط در
# مسیر بیلد معنا دارد. مقادیر موجود هرگز بازنویسی نمی‌شوند مگر با پرچم صریح.
ENV_FILE="$PROJECT_DIR/app/.env"

env_value() {
    sed -n -E "s/^[[:space:]]*(export[[:space:]]+)?$1=//p" "$ENV_FILE" 2>/dev/null \
        | tail -n 1 | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | tr -d '\r' || true
}

# پاک‌سازی .env دست‌کاری‌شده (فاصله ابتدای/انتهای خط و CR ویندوزی) — نسخهٔ
# اصلی یک‌بار در ‎.env.khanomgol-backup‎ نگه داشته می‌شود.
sanitize_env_file() {
    local tmp="$ENV_FILE.sanitize.$$"
    sed -E \
        -e 's/\r$//' \
        -e 's/^[[:space:]]*//' \
        -e 's/[[:space:]]*$//' \
        -e 's/^export[[:space:]]+([A-Za-z_][A-Za-z_0-9]*)=/export \1=/' \
        -e 's/^([A-Za-z_][A-Za-z_0-9]*)=[[:space:]]+/\1=/' \
        "$ENV_FILE" > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 0; }
    if ! cmp -s "$ENV_FILE" "$tmp"; then
        [ -f "$ENV_FILE.khanomgol-backup" ] || cp "$ENV_FILE" "$ENV_FILE.khanomgol-backup"
        cat "$tmp" > "$ENV_FILE"
        say "فایل ‎app/.env‎ پاک‌سازی شد (فاصله‌ها و CR حذف شد — نسخه قبلی: ‎.env.khanomgol-backup‎)."
    fi
    rm -f "$tmp"
    return 0
}

# افزودن کلیدهای غایب — مقادیر موجود هرگز بازنویسی نمی‌شوند
merge_app_keys() {
    local key val merged=0
    while IFS='|' read -r key val; do
        [ -n "$key" ] || continue
        if ! grep -Eq "^[[:space:]]*(export[[:space:]]+)?${key}=" "$ENV_FILE"; then
            if [ "$merged" -eq 0 ]; then
                printf '\n# کلیدهای خودکار افزوده‌شده توسط deploy/deploy_cpanel.sh\n' >> "$ENV_FILE"
                merged=1
            fi
            printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
        fi
    done <<APPEOF
VITE_API_ENABLED|false
VITE_API_TIMEOUT|6000
APPEOF
    if ! grep -Eq "^[[:space:]]*(export[[:space:]]+)?VITE_API_BASE=" "$ENV_FILE"; then
        printf '\n# آدرس بک‌اند REST فروشگاه — دامنهٔ واقعی بک‌اند مستقرشده را بگذارید\nVITE_API_BASE=https://api.example.ir/api/v1\n' >> "$ENV_FILE"
        warn "کلید VITE_API_BASE با placeholder به ‎app/.env‎ اضافه شد — آدرس بک‌اند واقعی را بنویسید."
    fi
    if ! grep -Eq "^[[:space:]]*(export[[:space:]]+)?VITE_BASE=" "$ENV_FILE"; then
        printf '\n# مسیر پایهٔ انتشار — cPanel/دامنهٔ اختصاصی: /  |  GitHub Pages: /food-shop/\nVITE_BASE=%s\n' "$BASE_CLI" >> "$ENV_FILE"
    fi
    return 0
}

# اعمال --api-base (بازنویسی VITE_API_BASE در .env)
apply_api_base_cli() {
    [ -n "$API_BASE_CLI" ] || return 0
    if grep -Eq "^[[:space:]]*(export[[:space:]]+)?VITE_API_BASE=" "$ENV_FILE"; then
        local tmp="$ENV_FILE.apibase.$$"
        awk -v v="$API_BASE_CLI" '
            /^[[:space:]]*(export[[:space:]]+)?VITE_API_BASE=/ && !done { sub(/=.*/, "=" v); done=1 }
            { print }
        ' "$ENV_FILE" > "$tmp" && mv "$tmp" "$ENV_FILE"
        say "VITE_API_BASE در ‎app/.env‎ برابر «$API_BASE_CLI» شد (از --api-base)."
    else
        printf 'VITE_API_BASE=%s\n' "$API_BASE_CLI" >> "$ENV_FILE"
        say "VITE_API_BASE به ‎app/.env‎ اضافه شد: $API_BASE_CLI"
    fi
}

# اعمال --api-enabled (بازنویسی VITE_API_ENABLED=true)
apply_api_enabled_cli() {
    [ "$API_ENABLED_CLI" -eq 1 ] || return 0
    if grep -Eq "^[[:space:]]*(export[[:space:]]+)?VITE_API_ENABLED=" "$ENV_FILE"; then
        local tmp="$ENV_FILE.apien.$$"
        awk '
            /^[[:space:]]*(export[[:space:]]+)?VITE_API_ENABLED=/ && !done { sub(/=.*/, "=true"); done=1 }
            { print }
        ' "$ENV_FILE" > "$tmp" && mv "$tmp" "$ENV_FILE"
    else
        printf 'VITE_API_ENABLED=true\n' >> "$ENV_FILE"
    fi
    say "VITE_API_ENABLED=true شد (اتصال به بک‌اند فعال است)."
}

# کنترل آدرس بک‌اند — اگر هنوز localhost یا placeholder است، هشدار قوی
api_base_check() {
    local b
    b="$(env_value VITE_API_BASE)"
    local en
    en="$(env_value VITE_API_ENABLED)"
    if [ "$en" != "true" ]; then
        info "اتصال بک‌اند خاموش است (VITE_API_ENABLED=$en) — اپ با دادهٔ محلی بیلد می‌شود."
    fi
    if [ -z "$b" ]; then
        warn "VITE_API_BASE خالی است — اپ به دادهٔ محلی برمی‌گردد."
        return 0
    fi
    case "$b" in
        *127.0.0.1*|*localhost*|*example.ir*|*example.com*)
            warn "VITE_API_BASE هنوز روی localhost/placeholder است:
    $b
برای اتصال واقعی، در فایل ‎app/.env‎ بنویسید:
    VITE_API_ENABLED=true
    VITE_API_BASE=https://دامنه-بک‌اند-شما/api/v1
یا با پرچم اجرا کنید:
    bash deploy/deploy_cpanel.sh --build --api-base https://دامنه-بک‌اند-شما/api/v1 --api-enabled" ;;
        *) info "آدرس بک‌اند: $b" ;;
    esac
}

# ------------------------------------------------- ابزار یافتن Node.js ----
# Vite 5 به Node ≥18 نیاز دارد. نسخهٔ واقعی هر کاندید بررسی می‌شود تا Node
# قدیمی سیستمی هرگز انتخاب نشود.
node_ok() {
    local v
    v="$("$1" --version 2>/dev/null)" || return 1
    v="${v#v}"
    [ -n "$v" ] || return 1
    local major="${v%%.*}"
    case "$major" in
        ''|*[!0-9]*) return 1 ;;
        1[8-9]|[2-9][0-9]|[1-9][0-9][0-9]) return 0 ;;
        *) return 1 ;;
    esac
}

find_node() {
    local candidate
    local -a candidates=()
    [ -n "$NODE_BIN" ] && candidates+=("$NODE_BIN")
    candidates+=(
        node
        nodejs
        /opt/alt/alt-nodejs18/bin/node
        /opt/alt/alt-nodejs20/bin/node
        /opt/alt/alt-nodejs22/bin/node
        /usr/local/bin/node
        /usr/bin/node
    )
    while IFS= read -r candidate; do
        candidates+=("$candidate")
    done < <(ls /opt/alt/alt-nodejs*/bin/node 2>/dev/null | sort -rV || true)

    for candidate in "${candidates[@]}"; do
        [ -n "$candidate" ] || continue
        if { [ -x "$candidate" ] || command -v "$candidate" >/dev/null 2>&1; } && node_ok "$candidate"; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# venv سی‌پنل (Setup Node.js App) — در ‎~/nodevenv/<پوشه>/<نسخه>‎
find_cpanel_nodevenv() {
    [ -d "$HOME/nodevenv" ] || return 1
    local proj_base rel root ver_dir
    proj_base="$(basename "$PROJECT_DIR")"
    local -a roots=( "$HOME/nodevenv/$proj_base" )
    case "$PROJECT_DIR" in
        "$HOME"/*)
            rel="${PROJECT_DIR#${HOME}/}"
            [ -n "$rel" ] && [ "$rel" != "$PROJECT_DIR" ] && roots+=( "$HOME/nodevenv/$rel" )
            ;;
    esac
    for root in "${roots[@]}"; do
        [ -d "$root" ] || continue
        for ver_dir in $(ls -1d "$root"/*/ 2>/dev/null | sort -rV); do
            if [ -x "${ver_dir%/}/bin/node" ] && node_ok "${ver_dir%/}/bin/node"; then
                echo "${ver_dir%/}/bin/node"
                return 0
            fi
        done
    done
    return 1
}

# --------------------------------------------- استقرار dist (یا بیلد) ----
# منبع انتشار: با --build پوشهٔ app/dist (تازه بیلدشده)، بدون --build ریشهٔ
# ریپو (خروجی بیلدِ commit‌شده برای GitHub Pages).
SRC_DIR="$PROJECT_DIR"

if [ "$DO_BUILD" -eq 1 ]; then
    # ---- مسیر بیلد روی هاست (با --build) ----
    if [ -f "$ENV_FILE" ]; then
        say "فایل ‎app/.env‎ موجود است."
        sanitize_env_file
        merge_app_keys
    else
        say "فایل ‎app/.env‎ وجود ندارد؛ از ‎.env.example‎ ساخته می‌شود ..."
        cp "$PROJECT_DIR/app/.env.example" "$ENV_FILE"
        merge_app_keys
        say "فایل ساخته شد: $ENV_FILE"
    fi
    apply_api_base_cli
    apply_api_enabled_cli
    api_base_check

    NODE_BIN="$(find_node)" || NODE_BIN="$(find_cpanel_nodevenv)" || true
    [ -n "$NODE_BIN" ] || die "Node ≥18 روی هاست پیدا نشد.
مسیرهای بررسی‌شده: node در PATH، ‎/opt/alt/alt-nodejs18..22/bin/node‎ (کلودلینوکس)،
‎/usr/local/bin/node‎ و ‎/usr/bin/node‎.
راه‌حل ۱ (پیشنهادی): بیلد را روی ماشین محلی بزنید و خروجی (index.html + assets/)
را در ریشهٔ ریپو commit/push کنید (پیش‌فرض اسکریپت، بدون --build).
راه‌حل ۲: در cPanel بخش «Setup Node.js App» یک برنامه با Node 18 بسازید یا مسیر دقیق Node را بدهید:
    bash deploy/deploy_cpanel.sh --build --node /opt/alt/alt-nodejs18/bin/node"
    NODE_VER="$("$NODE_BIN" --version 2>/dev/null)"
    info "Node انتخاب‌شده: $NODE_BIN (نسخه $NODE_VER)"
    NODE_DIR="$(dirname "$NODE_BIN")"
    NPM_BIN="$NODE_DIR/npm"
    [ -x "$NPM_BIN" ] || NPM_BIN="$(command -v npm 2>/dev/null)" || die "npm کنار Node ($NODE_BIN) پیدا نشد."
    export PATH="$NODE_DIR:$PATH"

    say "نصب وابستگی‌ها (چند دقیقه صبر کنید) ..."
    if [ -f "$PROJECT_DIR/app/package-lock.json" ]; then
        ( cd "$PROJECT_DIR/app" && "$NPM_BIN" ci --no-audit --no-fund ) 2>/tmp/npm-install.err || {
            warn "«npm ci» ناموفق بود؛ تلاش با «npm install» ..."
            ( cd "$PROJECT_DIR/app" && "$NPM_BIN" install --no-audit --no-fund ) || die "نصب وابستگی‌ها ناموفق بود.
$(tail -n 15 /tmp/npm-install.err 2>/dev/null)"
        }
    else
        ( cd "$PROJECT_DIR/app" && "$NPM_BIN" install --no-audit --no-fund ) || die "نصب وابستگی‌ها ناموفق بود."
    fi

    say "بیلد Vite با مسیر پایهٔ «$BASE_CLI» ..."
    ( cd "$PROJECT_DIR/app" && VITE_BASE="$BASE_CLI" "$NPM_BIN" run build ) || die "بیلد Vite ناموفق بود.
خروجی خطا را بالا بررسی کنید؛ معمولاً به Node قدیمی یا خطای سینتکس سورس مربوط است."

    [ -f "$PROJECT_DIR/app/dist/index.html" ] || die "بیلد انجام شد اما ‎app/dist/index.html‎ ساخته نشد."
    SRC_DIR="$PROJECT_DIR/app/dist"
    say "بیلد کامل شد: ‎app/dist/‎ (منبع انتشار)"
else
    # ---- پیش‌فرض: استقرار بیلدِ commit‌شدهٔ ریشهٔ ریپو ----
    [ -f "$SRC_DIR/index.html" ] || die "‎index.html‎ بیلدشده در ریشهٔ ریپو پیدا نشد.
روی ماشین محلی (با Node ≥18):
    cd app && npm ci && npm run build
سپس محتوای ‎app/dist/‎ را به ریشهٔ ریپو کپی، commit و push کنید، و روی هاست
«git pull» بزنید و دوباره اجرا کنید:    bash deploy/deploy_cpanel.sh
(یا برای بیلد روی خود هاست: bash deploy/deploy_cpanel.sh --build)"
    say "استقرار از بیلدِ commit‌شدهٔ ریشهٔ ریپو (بدون نیاز به Node روی هاست)."
    if [ -n "$API_BASE_CLI" ]; then
        warn "--api-base فقط با --build مؤثر است (آدرس بک‌اند در زمان بیلد داخل assets می‌رود)."
    fi
fi

# کنترل مسیر پایهٔ bake‌شده در index.html — هشدار توافق GitHub Pages
BAKED_BASE_CHECK() {
    local first_asset
    first_asset="$(grep -oE '(href|src)=\"[^\"]*assets/index[^\"]*\"' "$SRC_DIR/index.html" 2>/dev/null | head -n1 | sed 's/.*=\"//; s/\"$//')" || true
    if [ -z "$first_asset" ]; then
        info "مسیر دارایی‌ها در index.html به‌صورت نسبی/غیرمتعارف است (بررسی دستی کنید)."
        return 0
    fi
    case "$first_asset" in
        /food-shop/*)
            warn "این بیلد برای GitHub Pages با مسیر پایهٔ «/food-shop/» بسته شده است
($first_asset). اگر دامنهٔ cPanel را روی ریشهٔ وب نشانه بروید، فایل‌های css/js لود نمی‌شوند.
راه‌حل: bash deploy/deploy_cpanel.sh --build            (پیش‌فرض ‎--base /‎ است)"
            ;;
        /assets/*|./assets/*)
            info "مسیر پایهٔ بیلد برای دامنهٔ اختصاصی مناسب است: $first_asset"
            ;;
        *)
            info "مسیر پایهٔ بیلد: $first_asset"
            ;;
    esac
}
BAKED_BASE_CHECK

# خواندن آدرس بک‌اندِ bake‌شده داخل باندل (برای نمایش/کنترل)
baked_api_base() {
    grep -hoE 'https?://[a-zA-Z0-9._-]+(:[0-9]+)?[^"'"'"']*/api/v[0-9]+' \
        "$SRC_DIR"/assets/index-*.js 2>/dev/null | head -n1 || true
}
BAKED_API="$(baked_api_base)"
if [ -n "$BAKED_API" ]; then
    info "آدرس بک‌اندِ bake‌شده در باندل: $BAKED_API"
    case "$BAKED_API" in
        *127.0.0.1*|*localhost*|*example.ir*|*example.com*)
            warn "آدرس بک‌اندِ داخل باندل هنوز localhost/placeholder است ($BAKED_API) — اپ به دادهٔ محلی برمی‌گردد.
روی ماشین محلی ‎app/.env‎ را اصلاح کنید (VITE_API_ENABLED=true و VITE_API_BASE=https://دامنه-بک‌اند/api/v1)،
سپس بیلد و commit/push، و روی هاست «git pull»." ;;
    esac
else
    info "اتصال بک‌اند در باندل فعال نیست — اپ با دادهٔ محلی کار می‌کند (رفتار GitHub Pages)."
fi

DIST_FILES=$(find "$SRC_DIR" -type f | wc -l | tr -d ' ')
info "تعداد فایل‌های منبع انتشار: $DIST_FILES"

# --------------------------------------------------------- ریشهٔ وب مقصد ----
if [ -z "$WEBROOT" ]; then
    if [ -d "$HOME/public_html" ]; then
        WEBROOT="$HOME/public_html"
    else
        die "ریشهٔ وب پیدا نشد. مسیر را با --webroot بدهید، مثلاً:
    bash deploy/deploy_cpanel.sh --webroot ~/public_html
(یا برای زیردامنه/افزون‌دامنه: --webroot ~/shop.example.ir)"
    fi
fi
mkdir -p "$WEBROOT"
info "ریشهٔ وب مقصد: $WEBROOT"

case "$WEBROOT" in
    "$PROJECT_DIR"|"$PROJECT_DIR"/*) warn "ریشهٔ وب همان پوشهٔ ریپو است؛ قواعد امنیتی .htaccess نصب می‌شود ولی توصیه می‌شود ریپو را خارج از ریشهٔ وب نگه دارید (مثلاً ‎~/repos/food-shop‎) و فقط فایل‌های انتشار را کپی کنید." ;;
esac

# ---------------------------------------------------- همگام‌سازی → webroot ----
# غیرمخرب: پوشهٔ assets/ هش‌شده کاملاً جایگزین می‌شود و فایل‌های سطح‌بالای
# انتشار (index.html + محتویات app/public) کپی می‌شوند. سایر فایل‌های ریشهٔ
# وب (مثل cgi-bin) دست نمی‌خورند — مگر با --clean.
if [ "$CLEAN_WEBROOT" -eq 1 ]; then
    warn "--clean فعال: پاک‌سازی کامل ریشهٔ وب قبل از کپی ..."
    find "$WEBROOT" -mindepth 1 -maxdepth 1 ! -name 'cgi-bin' -exec rm -rf {} +
fi

# فایل‌های سطح‌بالای انتشار: index.html بیلد + محتویات app/public (404.html،
# robots.txt، sitemap.xml، .nojekyll). اگر از app/dist می‌آید، همه از همان‌جاست.
say "همگام‌سازی فایل‌های انتشار با ریشهٔ وب ..."
cp -a "$SRC_DIR/index.html" "$WEBROOT/index.html"
if [ "$SRC_DIR" = "$PROJECT_DIR/app/dist" ]; then
    find "$SRC_DIR" -mindepth 1 -maxdepth 1 ! -name assets ! -name index.html -exec cp -a {} "$WEBROOT/" \;
else
    # بیلد commit‌شدهٔ ریشهٔ ریپو: فقط نام‌های شناخته‌شدهٔ app/public کپی شود
    # تا سورس ریپو (app/، deploy/، scripts/ و …) به وب درز نکند.
    ( cd "$PROJECT_DIR/app/public" && find . -mindepth 1 -maxdepth 1 -print0 ) 2>/dev/null \
      | while IFS= read -r -d '' f; do
            rel="${f#./}"
            [ -e "$SRC_DIR/$rel" ] && cp -a "$SRC_DIR/$rel" "$WEBROOT/"
        done
fi

# جایگزینی کامل پوشهٔ assets
rm -rf "$WEBROOT/assets"
mkdir -p "$WEBROOT/assets"
if [ -d "$SRC_DIR/assets" ]; then
    cp -a "$SRC_DIR/assets/." "$WEBROOT/assets/" 2>/dev/null || cp -a "$SRC_DIR/assets/"* "$WEBROOT/assets/"
fi
say "فایل‌ها استقرار یافتند."

# -------------------------------------------------------- قواعد .htaccess ----
HTACCESS_FILE="$WEBROOT/.htaccess"
HT_MARKER="# BEGIN KHANOMGOL-SPA"
write_htaccess_block() {
    cat << 'HTACCESS'
# BEGIN KHANOMGOL-SPA
# ── استقرار SPA فروشگاه خانم گل (تولیدشده توسط deploy/deploy_cpanel.sh) ──
Options -Indexes

# فایل‌ها و مسیرهای حساس ریپو — هرگز از وب قابل دانلود نباشند
RewriteEngine On
RewriteRule (^|/)\.git(/|$) - [F,L]
RewriteRule (^|/)(app|deploy|scripts|download|upload|skills|tool-results)(/|$) - [F,L]
<FilesMatch "^\.env(\.[a-zA-Z0-9_-]+)?$|\.(vue|md|sh|toml|lock|example|gitignore|gitattributes|bak)$">
    Require all denied
</FilesMatch>
<FilesMatch "^(package\.json|package-lock\.json|vite\.config\.(js|ts)|README\.md)$">
    Require all denied
</FilesMatch>

# فشرده‌سازی gzip (اگر mod_deflate فعال باشد)
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/css text/javascript application/javascript application/json application/xml image/svg+xml
</IfModule>

# هدرهای کش — دارایی‌های هش‌شده طولانی، index.html بدون کش
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/html "access plus 0 seconds"
    ExpiresByType application/json "access plus 0 seconds"
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType text/javascript "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/webp "access plus 1 year"
    ExpiresByType image/x-icon "access plus 1 year"
    ExpiresByType font/woff "access plus 1 year"
    ExpiresByType font/woff2 "access plus 1 year"
</IfModule>
<IfModule mod_headers.c>
    <FilesMatch "\.(js|css|svg|png|jpe?g|gif|webp|ico|woff2?)$">
        Header set Cache-Control "public, max-age=31536000, immutable"
    </FilesMatch>
    <FilesMatch "index\.html$">
        Header set Cache-Control "no-cache, no-store, must-revalidate"
    </FilesMatch>
    # هدرهای امنیتی پایه (امن و بدون اثر بر کارکرد)
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Permissions-Policy "geolocation=(), camera=(), microphone=()"
    # Content-Security-Policy — پیشنهادی؛ قبل از فعال‌سازی همین بلوک را با دامنهٔ
    # واقعی بک‌اند در connect-src چک کنید (کد اپ هیچ inline-script اجرایی ندارد):
    # Header always set Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' https://z-cdn.chatglm.cn data:; connect-src 'self' https:; frame-ancestors 'self'; base-uri 'self'; form-action 'self'"
</IfModule>

# مسیریابی SPA — هر درخواست غیرِ فایل/پوشهٔ واقعی به index.html برمی‌گردد
# (تا /products، /product/1، /cart، /track و … با رفرش مستقیم کار کنند)
<IfModule mod_rewrite.c>
    RewriteCond %{REQUEST_FILENAME} -f [OR]
    RewriteCond %{REQUEST_FILENAME} -d
    RewriteRule ^ - [L]
    RewriteRule ^ index.html [L]
</IfModule>
# END KHANOMGOL-SPA
HTACCESS
}

if [ ! -f "$HTACCESS_FILE" ]; then
    write_htaccess_block > "$HTACCESS_FILE"
    say ".htaccess ساخته شد (SPA fallback + فشرده‌سازی + کش + محافظت)."
elif grep -q "$HT_MARKER" "$HTACCESS_FILE" 2>/dev/null; then
    # بلوک قبلی با نسخهٔ به‌روز جایگزین می‌شود (قواعد خارج از بلوک دست نمی‌خورند)
    local_tmp_ht="$HTACCESS_FILE.repl.$$"
    awk -v marker="$HT_MARKER" '
        $0 == marker { inblock=1; skip=1; next }
        $0 == "# END KHANOMGOL-SPA" { inblock=0; skip=0; next }
        !inblock { print }
    ' "$HTACCESS_FILE" > "$local_tmp_ht" 2>/dev/null || cp "$HTACCESS_FILE" "$local_tmp_ht"
    printf '\n' >> "$local_tmp_ht"
    write_htaccess_block >> "$local_tmp_ht"
    cat "$local_tmp_ht" > "$HTACCESS_FILE"
    rm -f "$local_tmp_ht"
    say "بلوک KHANOMGOL-SPA در .htaccess به‌روزرسانی شد."
else
    if [ ! -f "$HTACCESS_FILE.khanomgol-backup" ]; then
        cp "$HTACCESS_FILE" "$HTACCESS_FILE.khanomgol-backup"
        info "نسخهٔ قبلی .htaccess در ‎.htaccess.khanomgol-backup‎ نگه داشته شد."
    fi
    printf '\n' >> "$HTACCESS_FILE"
    write_htaccess_block >> "$HTACCESS_FILE"
    say "قواعد SPA به .htaccess موجود افزوده شد."
fi

# ------------------------------------------------------------------ خلاصه ----
echo ""
echo -e "${C_GREEN}═══════════════════════════════════════════════════════════════${C_OFF}"
say "استقرار کامل شد."
echo -e "${C_GREEN}═══════════════════════════════════════════════════════════════${C_OFF}"
echo ""
echo "قدم‌های بعدی:"
echo ""
echo "  ۱. مسیر پایه: بیلدِ commit‌شدهٔ ریپو برای GitHub Pages با «/food-shop/» بسته شده؛"
echo "     اگر دامنهٔ cPanel مستقیم به ریشهٔ وب اشاره می‌کند، یک‌بار بگیرید:"
echo "       bash deploy/deploy_cpanel.sh --build"
echo ""
echo "  ۲. اتصال بک‌اند (اختیاری): در ‎app/.env‎ مقادیر VITE_API_ENABLED=true و"
echo "     VITE_API_BASE=https://دامنه-بک‌اند/api/v1 را بگذارید و دوباره بیلد/استقرار کنید:"
echo "       bash deploy/deploy_cpanel.sh --build --api-base https://دامنه-بک‌اند/api/v1 --api-enabled"
echo "     قرارداد کامل نقاط پایانی در ‎app/.env.example‎ توضیح داده شده است."
echo ""
echo "  ۳. اگر بک‌اند هم روی cPanel است، متغیر CORS بک‌اند را روی دامنهٔ فرانت تنظیم کنید"
echo "     (مثلاً در Django: CORS_ALLOWED_ORIGINS=https://دامنه-فرانت-شما)."
echo ""
echo "  ۴. در cPanel → «Domains»/«Subdomains» دامنه/زیردامنهٔ فروشگاه را روی"
echo "     ریشهٔ وب مقصد ($WEBROOT) تنظیم کنید (اگر قبلاً نبوده)."
echo ""
echo -e "  ۵. ${C_YELLOW}AutoSSL${C_OFF} را در cPanel فعال کنید تا https کار کند؛ سپس VITE_API_BASE"
echo "     را روی https:// بک‌اند بگذارید (و دوباره بیلد + استقرار)."
echo ""
echo "  ۶. صفحه را در مرورگر باز کنید:"
echo "     • صفحهٔ اصلی:      https://دامنه-شما/"
echo "     • فروشگاه:        https://دامنه-شما/products"
echo "     • پیگیری سفارش:   https://دامنه-شما/track"
echo "     • اگر باز نشد / ۵۰۰ داد: راهنمای عیب‌یابی → deploy/GUIDE-CPANEL-FA.md"
echo ""
echo "  ۷. به‌روزرسانی پس از تغییر کد (روی ماشین محلی):"
echo "       cd app && npm run build && cp -r dist/. .. && git add -A && git commit -m 'build' && git push"
echo "       سپس روی هاست: git pull && bash deploy/deploy_cpanel.sh"
echo "     (روی هاست نیازی به Node/بیلد نیست — بیلد در گیت است.)"
echo ""
echo -e "  ۸. راهنمای کامل گام‌به‌گام استقرار و عیب‌یابی: ${C_YELLOW}deploy/GUIDE-CPANEL-FA.md${C_OFF}"
echo ""
