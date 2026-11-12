/* ---------- دادهٔ سئوی یک محصول (مشترک بین صفحهٔ محصول و پیش‌رندر زمان بیلد) ---------- */
import { priceOf, weightLabel } from './site';
import { catOf } from './catalog';

export const defaultWeight = p => p.weights[Math.min(1, p.weights.length - 1)];

/* تصویر محلی (/food-shop/img/x.jpg) → آدرس مطلق؛ آدرس‌های بیرونی دست‌نخورده */
const absImg = (u, siteUrl) => (u && u.startsWith('/')) ? siteUrl.replace(/^(https?:\/\/[^/]+).*$/, '$1') + u : u;

export function productSeo(p, siteUrl) {
  const w = defaultWeight(p);
  const price = priceOf(p, w);                                    // تومان
  const base = p.disc ? Math.round(p.price * w / 1000) : 0;      // قیمت قبل از تخفیف
  const inStock = p.stock > 0;
  const catName = catOf(p.cat)?.name || '';
  const desc = (p.desc && p.desc.trim())
    ? p.desc.trim()
    : `خرید آنلاین ${p.name}${catName ? ' از دستهٔ ' + catName : ''} با قیمت روز، تضمین تازگی و ارسال سریع از فروشگاه خانم گل`;
  const description = desc.length > 158 ? desc.slice(0, 155).trimEnd() + '…' : desc;
  const path = '/product/' + p.id;
  const url = siteUrl + path + '/';
  return {
    title: p.name,
    description,
    path,
    ogType: 'product',
    image: absImg(p.img, siteUrl),
    product: { price, oldPrice: base > price ? base : 0, inStock },
    meta: { w, wLabel: weightLabel(w), catName },
    jsonld: [{
      '@context': 'https://schema.org', '@type': 'Product',
      name: p.name, image: [absImg(p.img, siteUrl)], description: desc,
      sku: String(p.id), category: catName,
      brand: { '@type': 'Brand', name: 'خانم گل' },
      offers: {
        '@type': 'Offer', url,
        priceCurrency: 'IRR', price: price * 10,                  // schema.org: ریال
        itemCondition: 'https://schema.org/NewCondition',
        availability: inStock ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
        seller: { '@type': 'Organization', name: 'فروشگاه خانم گل' },
      },
    }, {
      '@context': 'https://schema.org', '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'خانه', item: siteUrl + '/' },
        { '@type': 'ListItem', position: 2, name: 'فروشگاه', item: siteUrl + '/products/' },
        { '@type': 'ListItem', position: 3, name: p.name, item: url },
      ],
    }],
  };
}
