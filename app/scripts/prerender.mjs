/* پیش‌رندر ایستای سئو — بعد از `vite build` اجرا می‌شود (npm run build)
 *
 * برای هر صفحهٔ قابل‌ایندکس یک فایل dist/<مسیر>/index.html با کد ۲۰۰ و
 * عنوان/توضیح/کنونیکال/OG/JSON-LD و محتوای متنی واقعی می‌سازد تا گوگل و
 * ترب (که جاوااسکریپت اجرا نمی‌کنند) صفحه را کامل ببینند؛ سپس sitemap.xml و
 * robots.txt را از روی کاتالوگ می‌سازد. وقتی Vue بالا بیاید محتوا را جایگزین می‌کند.
 *
 * تنظیمات (متغیر محیطی هنگام بیلد):
 *   VITE_SITE_URL  آدرس کامل ریشهٔ سایت بدون اسلش آخر
 *                  (پیش‌فرض https://hmplus28.github.io/food-shop)
 *   VITE_BASE      مسیر پایه (پیش‌فرض /food-shop/)
 */
import { createServer, loadEnv } from 'vite';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIST = path.join(ROOT, 'dist');
const LEGACY = 'https://hmplus28.github.io/food-shop';
const FILE_ENV = loadEnv('production', ROOT, 'VITE_');          // app/.env هم خوانده می‌شود
const envOf = k => process.env[k] || FILE_ENV[k] || '';
const SITE = (envOf('VITE_SITE_URL') || LEGACY).trim().replace(/\/+$/, '');
const BASE = process.env.VITE_BASE || '/food-shop/';       // مثل vite.config.js فقط از متغیر شل (deploy_cpanel.sh آن را export می‌کند)
const TODAY = new Date().toISOString().slice(0, 10);

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const money = n => Number(n).toLocaleString('fa-IR');
const url = p => SITE + (p === '/' ? '/' : p.replace(/\/+$/, '') + '/');
const ld = o => `<script type="application/ld+json" id="seo-jsonld">${JSON.stringify(o).replace(/</g, '\\u003c')}</script>`;   // همان id که useSeo جایگزین می‌کند

if (!fs.existsSync(path.join(DIST, 'index.html'))) { console.error('dist/index.html پیدا نشد؛ اول vite build'); process.exit(1); }
const template = fs.readFileSync(path.join(DIST, 'index.html'), 'utf8');

const server = await createServer({ root: ROOT, server: { middlewareMode: true }, appType: 'custom', logLevel: 'silent', optimizeDeps: { noDiscovery: true, include: [] } });
let products, CATS, productSeo, priceOf, weightLabel;
try {
  ({ products, CATS } = await server.ssrLoadModule('/src/data/catalog.js'));
  ({ productSeo } = await server.ssrLoadModule('/src/data/seoProduct.js'));
  ({ priceOf, weightLabel } = await server.ssrLoadModule('/src/data/site.js'));
} finally { await server.close(); }
const list = products.filter(p => !p.hide);

/* ---------- ساخت یک صفحه از روی قالب ---------- */
function render({ route, title, description, ogType = 'website', image, robots = 'index, follow, max-image-preview:large', product, jsonld = [], body }) {
  const canonical = url(route);
  const full = title ? `${title} | خانم گل` : 'خانم گل | فروشگاه اینترنتی خشکبار، آجیل و محصولات طبیعی';
  const img = image || list[0]?.img;
  const meta = [
    `<link rel="canonical" href="${esc(canonical)}">`,
    `<meta property="og:title" content="${esc(full)}">`,
    `<meta property="og:description" content="${esc(description)}">`,
    `<meta property="og:type" content="${ogType}">`,
    `<meta property="og:site_name" content="فروشگاه خانم گل">`,
    `<meta property="og:locale" content="fa_IR">`,
    `<meta property="og:url" content="${esc(canonical)}">`,
    `<meta property="og:image" content="${esc(img)}">`,
    `<meta name="twitter:card" content="summary_large_image">`,
    `<meta name="twitter:title" content="${esc(full)}">`,
    `<meta name="twitter:description" content="${esc(description)}">`,
    `<meta name="twitter:image" content="${esc(img)}">`,
  ];
  if (product) {
    meta.push(`<meta property="product:price:amount" content="${product.price}">`,
      `<meta property="product:price:currency" content="IRT">`,
      `<meta property="product:availability" content="${product.inStock ? 'instock' : 'out of stock'}">`);
    if (product.oldPrice) meta.push(`<meta property="product:original_price:amount" content="${product.oldPrice}">`);
  }
  if (jsonld.length) meta.push(ld(jsonld.length === 1 ? jsonld[0] : jsonld));

  let html = template.split(LEGACY).join(SITE);                    // JSON-LD ثابت قالب
  html = html.replace(/<title>[\s\S]*?<\/title>/, `<title>${esc(full)}</title>`);
  html = html.replace(/<meta name="description"[^>]*>/, `<meta name="description" content="${esc(description)}">`);
  html = html.replace(/<meta name="robots"[^>]*>/, `<meta name="robots" content="${robots}">`);
  html = html.replace('</head>', `  ${meta.join('\n  ')}\n</head>`);
  html = html.replace('<div id="app"></div>', `<div id="app">${body}</div>`);
  return html;
}

const nav = `<nav><a href="${BASE}">خانه</a> | <a href="${BASE}products/">فروشگاه</a> | <a href="${BASE}track/">پیگیری سفارش</a></nav>`;
const productLi = p => `<li><a href="${BASE}product/${p.id}/">${esc(p.name)}</a> — ${money(priceOf(p, p.weights[Math.min(1, p.weights.length - 1)]))} تومان</li>`;

function write(route, html) {
  const dir = path.join(DIST, route === '/' ? '' : route);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'index.html'), html);
}

const pages = [];   // برای sitemap

/* صفحهٔ اصلی */
write('/', render({
  route: '/', title: null,
  description: 'خرید آنلاین بهترین آجیل، پسته، بادام، گردو، خرما و زعفران با تضمین تازگی، ارسال سریع سراسری و مرجوعی رایگان از فروشگاه خانم گل',
  jsonld: [],
  body: `${nav}<h1>خانم گل | فروشگاه اینترنتی خشکبار و آجیل</h1><p>خرید آنلاین آجیل، پسته، بادام، گردو، خرما و زعفران با تضمین تازگی و ارسال سریع سراسری.</p>
<h2>دسته‌بندی‌ها</h2><ul>${CATS.map(c => `<li><a href="${BASE}products/?cat=${c.id}">${esc(c.name)}</a></li>`).join('')}</ul>
<h2>محصولات</h2><ul>${list.map(productLi).join('')}</ul>`,
}));
pages.push({ route: '/', pr: '1.0', cf: 'daily' });

/* فروشگاه */
write('/products', render({
  route: '/products', title: 'فروشگاه محصولات',
  description: 'لیست کامل محصولات خانم گل؛ آجیل، خشکبار، زعفران و دمنوش با تضمین تازگی و مرجوعی رایگان',
  jsonld: [{
    '@context': 'https://schema.org', '@type': 'ItemList',
    itemListElement: list.map((p, i) => ({ '@type': 'ListItem', position: i + 1, url: url('/product/' + p.id), name: p.name })),
  }],
  body: `${nav}<h1>فروشگاه محصولات خانم گل</h1><ul>${list.map(productLi).join('')}</ul>`,
}));
pages.push({ route: '/products', pr: '0.9', cf: 'daily' });

/* پیگیری سفارش */
write('/track', render({
  route: '/track', title: 'پیگیری سفارش',
  description: 'پیگیری لحظه‌ای وضعیت سفارش‌های فروشگاه خانم گل با کد سفارش',
  body: `${nav}<h1>پیگیری سفارش</h1><p>کد سفارش خود را وارد کنید تا وضعیت آن را ببینید.</p>`,
}));
pages.push({ route: '/track', pr: '0.3', cf: 'monthly' });

/* محصولات */
for (const p of list) {
  const s = productSeo(p, SITE);
  const route = '/product/' + p.id;
  write(route, render({
    route, title: s.title, description: s.description, ogType: 'product', image: s.image, product: s.product, jsonld: s.jsonld,
    body: `${nav}<article><h1>${esc(p.name)}</h1><img src="${esc(p.img)}" alt="${esc(p.name)}" width="400" height="400">
<p>دسته: ${esc(s.meta.catName)} | وزن: ${esc(s.meta.wLabel)}</p>
<p>قیمت: ${money(s.product.price)} تومان${s.product.oldPrice ? ` (قبل از تخفیف ${money(s.product.oldPrice)} تومان)` : ''} — ${s.product.inStock ? 'موجود' : 'ناموجود'}</p>
<p>${esc(s.description)}</p></article>`,
  }));
  pages.push({ route, pr: '0.8', cf: 'weekly', img: p.img, name: p.name });
}

/* ---------- sitemap.xml ---------- */
const sm = ['<?xml version="1.0" encoding="UTF-8"?>',
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
  ...pages.map(pg => `  <url><loc>${esc(url(pg.route))}</loc><lastmod>${TODAY}</lastmod><changefreq>${pg.cf}</changefreq><priority>${pg.pr}</priority>` +
    (pg.img ? `<image:image><image:loc>${esc(pg.img)}</image:loc><image:title>${esc(pg.name)}</image:title></image:image>` : '') + '</url>'),
  '</urlset>', ''].join('\n');
fs.writeFileSync(path.join(DIST, 'sitemap.xml'), sm);

/* ---------- robots.txt ---------- */
const sitePath = new URL(SITE).pathname.replace(/\/+$/, '');
fs.writeFileSync(path.join(DIST, 'robots.txt'), [
  'User-agent: *', 'Allow: /',
  ...['cart', 'checkout', 'account', 'admin', 'auth', 'dj-admin'].map(x => `Disallow: ${sitePath}/${x}`),
  '', `Sitemap: ${SITE}/sitemap.xml`, ''].join('\n'));

/* ---------- 404.html: مسیر بازگشت با مسیر پایهٔ واقعی ---------- */
const nf = path.join(DIST, '404.html');
if (fs.existsSync(nf)) fs.writeFileSync(nf, fs.readFileSync(nf, 'utf8').split('/food-shop/').join(BASE));

console.log(`[prerender] ${pages.length} صفحه، sitemap.xml و robots.txt ساخته شد (SITE=${SITE})`);
