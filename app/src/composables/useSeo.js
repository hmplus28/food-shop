/* ---------- سئو: عنوان، توضیح متا، کنونیکال، اوپن‌گراف، توییتر و JSON-LD هر صفحه ---------- */
/* آدرس کامل ریشهٔ سایت (بدون اسلش آخر). روی دامنهٔ واقعی هنگام بیلد تنظیم شود:
     VITE_SITE_URL=https://shop.example.ir            (دامنه در ریشه، VITE_BASE=/)
     VITE_SITE_URL=https://example.ir/food-shop       (زیرمسیر، VITE_BASE=/food-shop/)
   پیش‌فرض: GitHub Pages */
const raw = v => (typeof v === 'string' ? v.trim() : '');
const SITE = (raw(import.meta.env.VITE_SITE_URL) || 'https://hmplus28.github.io/food-shop').replace(/\/+$/, '');
const ORIGIN = SITE.replace(/^(https?:\/\/[^/]+).*$/, '$1');
const absUrl = u => (u && u.startsWith('/')) ? ORIGIN + u : u;     // تصویر محلی → آدرس مطلق برای OG/JSON-LD
const DEFAULT_IMG = SITE + '/img/66fd0cba7ee8.jpg';
const DEFAULT_TITLE = 'خانم گل | فروشگاه اینترنتی خشکبار، آجیل و محصولات طبیعی';

/* صفحاتی که نباید در نتایج گوگل بیایند */
const PRIVATE = ['/cart', '/checkout', '/account', '/admin', '/auth', '/404'];

function setMeta(attr, key, content) {
  if (content == null) return;
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) { el = document.createElement('meta'); el.setAttribute(attr, key); document.head.appendChild(el); }
  el.setAttribute('content', content);
}
function removeMeta(attr, key) { document.head.querySelector(`meta[${attr}="${key}"]`)?.remove(); }

function setJsonLd(id, data) {
  let el = document.getElementById(id);
  if (!data) { if (el) el.remove(); return; }
  if (!el) {
    el = document.createElement('script');
    el.type = 'application/ld+json';
    el.id = id;
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(data);
}

/* آدرس کنونیکال: صفحات پیش‌رندرشده با اسلش پایانی سرو می‌شوند */
export function canonicalUrl(path) {
  const p = (path && path !== '/') ? path.replace(/\/+$/, '') + '/' : '/';
  return SITE + p;
}

export function useSeo({ title, description, path, ogType = 'website', image, jsonld, product } = {}) {
  const full = title ? `${title} | خانم گل` : DEFAULT_TITLE;
  document.title = full;
  if (description) setMeta('name', 'description', description);
  setMeta('property', 'og:title', full);
  if (description) setMeta('property', 'og:description', description);
  setMeta('property', 'og:type', ogType);
  setMeta('property', 'og:site_name', 'فروشگاه خانم گل');
  setMeta('property', 'og:locale', 'fa_IR');
  const url = canonicalUrl(path || '/');
  setMeta('property', 'og:url', url);
  setMeta('property', 'og:image', absUrl(image) || DEFAULT_IMG);
  setMeta('name', 'twitter:card', 'summary_large_image');
  setMeta('name', 'twitter:title', full);
  if (description) setMeta('name', 'twitter:description', description);
  setMeta('name', 'twitter:image', absUrl(image) || DEFAULT_IMG);

  const isPrivate = PRIVATE.some(p => (path || '').startsWith(p));
  setMeta('name', 'robots', isPrivate ? 'noindex, nofollow' : 'index, follow, max-image-preview:large');

  let link = document.head.querySelector('link[rel="canonical"]');
  if (!link) { link = document.createElement('link'); link.rel = 'canonical'; document.head.appendChild(link); }
  link.href = url;

  /* متاتگ‌های محصول (برای ترب و اشتراک‌گذاری): قیمت به تومان */
  ['product:price:amount', 'product:price:currency', 'product:availability', 'product:original_price:amount'].forEach(k => removeMeta('property', k));
  if (product) {
    setMeta('property', 'product:price:amount', String(product.price));
    setMeta('property', 'product:price:currency', 'IRT');
    setMeta('property', 'product:availability', product.inStock ? 'instock' : 'out of stock');
    if (product.oldPrice) setMeta('property', 'product:original_price:amount', String(product.oldPrice));
  }
  setJsonLd('seo-jsonld', jsonld || null);
}

export const SITE_URL = SITE;
