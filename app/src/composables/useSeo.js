/* ---------- سئو: عنوان، توضیح متا، کنونیکال، اوپن‌گراف و JSON-LD هر صفحه ---------- */
const SITE = 'https://hmplus28.github.io/food-shop';
const BASE = '/food-shop/';

function setMeta(attr, key, content) {
  if (content == null) return;
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) { el = document.createElement('meta'); el.setAttribute(attr, key); document.head.appendChild(el); }
  el.setAttribute('content', content);
}

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

export function useSeo({ title, description, path, ogType = 'website', jsonld } = {}) {
  const full = title ? `${title} | خانم گل` : 'خانم گل | فروشگاه اینترنتی خشکبار، آجیل و محصولات طبیعی';
  document.title = full;
  if (description) setMeta('name', 'description', description);
  setMeta('property', 'og:title', full);
  if (description) setMeta('property', 'og:description', description);
  setMeta('property', 'og:type', ogType);
  setMeta('property', 'og:site_name', 'فروشگاه خانم گل');
  setMeta('property', 'og:locale', 'fa_IR');
  const url = SITE + (path || BASE);
  setMeta('property', 'og:url', url);
  let link = document.head.querySelector('link[rel="canonical"]');
  if (!link) { link = document.createElement('link'); link.rel = 'canonical'; document.head.appendChild(link); }
  link.href = url;
  setJsonLd('seo-jsonld', jsonld || null);
}

export const SITE_URL = SITE;
