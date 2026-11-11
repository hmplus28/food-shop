/* ---------- سبد خرید ---------- */
import { reactive, computed } from 'vue';
import { LS, priceOf, money, toFa, FREE_SHIP } from '../data/site';
import { prod, COUPONS } from '../data/catalog';
import { toast } from './ui';

/* فقط ردیف‌های سالم: محصول موجود، وزن مجاز و تعداد ۱ تا ۲۰ */
const sanitize = list => (Array.isArray(list) ? list : []).filter(c =>
  c && typeof c === 'object' && prod(c.pid) && prod(c.pid).weights.includes(c.w) &&
  Number.isFinite(c.qty) && c.qty >= 1).map(c => ({ pid: Number(c.pid), w: c.w, qty: Math.min(20, Math.floor(c.qty)) }));

export const cart = reactive({
  items: sanitize(LS.get('cart', [])),      // [{pid, w, qty}]
  coupon: null,
});

const save = () => LS.set('cart', cart.items);

/* بعد از همگام‌سازی کاتالوگ با بک‌اند، کالاهای حذف/مخفی‌شده را از سبد پاک کن */
export function pruneCart() {
  const clean = sanitize(cart.items);
  if (clean.length !== cart.items.length) {
    cart.items.splice(0, cart.items.length, ...clean);
    save();
    toast('برخی کالاهای سبد دیگر موجود نبودند و حذف شدند', 'err');
  }
}

export const cartCount = computed(() => cart.items.reduce((s, c) => s + c.qty, 0));
export const cartSub = computed(() => cart.items.reduce((s, c) => { const p = prod(c.pid); return s + (p ? priceOf(p, c.w) * c.qty : 0); }, 0));

/* اولین خرید (برای کد WELCOME10) */
export const isFirstOrder = computed(() => (LS.get('orders', [])).length === 0);
export const wonCodes = () => LS.get('codes', []);

export const couponDef = computed(() => {
  const code = cart.coupon;
  if (!code) return null;
  let def = COUPONS[code];
  if (def && def.first && !isFirstOrder.value) def = null;
  if (!def) {
    const lucky = wonCodes().find(x => x.code === code);
    if (lucky && COUPONS[lucky.code]) def = COUPONS[lucky.code];
  }
  return def || null;
});

export const couponVal = computed(() => {
  const c = couponDef.value;
  const sub = cartSub.value;
  if (!c || sub < (c.min || 0)) return { off: 0, ship: 0 };
  if (c.type === 'pct') return { off: Math.round(sub * c.val / 100), ship: 0 };
  if (c.type === 'cash') return { off: Math.min(c.val, sub), ship: 0 };
  if (c.type === 'ship') return { off: 0, ship: 1 };
  return { off: 0, ship: 0 };
});

export const shipRemain = computed(() => Math.max(0, FREE_SHIP - cartSub.value));
export const shipFree = computed(() => cartSub.value === 0 ? false : (shipRemain.value <= 0 || couponVal.value.ship === 1));
export const shipCost = computed(() => cartSub.value === 0 ? 0 : (shipFree.value ? 0 : 89000));
export const grandTotal = computed(() => Math.max(0, cartSub.value - couponVal.value.off + shipCost.value));

export function addToCart(pid, w, qty = 1, pack = false) {
  const p = prod(pid);
  if (!p) return;
  const line = cart.items.find(c => c.pid === pid && c.w === w);
  if (line) line.qty = Math.min(20, line.qty + qty);
  else cart.items.push({ pid, w, qty });
  save();
  toast(`${pack ? 'پک' : 'محصول'} «${p.name}» به سبد اضافه شد ✅`, 'ok');
}

export function lineQty(i, delta) {
  const it = cart.items[i];
  if (!it) return;
  if (delta === 0) { cart.items.splice(i, 1); toast('محصول از سبد حذف شد', 'ok'); }
  else if (delta > 0) it.qty = Math.min(20, it.qty + 1);
  else { it.qty--; if (it.qty < 1) cart.items.splice(i, 1); }
  save();
}

export function clearCart() { cart.items.splice(0); cart.coupon = null; save(); }

export function applyCoupon(raw) {
  const code = (raw || '').trim().toUpperCase();
  if (!code) return toast('کد تخفیف را وارد کنید', 'err');
  const def = COUPONS[code];
  const lucky = wonCodes().find(c => c.code === code);
  if (!def && !lucky) return toast('کد تخفیف نامعتبر است ❌', 'err');
  if (def && def.first && !isFirstOrder.value) return toast('کد WELCOME10 فقط برای اولین خرید است', 'err');
  const rule = def || COUPONS[lucky.code];
  if (cartSub.value < (rule.min || 0)) return toast(`این کد برای سفارش بالای ${money(rule.min)} تومان است`, 'err');
  cart.coupon = code;
  toast(`کد ${code} اعمال شد ✅ (${rule.label})`, 'gold');
}

export function markCouponUsed(code) {
  const codes = wonCodes();
  const c = codes.find(c => c.code === code);
  if (c) { c.used = true; LS.set('codes', codes); }
}

export function addWonCode(code, label) {
  const codes = wonCodes();
  if (!codes.some(c => c.code === code)) { codes.push({ code, label, used: false, ts: Date.now() }); LS.set('codes', codes); }
}

export const cartQtyLabel = computed(() => cartCount.value === 0 ? 'سبد خرید خالی است' : `${toFa(cartCount.value)} کالا در سبد`);
