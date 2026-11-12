#!/usr/bin/env bash
# اجرای کامل همهٔ تست‌ها از صفر (دیتابیس و سرور تازه برای هر مجموعه؛ سقف نرخ ورود ۶۰/ساعت بین مجموعه‌ها نشت نکند)
# پیش‌نیاز: python3 با پکیج‌های backend/requirements.txt ، Node و Playwright. اجرا از ریشهٔ ریپو:  bash scripts/run_all_tests.sh
set -uo pipefail
cd "$(dirname "$0")/.."
FAIL=0
fresh_backend() {
  pkill -f "manage.py runserver" 2>/dev/null; sleep 1
  ( cd backend && rm -rf db.sqlite3 logs && python manage.py migrate >/dev/null 2>&1 && python manage.py seed_shop >/dev/null 2>&1 \
    && (nohup python manage.py runserver 8787 >/dev/null 2>&1 &) ); sleep 3
}
run() { echo "── $1"; shift; "$@" 2>&1 | grep -E "✗|نتیجه|بدون خطا" ; [ "${PIPESTATUS[0]}" -eq 0 ] || FAIL=1; }

fresh_backend; run "API بک‌اند" python3 scripts/test_backend_api.py
fresh_backend; run "امنیت بک‌اند" python3 scripts/test_backend_security.py
run "locale ASCII (رگرسیون ۵۰۰ هاست)" python3 scripts/test_ascii_locale.py

( cd app && npm run build >/dev/null 2>&1 && (nohup npx vite preview --port 4173 >/dev/null 2>&1 &) ); sleep 3
run "سبد خرید (دمو بدون سرور)" node scripts/test_cart_ui.js
run "سئو و پیش‌رندر" node scripts/test_seo.js
pkill -f "vite preview" 2>/dev/null

fresh_backend
( cd app && VITE_BASE=/ VITE_API_ENABLED=true VITE_API_BASE=http://127.0.0.1:8787/api/v1 npx vite build --outDir /tmp/ui-dist >/dev/null 2>&1 \
  && (VITE_BASE=/ nohup npx vite preview --outDir /tmp/ui-dist --port 4174 >/dev/null 2>&1 &) ); sleep 3
run "رابط + مدیریت (با بک‌اند واقعی)" node scripts/test_ui_admin.js
echo "خطاهای ۵xx ثبت‌شده در لاگ سرور: $(cat backend/logs/django-error.log 2>/dev/null | wc -l)"
pkill -f "vite preview" 2>/dev/null; pkill -f "manage.py runserver" 2>/dev/null
exit $FAIL
