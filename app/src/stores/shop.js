/* ---------- محتوای سراسری سایت (از سرور؛ مدیر در پنل ویرایش می‌کند) ----------
   اطلاعات تماس و متن‌ها، روش‌ها و هزینهٔ ارسال، فهرست صفحات راهنما، تنظیم کارت شانس.
   مقدار پیش‌فرض/کش‌شده از اولین لحظه نمایش داده می‌شود و پس از رسیدن پاسخ سرور جایگزین می‌شود. */
import { reactive, computed } from 'vue';
import { LS, SHIP_OPTIONS, FREE_SHIP } from '../data/site';
import { siteApi } from '../services/api';

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

const cached = LS.get('shopCache', {});

export const shop = reactive({
  info: { ...DEFAULT_INFO, ...(cached.info || {}) },
  shipping: cached.shipping || { methods: SHIP_OPTIONS.map(o => ({ ...o })), freeFrom: FREE_SHIP, freeEnabled: true },
  pages: cached.pages || [],
  lucky: cached.lucky || { enabled: true, cooldownHours: 24 },
  loaded: false,
});

export async function loadShop() {
  const r = await siteApi();
  if (!r.ok) return false;
  shop.info = { ...DEFAULT_INFO, ...(r.info || {}) };
  if (r.shipping && Array.isArray(r.shipping.methods) && r.shipping.methods.length) shop.shipping = r.shipping;
  shop.pages = Array.isArray(r.pages) ? r.pages : [];
  if (r.lucky) shop.lucky = r.lucky;
  shop.loaded = true;
  LS.set('shopCache', { info: shop.info, shipping: shop.shipping, pages: shop.pages, lucky: shop.lucky });
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
