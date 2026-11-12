/* ---------- سفارش‌ها ----------
   سفارش همیشه اول در همین مرورگر ذخیره می‌شود (فروشگاه هیچ‌وق از کار نمی‌افتد)، و اگر
   بک‌اند فعال باشد (VITE_API_ENABLED=true)، همان لحظه به سرور هم POST می‌شود؛
   خطای شبکه بی‌صدا نادیده گرفته می‌شود و سفارش محلی معتبر می‌ماند. */
import { LS, toEn, money } from '../data/site';
import { toast } from './ui';
import { cart, couponVal, cartSub, shipCost, clearCart, markCouponUsed } from './cart';
import { shipMethods, freeFrom, freeShipOn } from './shop';
import { apiState, apiCall, createOrderStrict, createOrderApi, fetchOrderStatusApi, patchOrderStatusApi, myOrdersApi } from '../services/api';

export const orders = LS.get('orders', []);
const save = () => LS.set('orders', orders);

/* با تغییر حساب (ورود/خروج) سفارش‌های محلیِ حساب قبلی نباید دیده شوند */
export function clearOrders() { orders.splice(0); save(); }

export const STATUS = ['در حال ثبت', 'در حال آماده‌سازی', 'در مسیر ارسال', 'تحویل شده'];

/* مقیاس نمایشی: هر مرحله چند دقیقه جلو می‌رود — فقط برای سفارش‌های بدون
   وضعیت واقعی؛ سفارش‌های همگام‌شده از بک‌اند status عددی واقعی دارند. */
export function orderStep(o) {
  if (typeof o.status === 'number') return o.status;
  const m = (Date.now() - o.ts) / 60000;
  return m < 2 ? 0 : m < 6 ? 1 : m < 15 ? 2 : 3;
}

/* ثبت سفارش با سرور فعال: فقط با حساب؛ قیمت‌ها را سرور محاسبه و برمی‌گرداند. خروجی {ok, order?, msg?} */
export async function placeOrderServer({ addr, shipType, note = '' }) {
  const body = {
    items: cart.items.map(c => ({ pid: c.pid, w: c.w, qty: c.qty })),
    coupon: cart.coupon || '', shipType,
    addr: { name: addr.name.trim(), phone: toEn(addr.phone).replace(/\D/g, ''), prov: addr.prov, city: addr.city.trim(), addr: addr.addr.trim() },
    note,
  };
  const r = await createOrderStrict(body);
  if (!r.ok) return { ok: false, msg: r.msg || 'ثبت سفارش انجام نشد', status: r.status };
  const opt = shipMethods.value.find(m => m.type === shipType) || {};
  const order = {
    code: r.code, remoteCode: r.code, ts: Date.now(), items: cart.items.map(c => ({ ...c })),
    sub: r.sub, off: r.off, coupon: cart.coupon, shipCost: r.ship_cost, shipType, shipLabel: opt.label, shipDays: opt.days,
    total: r.total, addr: body.addr, status: Number(r.status) || 0, fromServer: true,
  };
  orders.unshift(order);
  save();
  clearCart();
  return { ok: true, order };
}

export function placeOrder({ addr, shipType }) {
  const sub = cartSub.value, cv = couponVal.value;
  const free = (freeShipOn.value && sub >= freeFrom.value) || cv.ship === 1;
  const opt = shipMethods.value.find(s => s.type === shipType) || shipMethods.value[0];
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

/* پیگیری عمومی با کد سفارش: با سرور فعال از سرور (روی هر دستگاهی کار می‌کند)، وگرنه نسخهٔ محلی */
export async function trackOrder(q) {
  const code = toEn(q).trim().toUpperCase();
  if (!code) return null;
  if (apiState.enabled) {
    const r = await apiCall('/orders/' + encodeURIComponent(code));
    if (!r.ok || !r.code) return null;
    return {
      code: r.code, ts: r.ts, status: Number(r.status) || 0, total: r.total, shipLabel: r.ship_label, shipDays: r.ship_days,
      shipType: /پیک/.test(r.ship_label || '') ? 'peyk' : 'post',
      items: (r.items || []).map(c => ({ pid: c.pid, w: c.w, qty: c.qty, pname: c.name })), addr: {},
    };
  }
  return findOrder(code);
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

/* واکشی سفارش‌های کاربر لاگین‌شده از بک‌اند و ادغام با نسخهٔ محلی؛
   برای پنل کاربری — خطای شبکه بی‌صدا نادیده گرفته می‌شود. */
export async function syncMineOrders() {
  if (!apiState.enabled) return 0;
  const res = await myOrdersApi();
  if (!res || !Array.isArray(res.results)) return 0;
  let added = 0;
  for (const r of res.results) {
    const local = orders.find(o => o.code === r.code || o.remoteCode === r.code
      || (r.client_code && (o.code === r.client_code || o.remoteCode === r.client_code)));
    if (local) {
      if (Number.isInteger(r.status) && local.status !== r.status) { local.status = r.status; save(); }
      if (r.code && local.remoteCode !== r.code) { local.remoteCode = r.code; save(); }
      continue;
    }
    orders.unshift({
      code: r.code, remoteCode: r.code, ts: r.ts || Date.now(),
      items: (r.items || []).map(c => ({ pid: c.pid, w: c.w, qty: c.qty })),
      sub: r.sub, off: r.off, coupon: r.coupon,
      shipCost: r.ship_cost, shipType: r.ship_type, shipLabel: r.ship_label, shipDays: r.ship_days,
      total: r.total, addr: r.addr || { phone: '' }, status: Number(r.status) || 0,
      fromServer: true,
    });
    added++;
  }
  if (added) save();
  return added;
}

export const spentTotal = () => orders.reduce((s, o) => s + o.total, 0);
export const tierOf = t => t >= 15000000 ? { n: 'طلایی', i: '🥇' } : t >= 5000000 ? { n: 'نقره‌ای', i: '🥈' } : { n: 'برنزی', i: '🥉' };
export const moneyOf = money;
