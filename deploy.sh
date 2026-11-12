#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  فروشگاه خانم گل — استقرار یکپارچهٔ فرانت + بک‌اند روی cPanel (بدون Node/بیلد روی هاست)
#
#  یک دستور:      bash deploy.sh --domain khanomgol.ir
#
#  مراحل:
#    ۱. فرانت: پوشهٔ از پیش‌ساخته‌شدهٔ host-dist/ (commit شده) در یک پوشهٔ موقت کپی و
#       دامنهٔ واقعی جایگزین جانشین __SITE_HOST__ می‌شود (canonical، sitemap، آدرس API)،
#       سپس با deploy/deploy_cpanel.sh --dist به ریشهٔ وب می‌رود (.htaccess هم ساخته می‌شود).
#    ۲. بک‌اند: backend/deploy/deploy_cpanel.sh (venv، pip، migrate، seed، static، Passenger).
#    ۳. بررسی نهایی: درخواست واقعی به سایت و API؛ اگر ۵xx بود لاگ‌ها و عیب‌یابی خودکار چاپ می‌شود.
#
#  گزینه‌ها:
#    --api-base <url>   آدرس کامل API (پیش‌فرض: از «Setup Python App» خودکار؛ مثلاً https://api.دامنه/api/v1)
#    --domain <دامنه>   دامنهٔ سایت بدون https (پیش‌فرض: اولین دامنهٔ ALLOWED_HOSTS در backend/.env)
#    --webroot <مسیر>   ریشهٔ وب (پیش‌فرض ~/public_html)
#    --skip-front       فقط بک‌اند
#    --skip-back        فقط فرانت
#    --fetch-assets     تصاویر محصولات و لوگوی دایناکد را مستقیم داخل <ریشهٔ وب>/img دانلود می‌کند (بدون Node؛ نیازمند دسترسی هاست به CDN)
#    --check            فقط بررسی و عیب‌یابی (بدون استقرار)
#    --insecure         بررسی با http به‌جای https (قبل از نصب SSL)
#
#  نسخهٔ آمادهٔ هاست روی ماشین محلی ساخته می‌شود:  bash scripts/build_host.sh
#  به‌روزرسانی بعدی روی هاست:  git pull && bash deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="${KHANOMGOL_DOMAIN:-}"; API_BASE="${KHANOMGOL_API_BASE:-}"; WEBROOT=""; DO_FRONT=1; DO_BACK=1; CHECK_ONLY=0; FETCH=0; SCHEME=https

if [ -t 1 ]; then G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; O='\033[0m'; else G=; Y=; R=; B=; O=; fi
say(){ echo -e "${G}✔${O} $*"; }; info(){ echo -e "${B}ℹ${O} $*"; }; warn(){ echo -e "${Y}⚠${O} $*" >&2; }
die(){ echo -e "${R}✘ خطا:${O} $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --domain) [ $# -ge 2 ] || die "--domain نیاز به مقدار دارد"; DOMAIN="$2"; shift 2 ;;
    --domain=*) DOMAIN="${1#*=}"; shift ;;
    --api-base) [ $# -ge 2 ] || die "--api-base نیاز به مقدار دارد"; API_BASE="$2"; shift 2 ;;
    --api-base=*) API_BASE="${1#*=}"; shift ;;
    --webroot) [ $# -ge 2 ] || die "--webroot نیاز به مسیر دارد"; WEBROOT="$2"; shift 2 ;;
    --webroot=*) WEBROOT="${1#*=}"; shift ;;
    --skip-front) DO_FRONT=0; shift ;;
    --skip-back) DO_BACK=0; shift ;;
    --check) CHECK_ONLY=1; shift ;;
    --fetch-assets) FETCH=1; shift ;;
    --insecure) SCHEME=http; shift ;;
    -h|--help) awk 'NR>1 { if ($0 ~ /^#/) { sub(/^# ? ?/, ""); print } else exit }' "$0"; exit 0 ;;
    *) warn "آرگومان ناشناخته: $1" ; shift ;;
  esac
done
[ -n "$WEBROOT" ] && WEBROOT="${WEBROOT/#\~/$HOME}"
[ -z "$WEBROOT" ] && WEBROOT="$HOME/public_html"

echo -e "\n${B}═══════════════════════════════════════════════════════════════${O}"
echo -e "${B}  فروشگاه خانم گل — استقرار یکپارچه (فرانت + بک‌اند)${O}"
echo -e "${B}═══════════════════════════════════════════════════════════════${O}"

# موقعیت فعلی لاگ‌ها؛ در عیب‌یابی فقط خطوط «بعد از این استقرار» نشان داده می‌شود (نه traceback های قدیمی)
declare -A LOGPOS
for lf in "$ROOT/backend/logs/django-error.log" "$ROOT/stderr.log" "$ROOT/backend/stderr.log" "$HOME/logs/error_log"; do
  [ -f "$lf" ] && LOGPOS["$lf"]="$(stat -c %s "$lf" 2>/dev/null || echo 0)"
done

# ── دامنه ──
ENVF="${KHANOMGOL_ENV_FILE:-$ROOT/backend/.env}"
BACKEND_SCRIPT="${KHANOMGOL_BACKEND_SCRIPT:-$ROOT/backend/deploy/deploy_cpanel.sh}"
if [ -z "$DOMAIN" ] && [ -f "$ENVF" ]; then
  DOMAIN="$(grep -E '^ALLOWED_HOSTS=' "$ENVF" | head -n1 | cut -d= -f2- | tr ',' '\n' | tr -d ' \r"' | grep -vE '^\*$|^\.|^$|^localhost|^127\.' | head -n1)"
fi
DOMAIN="${DOMAIN#http://}"; DOMAIN="${DOMAIN#https://}"; DOMAIN="${DOMAIN%%/*}"
[ -n "$DOMAIN" ] || die "دامنه مشخص نیست. اجرا کنید:  bash deploy.sh --domain دامنه-شما.ir"
case "$DOMAIN" in *[!a-zA-Z0-9.:-]*) die "دامنهٔ نامعتبر: $DOMAIN" ;; esac
info "دامنه: $DOMAIN | ریشهٔ وب: $WEBROOT | ریپو: $ROOT"

# ── آدرس API: از پایتون‌اپ ثبت‌شده در cPanel (دامنه/زیردامنه + مسیر) ──
if [ -z "$API_BASE" ]; then
  SEL="$HOME/.cl.selector/python-selector.json"
  if [ -f "$SEL" ] && command -v python3 >/dev/null 2>&1; then
    API_BASE="$(python3 - "$SEL" "$(basename "$ROOT")" <<'PYAPI' 2>/dev/null
import json, sys
d = json.load(open(sys.argv[1])); apps = (d.get("apps") or d) if isinstance(d, dict) else {}
for name, a in apps.items():
    if isinstance(a, dict) and a.get("domain") and sys.argv[2] in name:
        uri = (a.get("app_uri") or "").strip("/")
        print("https://%s%s/api/v1" % (a["domain"], ("/" + uri) if uri else "")); break
PYAPI
)"
  fi
  [ -n "$API_BASE" ] && info "آدرس API از Setup Python App تشخیص داده شد: $API_BASE" \
                     || { API_BASE="https://$DOMAIN/food-shop/api/v1"; warn "اپ پایتون در cPanel پیدا نشد؛ پیش‌فرض: $API_BASE (با --api-base تغییر دهید)"; }
fi
API_BASE="${API_BASE%/}"
case "$API_BASE" in http://*|https://*) ;; *) die "--api-base باید با http(s):// شروع شود: $API_BASE" ;; esac
API_ORIGIN="$(echo "$API_BASE" | sed -E 's#^(https?://[^/]+).*#\1#')"; API_HOST="${API_ORIGIN#*://}"

env_get() { grep -E "^$1=" "$ENVF" 2>/dev/null | tail -n1 | cut -d= -f2- | tr -d '\r'; }
env_set() {  # env_set KEY VALUE — مقدار موجود را جایگزین یا کلید را اضافه می‌کند
  local k="$1" v="$2" tmp; tmp="$(mktemp)"
  if grep -qE "^$k=" "$ENVF"; then V="$v" awk -v k="$k" 'BEGIN{v=ENVIRON["V"];d=0} { if(!d && index($0,k"=")==1){print k"="v;d=1}else print }' "$ENVF" > "$tmp"
  else cp "$ENVF" "$tmp"; printf '\n%s=%s\n' "$k" "$v" >> "$tmp"; fi
  cat "$tmp" > "$ENVF"; rm -f "$tmp"
}

# ── تصاویر محلی (اختیاری): دانلود مستقیم روی هاست ──
if [ "$FETCH" -eq 1 ]; then
  info "دانلود تصاویر محصولات و لوگو در $WEBROOT/img ..."
  mkdir -p "$WEBROOT/img"
  python3 "$ROOT/scripts/fetch_assets.py" --out "$WEBROOT/img" ${KHANOMGOL_ASSETS_ARGS:-} \
    && say "تصاویر دانلود شد." \
    || warn "دانلود تصاویر کامل نشد (هاست به CDN دسترسی ندارد؟). روی سیستم دیگری با اینترنت آزاد: python3 scripts/fetch_assets.py && bash scripts/build_host.sh و commit/push."
fi

# ── ۱) فرانت ──
if [ "$DO_FRONT" -eq 1 ] && [ "$CHECK_ONLY" -eq 0 ]; then
  [ -f "$ROOT/host-dist/index.html" ] || die "host-dist/ پیدا نشد. روی ماشین محلی: bash scripts/build_host.sh و سپس commit/push و روی هاست git pull."
  STAGE="$(mktemp -d "${TMPDIR:-/tmp}/kg-front.XXXXXX")"
  trap 'rm -rf "$STAGE"' EXIT
  cp -a "$ROOT/host-dist/." "$STAGE/"
  find "$STAGE" -type f \( -name '*.html' -o -name '*.js' -o -name '*.css' -o -name '*.xml' -o -name '*.txt' \) -print0 \
    | xargs -0 sed -i -e "s/__SITE_HOST__/$DOMAIN/g" -e "s#__API_BASE__#$API_BASE#g"
  LEFT="$(grep -rlE '__SITE_HOST__|__API_BASE__' "$STAGE" 2>/dev/null | wc -l | tr -d ' ')"
  [ "$LEFT" = "0" ] || die "جانشین دامنه در $LEFT فایل باقی ماند."
  say "دامنه در فایل‌های فرانت جایگزین شد (canonical، sitemap، آدرس API)."
  bash "$ROOT/deploy/deploy_cpanel.sh" --dist "$STAGE" --webroot "$WEBROOT" || die "استقرار فرانت ناموفق بود."
fi

# ── ۲) بک‌اند ──
if [ "$DO_BACK" -eq 1 ] && [ "$CHECK_ONLY" -eq 0 ]; then
  if [ -f "$ENVF" ]; then
    [ -f "$ENVF.deploy-backup" ] || cp "$ENVF" "$ENVF.deploy-backup"
    # CORS: وقتی API روی origin دیگری است (زیردامنه)، فرانت باید مجاز باشد
    if [ "$API_HOST" != "$DOMAIN" ]; then
      CUR="$(env_get CORS_ORIGINS)"
      if [ "$CUR" = "*" ]; then warn "CORS_ORIGINS=* است؛ در تولید به $SCHEME://$DOMAIN محدود کنید."
      else
        NEWC="$CUR"
        for o in "$SCHEME://$DOMAIN" "$SCHEME://www.$DOMAIN"; do
          echo ",$NEWC," | grep -qF ",$o," || NEWC="${NEWC:+$NEWC,}$o"
        done
        [ "$NEWC" != "$CUR" ] && { env_set CORS_ORIGINS "$NEWC"; say "CORS_ORIGINS به‌روز شد: $NEWC"; }
      fi
      # API روی ریشهٔ ساب‌دامین است؛ پیشوند /food-shop برای Django غلط است
      if [ -n "$(env_get FORCE_SCRIPT_NAME)" ]; then
        env_set FORCE_SCRIPT_NAME ""; env_set STATIC_URL "/static/"
        say "FORCE_SCRIPT_NAME پاک و STATIC_URL=/static/ شد (API روی ریشهٔ $API_HOST است)."
      fi
      AH="$(env_get ALLOWED_HOSTS)"
      if [ "$AH" != "*" ] && ! echo ",$AH," | grep -qF ",$API_HOST,"; then
        warn "ALLOWED_HOSTS شامل $API_HOST نیست؛ API ۴۰۰ می‌دهد. بگذارید: ALLOWED_HOSTS=$API_HOST,$DOMAIN,www.$DOMAIN"
      fi
    fi
    # تصاویر محلی روی هاست؟ → فید ترب و SEO از همان‌جا (در غیر این صورت منبع اصلی)
    NIMG="$(ls "$WEBROOT/img" 2>/dev/null | wc -l | tr -d ' ')"
    if [ "${NIMG:-0}" -ge 30 ]; then
      [ "$(env_get LOCAL_IMAGES)" = "true" ] || { env_set LOCAL_IMAGES true; say "LOCAL_IMAGES=true شد ($NIMG تصویر روی هاست)."; }
    else
      warn "تصاویر محصولات روی هاست نیست ($NIMG فایل در $WEBROOT/img) — سایت هنوز به CDN خارجی وابسته است. روی سیستمی که دسترسی دارد: python3 scripts/fetch_assets.py && bash scripts/build_host.sh و commit/push."
    fi
    grep -qE '^SHOP_URL=.*github\.io' "$ENVF" && warn "SHOP_URL در backend/.env هنوز GitHub Pages است؛ برای فید ترب و پیامک‌ها بگذارید: SHOP_URL=$SCHEME://$DOMAIN/"
    [ "$(env_get ALLOWED_HOSTS)" = "*" ] && warn "ALLOWED_HOSTS=* است؛ در تولید بگذارید: ALLOWED_HOSTS=$API_HOST,$DOMAIN,www.$DOMAIN"
  fi
  ( cd "$ROOT/backend" && bash "$BACKEND_SCRIPT" ) || die "استقرار بک‌اند ناموفق بود."
fi

# ── هشدار Application URL ──
if [ -f "$WEBROOT/.htaccess" ]; then
  BASEURI="$(grep -E 'PassengerBaseURI' "$WEBROOT/.htaccess" 2>/dev/null | head -n1 | sed -E 's/.*PassengerBaseURI[[:space:]]+"?([^"[:space:]]*)"?.*/\1/')"
  case "$BASEURI" in
    "") ;;
    "/") warn "Application URL پایتون‌اپ روی «/» است؛ Passenger صفحهٔ اصلی فرانت را می‌گیرد. در cPanel → Setup Python App آن را به /food-shop تغییر دهید و Restart بزنید." ;;
    *) info "Application URL پایتون‌اپ: $BASEURI" ;;
  esac
fi

# ── ۳) بررسی نهایی ── (+ بررسی CORS از دید مرورگر)
echo ""; info "بررسی نهایی سایت ..."
BAD=0
probe() {  # probe <مسیر> <توضیح> <متن-مورد-انتظار-در-پاسخ>
  local url out code want="${3:-}"; case "$1" in http*) url="$1" ;; *) url="$SCHEME://$DOMAIN$1" ;; esac
  out="$(mktemp)"; code="$(curl -sS -L -m 25 -o "$out" -w '%{http_code}' "$url" 2>"$out.err")" || true; [ -n "$code" ] || code=000
  if [ "${code:0:1}" != "2" ]; then
    BAD=1; warn "$2  [$code]  $url"; head -c 200 "$out" | tr '\n' ' ' >&2; echo >&2; head -c 200 "$out.err" >&2
    grep -q "The requested resource was not found" "$out" 2>/dev/null && warn "   ↑ این صفحهٔ ۴۰۴ خودِ Django است: Passenger این مسیر را گرفته (آدرس API یا Application URL پایتون‌اپ را در Setup Python App بررسی کنید)"
  elif [ -n "$want" ] && ! grep -qF -- "$want" "$out"; then
    BAD=1; warn "$2  [$code]  $url — پاسخ همان چیزی که انتظار می‌رفت نیست (انتظار: «$want»)"; head -c 160 "$out" | tr '\n' ' ' >&2; echo >&2
  else say "$2  [$code]  $url"; fi
  rm -f "$out" "$out.err"
}
probe "/" "صفحهٔ اصلی فرانت" 'id="app"'
probe "/product/1/" "صفحهٔ محصول (پیش‌رندر)" 'application/ld+json'
probe "/sitemap.xml" "sitemap"
probe "$API_BASE/health" "سلامت API" '"ok"'
probe "$API_BASE/products" "محصولات API" '"name"'
probe "$API_BASE/torob/products?page=1" "فید ترب" '"products"'

# CORS از دید مرورگر: فرانت روی origin دیگری است و API باید آن را مجاز کند
if [ "$BAD" -eq 0 ] && [ "$API_HOST" != "$DOMAIN" ]; then
  ACAO="$(curl -sS -m 20 -D - -o /dev/null -H "Origin: $SCHEME://$DOMAIN" "$API_BASE/health" 2>/dev/null | tr -d '\r' | grep -i '^access-control-allow-origin' | head -n1)"
  if [ -n "$ACAO" ]; then say "CORS برای $SCHEME://$DOMAIN مجاز است  [$ACAO]"
  else BAD=1; warn "CORS: API هدر access-control-allow-origin برای $SCHEME://$DOMAIN نمی‌دهد → مرورگر درخواست‌های فرانت را رد می‌کند. CORS_ORIGINS در backend/.env را بررسی و touch backend/tmp/restart.txt بزنید."; fi
fi

if [ "$BAD" -ne 0 ]; then
  echo ""; warn "مشکل پیدا شد — عیب‌یابی خودکار:"
  echo "── اپ‌های پایتون ثبت‌شده در cPanel (Setup Python App) ──"
  SEL="$HOME/.cl.selector/python-selector.json"
  if [ -f "$SEL" ]; then
    python3 - "$SEL" <<'PYSEL' 2>&1 | head -30
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print("خواندن ناموفق:", e); sys.exit()
apps = (d.get("apps") or d) if isinstance(d, dict) else {}
print("  (کلیدهای فایل:", ", ".join(list(d.keys())[:8]) if isinstance(d, dict) else type(d).__name__, ")")
for name, a in (apps.items() if isinstance(apps, dict) else []):
    if isinstance(a, dict):
        print("  •", name, "| url:", a.get("app_uri"), "| domain:", a.get("domain"), "| python:", a.get("python_version"),
              "| startup:", a.get("startup_file"), "| status:", a.get("app_status"))
PYSEL
  else echo "  (فایل $SEL پیدا نشد)"; fi
  echo "── قواعد Passenger در .htaccess ها ──"
  for hf in "$WEBROOT/.htaccess" "$ROOT/.htaccess" "$ROOT/backend/.htaccess" "$WEBROOT/food-shop/.htaccess"; do
    [ -f "$hf" ] && { echo "[$hf]"; grep -nE 'Passenger(AppRoot|BaseURI|Python|AppType|StartupFile|Enabled)' "$hf" | sed 's/^/   /'; }
  done
  echo "── پاسخ خام API (هدرها) ──"
  curl -sS -I -m 20 "$API_BASE/health" 2>&1 | head -12 | sed 's/^/   /'
  echo "── محتوای ریشهٔ اپ ──"; ls -la "$ROOT" | head -30 | sed 's/^/   /'; ls -la "$ROOT/tmp" 2>/dev/null | sed 's/^/   /'

  # venv سی‌پنل در هر عمقی (مثلاً ~/virtualenv/public_html/food-shop/backend/3.11/bin/python)؛ python3 سیستمی ۳.۶ است و Django ندارد
  VPY="$(find "$HOME/virtualenv" -maxdepth 6 \( -type f -o -type l \) -path '*/bin/python' 2>/dev/null | grep -F "$(basename "$ROOT")" | sort -r | head -n1)"
  [ -z "$VPY" ] && VPY="$(find "$HOME/virtualenv" -maxdepth 6 \( -type f -o -type l \) -path '*/bin/python' 2>/dev/null | sort -r | head -n1)"
  [ -z "$VPY" ] && VPY="python3"
  echo "── diagnose.py ($VPY) ──"
  ( cd "$ROOT/backend" && "$VPY" deploy/diagnose.py "$DOMAIN" 2>&1 | tail -60 )
  for lf in "$ROOT/backend/logs/django-error.log" "$ROOT/stderr.log" "$ROOT/backend/stderr.log" "$HOME/logs/error_log" "$HOME/logs/$DOMAIN.error.log"; do
    if [ -s "$lf" ]; then
      NEW="$(tail -c +$(( ${LOGPOS[$lf]:-0} + 1 )) "$lf" 2>/dev/null | tail -n 40)"
      if [ -n "$NEW" ]; then echo "── خطوط جدید $lf (بعد از شروع این استقرار) ──"; echo "$NEW"; fi
    fi
  done
  echo ""; warn "این خروجی را (رمزی در آن نیست) برای بررسی بفرستید. بعد از رفع: touch $ROOT/tmp/restart.txt"
  exit 2
fi
say "همه‌چیز سالم است ✅  →  $SCHEME://$DOMAIN/"
