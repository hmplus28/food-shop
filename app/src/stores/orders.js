/* ---------- سفارش‌ها ----------
   سفارش همیشه اول در همین مرورگر ذخیره می‌شود (فروشگاه هیچ‌وق از کار نمی‌افتد)، و اگر
   بک‌اند فعال باشد (VITE_API_ENABLED=true)، همان لحظه به سرور هم POST می‌شود؛
   خطای شبکه بی‌صدا نادیده گرفته می‌شود و سفارش محلی معتبر می‌ماند. */
import { LS, toEn, money } from '../data/site';
import { toast } from './ui';
import { cart, couponVal, cartSub, shipCost, clearCart, markCouponUsed } from './cart';
import { SHIP_OPTIONS } from '../data/site';
import { apiState, createOrderApi, fetchOrderStatusApi, patchOrderStatusApi } from '../services/api';

export const orders = LS.get('orders', []);
const save = () => LS.set('orders', orders);

export const STATUS = ['در حال ثبت', 'در حال آماده‌سازی', 'در مسیر ارسال', 'تحویل شده'];

/* مقیاس نمایشی: هر مرحله چند دقیقه جلو می‌رود — فقط برای سفارش‌های بدون
   وضعیت واقعی؛ سفارش‌های همگام‌شده از بک‌اند status عددی واقعی دارند. */
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
  pushOrder(order);          // ارسال به بک‌اند (اگر فعال باشد)؛ موفق/ناموفق بی‌صدا
  return order;
}

/* ارسال غیرهمگام سفارش به بک‌اند؛ اگر سرور کد خودش را بدهید به‌عنوان
   remoteCode ذخیره می‌شود تا پیگیری با هر دو کد ممکن باشد. */
function pushOrder(order) {
  if (!apiState.enabled) return;
  createOrderApi({
    code: order.code, ts: order.ts, items: order.items, sub: order.sub,
    off: order.off, coupon: order.coupon, shipCost: order.shipCost,
    shipType: order.shipType, shipLabel: order.shipLabel, shipDays: order.shipDays,
    total: order.total, addr: order.addr, status: order.status,
  }).then(res => {
    if (res && res.code && String(res.code).toUpperCase() !== order.code) {
      order.remoteCode = String(res.code).toUpperCase();
      save();
    }
    if (res && Number.isInteger(Number(res.status))) { order.status = Number(res.status); save(); }
  }).catch(() => {});
}

export function findOrder(q) {
  q = toEn(q).trim().toUpperCase();
  if (!q) return null;
  if (!q.startsWith('AS-') && /^\d+$/.test(q)) q = 'AS-' + q.replace(/^0+/, '');
  return orders.find(o => o.code === q || o.remoteCode === q) || null;
}

export function findByPhone(phone) {
  const p = toEn(phone).replace(/\D/g, '');
  return /^09\d{9}$/.test(p) ? orders.filter(o => o.addr.phone === p) : [];
}

export function setStatus(code, st) {
  const o = orders.find(x => x.code === code || x.remoteCode === code);
  if (o) {
    o.status = st; save();
    toast(`وضعیت سفارش ${o.code} به «${STATUS[st]}» تغییر کرد`, 'ok');
    if (apiState.enabled) patchOrderStatusApi(code, st).catch(() => {});   // همگام‌سازی پنل مدیر با بک‌اند
  }
}

/* تازه‌سازی وضعیت یک سفارش از بک‌اند (صفحهٔ پیگیری)؛ ناموفق → بی‌صدا */
export async function refreshOrderStatus(code) {
  if (!apiState.enabled) return null;
  const st = await fetchOrderStatusApi(code);
  if (st == null) return null;
  const o = orders.find(x => x.code === String(code).toUpperCase() || x.remoteCode === String(code).toUpperCase());
  if (o && o.status !== st) { o.status = st; save(); }
  return st;
}

export const spentTotal = () => orders.reduce((s, o) => s + o.total, 0);
export const tierOf = t => t >= 15000000 ? { n: 'طلایی', i: '🥇' } : t >= 5000000 ? { n: 'نقره‌ای', i: '🥈' } : { n: 'برنزی', i: '🥉' };
export const moneyOf = money;
