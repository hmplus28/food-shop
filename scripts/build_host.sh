#!/usr/bin/env bash
# ساخت نسخهٔ آمادهٔ هاست (روی ماشین محلی/CI با Node ≥18) → پوشهٔ host-dist/
#
# چون روی هاست Node/بیلد نیست، این نسخه یک‌بار با «دامنهٔ جانشین» ساخته و commit می‌شود؛
# deploy.sh روی هاست دامنهٔ واقعی را با sed جایگزین می‌کند (canonical، sitemap، آدرس API).
# جانشین‌ها: __SITE_HOST__ (دامنهٔ فرانت) و __API_BASE__ (آدرس کامل API، مثلاً https://api.دامنه/api/v1).
#
# اجرا:  bash scripts/build_host.sh  &&  git add host-dist && git commit && git push
set -euo pipefail
cd "$(dirname "$0")/../app"
npm ci --no-audit --no-fund
VITE_BASE=/ \
VITE_SITE_URL=https://__SITE_HOST__ \
VITE_API_ENABLED=true \
VITE_API_BASE=__API_BASE__ \
  npm run build
rm -rf ../host-dist
cp -r dist ../host-dist
echo "✔ host-dist/ ساخته شد ($(find ../host-dist -type f | wc -l) فایل). حالا commit و push کنید."
