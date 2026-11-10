/* ---------- وضعیت سراسری رابط (تم، کشوها، مودال‌ها، اعلان‌ها) ---------- */
import { reactive } from 'vue';
import { LS } from '../data/site';
import { THEMES } from '../data/catalog';

export const ui = reactive({
  cartOpen: false,
  navOpen: false,
  modal: null,            // 'lucky' | 'fav' | null
  toasts: [],
  theme: LS.get('theme', 'default'),
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

/* مهاجرت یک‌بارهٔ هویت رنگی برند: تم قدیمی مرورگر یک بار پاک می‌شود */
if (LS.get('brandVer', 0) < 2) {
  LS.set('theme', 'default');
  LS.set('brandVer', 2);
  ui.theme = 'default';
}

export function applyTheme() {
  document.documentElement.dataset.theme = ui.theme === 'default' ? '' : ui.theme;
}
export function setTheme(id) {
  ui.theme = id;
  LS.set('theme', id);
  applyTheme();
  toast('تم رنگی به «' + THEMES.find(t => t.id === id).name + '» تغییر کرد 🎨', 'gold');
}
applyTheme();
