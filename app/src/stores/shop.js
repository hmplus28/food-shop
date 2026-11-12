/* ---------- محتوای سراسری سایت (از سرور؛ مدیر در پنل ویرایش می‌کند) ----------
   اطلاعات تماس و متن‌ها، روش‌ها و هزینهٔ ارسال، فهرست صفحات راهنما، تنظیم کارت شانس.
   مقدار پیش‌فرض/کش‌شده از اولین لحظه نمایش داده می‌شود و پس از رسیدن پاسخ سرور جایگزین می‌شود. */
import { reactive, computed } from 'vue';
import { LS, SHIP_OPTIONS, FREE_SHIP } from '../data/site';
import { siteApi, localImg } from '../services/api';
import { PACKS, TRUST, IMG, virtualFrom, setVirtualProducts } from '../data/catalog';

export const DEFAULT_INFO = {
  shopName: 'فروشگاه خانم گل', phone: '۰۲۱-۹۱۰۹۲۰۰۰', phoneTel: '02191092000', whatsapp: '989120000000',
  email: 'info@asalat-shop.ir', address: 'تهران، خیابان ولی‌عصر، مجتمع تجاری خانم گل، طبقه ۲',
  hours: 'شنبه تا پنجشنبه ۹ تا ۲۱ | جمعه‌ها ۱۰ تا ۱۸', instagram: '', telegram: '',
  topbarMsg: 'پاسخگویی شبانه‌روزی، همیشه در کنار شما',
  footerAbout: 'خانم گل، فروشگاه اینترنتی خشکبار و محصولات طبیعی؛ بیش از سه دهه است که تازه‌ترین آجیل، خشکبار، زعفران و دمنوش‌ها را مستقیم از باغ‌داران ایرانی تهیه و با بسته‌بندی بهداشتی به سراسر ایران می‌رساند.',
  heroTag: 'تازه، سالم و باکیفیت', heroTitle: 'طعم اصالت، کیفیت در', heroTitleEm: 'هر دانه',
  heroText: 'انتخابی تازه و باکیفیت از بهترین آجیل‌ها، خشکبار و محصولات طبیعی؛ از دل طبیعت تا سفره شما.',
  consultText: 'نمی‌دانید برای مهمانی، هدیه یا رژیم غذایی‌تان چه محصولی مناسب است؟ همین حالا تماس بگیرید تا رایگان راهنمایی‌تان کنیم.',
  returnsNote: 'مرجوعی کاملاً رایگان تا ۷ روز',
};

/* پیش‌فرض صفحهٔ اصلی (همان محتوای قبلی)؛ پس از رسیدن پاسخ سرور جایگزین می‌شود */
export const DEFAULT_HOME = {
  order: ['packs', 'cats', 'amazing', 'best', 'trust', 'consult', 'why'],
  packs: { on: true, title: 'پک‌های', titleEm: 'تخفیفی', titleTail: 'ویژه امروز', sub: 'فرصت محدود؛ فقط تا پایان شمارش معکوس باقی است!' },
  cats: { on: true, title: 'دسته‌بندی‌های', titleEm: 'محبوب', titleTail: '', sub: 'از میان طعم‌های اصیل ایرانی انتخاب کنید' },
  amazing: { on: true, title: 'پیشنهاد شگفت‌انگیز', badge: 'تا ٪۳۰', text: 'تخفیف‌های باورنکردنی روی محصولات منتخب؛ فرصت باقی‌مانده:', countdown: true, limit: 6 },
  best: { on: true, title: 'پرفروش‌ترین', titleEm: 'محصولات', titleTail: '', sub: 'انتخاب هزاران مشتری در سراسر ایران', limit: 8 },
  trust: { on: true, title: 'خرید', titleEm: 'اطمینان', titleTail: '', sub: 'هر روز یک کالای منتخب با قیمت ویژه؛ چون به نام ما اعتماد دارید، با خیال راحت بخرید', why: 'اعتماد شما بزرگ‌ترین سرمایه ماست! هر روز یک کالای منتخب با قیمت ویژه به سبد شما اضافه می‌کنیم.', kicker: 'کالای منتخب خانم گل' },
  consult: { on: true, title: 'مشاوره خرید', titleEm: '', titleTail: 'و پیگیری سفارش', sub: 'کارشناسان خانم گل پاسخگوی انتخاب‌های شما هستند' },
  why: { on: true, title: 'چرا', titleEm: 'خانم گل', titleTail: '؟', sub: 'چهار دلیل برای اعتماد هزاران خانواده ایرانی', items: [
    { icon: 'i-leaf', title: 'تضمین تازگی و کیفیت', text: 'محصولات روزانه از باغ‌ها دریافت و بو داده می‌شوند؛ اگر راضی نبودید، مرجوعی رایگان.' },
    { icon: 'i-box', title: 'بسته‌بندی بهداشتی', text: 'بسته‌بندی وکیوم و استاندارد مواد غذایی با درج تاریخ تولید و انقضا روی هر بسته.' },
    { icon: 'i-truck', title: 'ارسال سریع سراسری', text: 'پیک فوری در تهران، پست پیشتاز و تیپاکس به تمام نقاط ایران.' },
    { icon: 'i-scale', title: 'قیمت منصفانه و شفاف', text: 'خرید مستقیم از باغ‌دار بدون واسطه؛ قیمت‌ها همیشه شفاف و بدون هزینه پنهان.' },
  ] },
};
const DEFAULT_BANNERS = [{ id: 0, image: IMG + '62b15d793f24.png', tag: 'تازه، سالم و باکیفیت', title: 'طعم اصالت، کیفیت در', titleEm: 'هر دانه',
  text: 'انتخابی تازه و باکیفیت از بهترین آجیل‌ها، خشکبار و محصولات طبیعی؛ از دل طبیعت تا سفره شما.',
  cta1: { label: 'مشاهده محصولات', link: '/products' }, cta2: { label: 'مشاهده پیشنهادهای ویژه', link: '/#amazing' } }];

const cached = LS.get('shopCache', {});

export const shop = reactive({
  info: { ...DEFAULT_INFO, ...(cached.info || {}) },
  shipping: cached.shipping || { methods: SHIP_OPTIONS.map(o => ({ ...o })), freeFrom: FREE_SHIP, freeEnabled: true },
  pages: cached.pages || [],
  lucky: cached.lucky || { enabled: true, cooldownHours: 24 },
  home: { ...DEFAULT_HOME, ...(cached.home || {}) },
  banners: cached.banners || DEFAULT_BANNERS,
  packs: cached.packs || PACKS.map((p, i) => ({ id: i, pid: p.pid, name: p.name, sub: p.sub, image: '', old: p.old, now: p.now, endsAt: Date.now() + p.hours * 3600000, stock: 99, w: p.w })),
  trust: cached.trust || TRUST.map(t => ({ id: t.day, day: t.day, name: t.name, image: t.img, old: t.old, price: t.price, pid: 90 + TRUST.indexOf(t), stock: 8 })),
  loaded: false,
});

export async function loadShop() {
  const r = await siteApi();
  if (!r.ok) return false;
  shop.info = { ...DEFAULT_INFO, ...(r.info || {}) };
  if (r.shipping && Array.isArray(r.shipping.methods) && r.shipping.methods.length) shop.shipping = r.shipping;
  shop.pages = Array.isArray(r.pages) ? r.pages : [];
  if (r.lucky) shop.lucky = r.lucky;
  if (r.home) shop.home = { ...DEFAULT_HOME, ...r.home };
  if (Array.isArray(r.banners)) shop.banners = r.banners;
  if (Array.isArray(r.packs)) shop.packs = r.packs;
  if (Array.isArray(r.trust)) shop.trust = r.trust;
  shop.loaded = true;
  setVirtualProducts(virtualFrom(shop.packs, shop.trust, localImg));   // قابل‌خرید شدن پک/اعتماد در سبد
  LS.set('shopCache', { info: shop.info, shipping: shop.shipping, pages: shop.pages, lucky: shop.lucky, home: shop.home, banners: shop.banners, packs: shop.packs, trust: shop.trust });
  return true;
}

/* ---- ارسال ---- */
export const shipMethods = computed(() => shop.shipping.methods);
export const freeFrom = computed(() => Number(shop.shipping.freeFrom) || 0);
export const freeShipOn = computed(() => !!shop.shipping.freeEnabled && freeFrom.value > 0);
export const defaultShipCost = computed(() => (shipMethods.value[0] ? Number(shipMethods.value[0].cost) : 0));

/* ---- پیوندها ---- */
export const waLink = computed(() => (shop.info.whatsapp ? 'https://wa.me/' + shop.info.whatsapp.replace(/\D/g, '') : ''));
export const telLink = computed(() => 'tel:' + (shop.info.phoneTel || '').replace(/[^\d+]/g, ''));
export const guidePages = computed(() => shop.pages.filter(p => p.group === 'guide'));
export const aboutPages = computed(() => shop.pages.filter(p => p.group !== 'guide'));
