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
#    --domain <دامنه>   دامنهٔ سایت بدون https (پیش‌فرض: اولین دامنهٔ ALLOWED_HOSTS در backend/.env)
#    --webroot <مسیر>   ریشهٔ وب (پیش‌فرض ~/public_html)
#    --skip-front       فقط بک‌اند
#    --skip-back        فقط فرانت
#    --check            فقط بررسی و عیب‌یابی (بدون استقرار)
#    --insecure         بررسی با http به‌جای https (قبل از نصب SSL)
#
#  نسخهٔ آمادهٔ هاست روی ماشین محلی ساخته می‌شود:  bash scripts/build_host.sh
#  به‌روزرسانی بعدی روی هاست:  git pull && bash deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="${KHANOMGOL_DOMAIN:-}"; WEBROOT=""; DO_FRONT=1; DO_BACK=1; CHECK_ONLY=0; SCHEME=https

if [ -t 1 ]; then G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; O='\033[0m'; else G=; Y=; R=; B=; O=; fi
say(){ echo -e "${G}✔${O} $*"; }; info(){ echo -e "${B}ℹ${O} $*"; }; warn(){ echo -e "${Y}⚠${O} $*" >&2; }
die(){ echo -e "${R}✘ خطا:${O} $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    --domain) [ $# -ge 2 ] || die "--domain نیاز به مقدار دارد"; DOMAIN="$2"; shift 2 ;;
    --domain=*) DOMAIN="${1#*=}"; shift ;;
    --webroot) [ $# -ge 2 ] || die "--webroot نیاز به مسیر دارد"; WEBROOT="$2"; shift 2 ;;
    --webroot=*) WEBROOT="${1#*=}"; shift ;;
    --skip-front) DO_FRONT=0; shift ;;
    --skip-back) DO_BACK=0; shift ;;
    --check) CHECK_ONLY=1; shift ;;
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
ENVF="$ROOT/backend/.env"
if [ -z "$DOMAIN" ] && [ -f "$ENVF" ]; then
  DOMAIN="$(grep -E '^ALLOWED_HOSTS=' "$ENVF" | head -n1 | cut -d= -f2- | tr ',' '\n' | tr -d ' \r"' | grep -vE '^\*$|^\.|^$|^localhost|^127\.' | head -n1)"
fi
DOMAIN="${DOMAIN#http://}"; DOMAIN="${DOMAIN#https://}"; DOMAIN="${DOMAIN%%/*}"
[ -n "$DOMAIN" ] || die "دامنه مشخص نیست. اجرا کنید:  bash deploy.sh --domain دامنه-شما.ir"
case "$DOMAIN" in *[!a-zA-Z0-9.:-]*) die "دامنهٔ نامعتبر: $DOMAIN" ;; esac
info "دامنه: $DOMAIN | ریشهٔ وب: $WEBROOT | ریپو: $ROOT"

# ── ۱) فرانت ──
if [ "$DO_FRONT" -eq 1 ] && [ "$CHECK_ONLY" -eq 0 ]; then
  [ -f "$ROOT/host-dist/index.html" ] || die "host-dist/ پیدا نشد. روی ماشین محلی: bash scripts/build_host.sh و سپس commit/push و روی هاست git pull."
  STAGE="$(mktemp -d "${TMPDIR:-/tmp}/kg-front.XXXXXX")"
  trap 'rm -rf "$STAGE"' EXIT
  cp -a "$ROOT/host-dist/." "$STAGE/"
  find "$STAGE" -type f \( -name '*.html' -o -name '*.js' -o -name '*.css' -o -name '*.xml' -o -name '*.txt' \) -print0 \
    | xargs -0 sed -i "s/__SITE_HOST__/$DOMAIN/g"
  LEFT="$(grep -rl '__SITE_HOST__' "$STAGE" 2>/dev/null | wc -l | tr -d ' ')"
  [ "$LEFT" = "0" ] || die "جانشین دامنه در $LEFT فایل باقی ماند."
  say "دامنه در فایل‌های فرانت جایگزین شد (canonical، sitemap، آدرس API)."
  bash "$ROOT/deploy/deploy_cpanel.sh" --dist "$STAGE" --webroot "$WEBROOT" || die "استقرار فرانت ناموفق بود."
fi

# ── ۲) بک‌اند ──
if [ "$DO_BACK" -eq 1 ] && [ "$CHECK_ONLY" -eq 0 ]; then
  if [ -f "$ENVF" ]; then
    grep -qE '^SHOP_URL=.*github\.io' "$ENVF" && warn "SHOP_URL در backend/.env هنوز GitHub Pages است؛ برای فید ترب و پیامک‌ها بگذارید: SHOP_URL=$SCHEME://$DOMAIN/"
    grep -qE '^ALLOWED_HOSTS=\*?$' "$ENVF" && warn "ALLOWED_HOSTS=* است؛ در تولید بگذارید: ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN"
  fi
  ( cd "$ROOT/backend" && bash deploy/deploy_cpanel.sh ) || die "استقرار بک‌اند ناموفق بود."
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

# ── ۳) بررسی نهایی ──
echo ""; info "بررسی نهایی سایت ..."
BAD=0
probe() {  # probe <مسیر> <توضیح> <متن-مورد-انتظار-در-پاسخ>
  local url="$SCHEME://$DOMAIN$1" out code want="${3:-}"
  out="$(mktemp)"; code="$(curl -sS -L -m 25 -o "$out" -w '%{http_code}' "$url" 2>"$out.err" || echo 000)"
  if [ "${code:0:1}" != "2" ]; then
    BAD=1; warn "$2  [$code]  $url"; head -c 200 "$out" | tr '\n' ' ' >&2; echo >&2; head -c 200 "$out.err" >&2
    grep -q "The requested resource was not found" "$out" 2>/dev/null && warn "   ↑ این صفحهٔ ۴۰۴ خودِ Django است: Passenger این مسیر را گرفته (Application URL پایتون‌اپ باید /food-shop باشد، نه /)"
  elif [ -n "$want" ] && ! grep -qF -- "$want" "$out"; then
    BAD=1; warn "$2  [$code]  $url — پاسخ همان چیزی که انتظار می‌رفت نیست (انتظار: «$want»)"; head -c 160 "$out" | tr '\n' ' ' >&2; echo >&2
  else say "$2  [$code]  $url"; fi
  rm -f "$out" "$out.err"
}
probe "/" "صفحهٔ اصلی فرانت" 'id="app"'
probe "/product/1/" "صفحهٔ محصول (پیش‌رندر)" 'application/ld+json'
probe "/sitemap.xml" "sitemap"
probe "/food-shop/api/v1/health" "سلامت API" '"ok"'
probe "/food-shop/api/v1/products" "محصولات API" '"name"'
probe "/food-shop/api/v1/torob/products?page=1" "فید ترب" '"products"'

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
  curl -sS -I -m 20 "$SCHEME://$DOMAIN/food-shop/api/v1/health" 2>&1 | head -12 | sed 's/^/   /'
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
