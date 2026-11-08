/* ---------- سفارش‌ها ---------- */
import { LS, toEn, money } from '../data/site';
import { toast } from './ui';
import { cart, couponVal, cartSub, shipCost, clearCart, markCouponUsed } from './cart';
import { SHIP_OPTIONS } from '../data/site';

export const orders = LS.get('orders', []);
const save = () => LS.set('orders', orders);

export const STATUS = ['در حال ثبت', 'در حال آماده‌سازی', 'در مسیر ارسال', 'تحویل شده'];

/* مقیاس نمایشی: هر مرحله چند دقیقه جلو می‌رود (تا زمان اتصال بک‌اند واقعی) */
export function orderStep(o) {
  if (typeof o.status === 'number') return o.status;
  const m = (Date.now() - o.ts) / 60000;
  return m < 2 ? 0 : m < 6 ? 1 : m < 15 ? 2 : 3;
}

export function placeOrder({ addr, shipType }) {
  const sub = cartSub.value, cv = couponVal.value;
  const free = (Math.max(0, 1500000 - sub) <= 0) || cv.ship === 1;
  const opt = SHIP_OPTIONS.find(s => s.type === shipType) || SHIP_OPTIONS[0];
  const sc = free ? 0 : opt.cost;
  const total = Math.max(0, sub - cv.off + sc);
  const code = 'AS-' + (1000 + orders.length + Math.floor(Math.random() * 90));
  const order = {
    code, ts: Date.now(),
    items: cart.items.map(c => ({ ...c })),
    sub, off: cv.off, coupon: cart.coupon,
    shipCost: sc, shipType: opt.type, shipLabel: opt.label, shipDays: opt.days,
    total, addr: { ...addr, phone: toEn(addr.phone).replace(/\D/g, '') },
    status: 0,
  };
  orders.unshift(order);
  save();
  if (cart.coupon && cart.coupon !== 'WELCOME10') markCouponUsed(cart.coupon);
  clearCart();
  return order;
}

export function findOrder(q) {
  q = toEn(q).trim().toUpperCase();
  if (!q) return null;
  if (!q.startsWith('AS-')) q = 'AS-' + q.replace(/^0+/, '');
  return orders.find(o => o.code === q) || null;
}

export function findByPhone(phone) {
  const p = toEn(phone).replace(/\D/g, '');
  return /^09\d{9}$/.test(p) ? orders.filter(o => o.addr.phone === p) : [];
}

export function setStatus(code, st) {
  const o = orders.find(x => x.code === code);
  if (o) { o.status = st; save(); toast(`وضعیت سفارش ${code} به «${STATUS[st]}» تغییر کرد`, 'ok'); }
}

export const spentTotal = () => orders.reduce((s, o) => s + o.total, 0);
export const tierOf = t => t >= 15000000 ? { n: 'طلایی', i: '🥇' } : t >= 5000000 ? { n: 'نقره‌ای', i: '🥈' } : { n: 'برنزی', i: '🥉' };
export const moneyOf = money;
