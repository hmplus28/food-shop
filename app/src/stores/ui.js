/* ---------- وضعیت سراسری رابط (تم، کشوها، مودال‌ها، اعلان‌ها) ---------- */
import { reactive } from 'vue';
import { LS } from '../data/site';
import { siteSettingsApi, adminSettingsApi, luckyStatusApi } from '../services/api';

export const ui = reactive({
  cartOpen: false,
  navOpen: false,
  modal: null,            // 'lucky' | 'fav' | null
  toasts: [],
});

let tid = 0;
export function toast(msg, type = 'ok', ms = 3400) {
  const id = ++tid;
  ui.toasts.push({ id, msg, type });
  while (ui.toasts.length >= 3) ui.toasts.shift(); /* حداکثر ۳ اعلان همزمان */
  setTimeout(() => {
    const i = ui.toasts.findIndex(t => t.id === id);
    if (i > -1) ui.toasts.splice(i, 1);
  }, ms);
}

export const openCart = () => { ui.cartOpen = true; };
export const closeCart = () => { ui.cartOpen = false; };
export const openNav = () => { ui.navOpen = true; };
export const closeNav = () => { ui.navOpen = false; };
export const openModal = m => { ui.modal = m; };
export const closeModal = () => { ui.modal = null; };
export const closeAll = () => { ui.cartOpen = false; ui.navOpen = false; ui.modal = null; };

/* ---------- ظاهر سراسری سایت (تم + رنگ برند) ----------
   مقدار اصلی روی سرور است و برای همهٔ بازدیدکنندگان یکسان؛ فقط مدیر (سوپریوزر) می‌تواند عوضش کند.
   نسخهٔ آخرین مقدار در LocalStorage فقط برای جلوگیری از پرش رنگ در بارگذاری بعدی نگه داشته می‌شود. */
const BRAND_VARS = ['--brand', '--brand-600', '--brand-700', '--brand-800'];
LS.del('theme'); LS.del('brandVer'); try { localStorage.removeItem('asalat_brandtune'); } catch (e) {}   // انتخاب‌های قدیمی هر بازدیدکننده

export const look = reactive({ theme: 'default', tune: null, ...LS.get('look', {}) });

export function applyLook(l = look) {
  const root = document.documentElement;
  if (l.theme && l.theme !== 'default') root.dataset.theme = l.theme; else delete root.dataset.theme;
  BRAND_VARS.forEach((k, i) => {
    if (Array.isArray(l.tune) && /^#[0-9a-f]{6}$/i.test(l.tune[i] || '')) root.style.setProperty(k, l.tune[i]);
    else root.style.removeProperty(k);
  });
}

/* دریافت ظاهر فعلی از سرور و اعمال برای همه؛ ناموفق → همان نسخهٔ کش‌شده */
export async function loadLook() {
  const r = await siteSettingsApi();
  if (!r) return false;
  look.theme = r.theme; look.tune = r.tune;
  LS.set('look', { theme: r.theme, tune: r.tune });
  applyLook();
  return true;
}

/* ذخیرهٔ ظاهر برای کل سایت (فقط مدیر؛ سرور هم دسترسی را چک می‌کند) */
export async function saveLook(theme, tune) {
  const r = await adminSettingsApi({ theme, tune });
  if (!r.ok) { toast(r.msg || 'ذخیره نشد', 'err'); return false; }
  look.theme = r.theme; look.tune = r.tune;
  LS.set('look', { theme: r.theme, tune: r.tune });
  applyLook();
  toast('ظاهر سایت برای همهٔ بازدیدکنندگان ذخیره شد ✅', 'gold');
  return true;
}
applyLook();

/* ---------- کارت شانس: وضعیت حساب (سرور تعیین می‌کند) ---------- */
export const lucky = reactive({ loaded: false, enabled: true, loggedIn: false, canSpin: false, nextAt: null });
export async function refreshLucky() {
  const r = await luckyStatusApi();
  if (!r.ok) return false;
  Object.assign(lucky, { loaded: true, enabled: !!r.enabled, loggedIn: !!r.loggedIn, canSpin: !!r.canSpin, nextAt: r.nextAt || null });
  return true;
}
