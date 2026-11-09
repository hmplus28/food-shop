/* ---------- لایهٔ اتصال به بک‌اند (REST) — فروشگاه خانم گل ----------
 *
 * محصولات، سفارش‌ها و حساب کاربری به یک بک‌اند REST قابل اتصال‌اند.
 * تنظیمات در زمان «بیلد» با متغیرهای محیطی داخل باندل می‌رود (Vite):
 *
 *   VITE_API_ENABLED=true|false      کلیدِ اصلی؛ false یعنی فقط دادهٔ محلی
 *   VITE_API_BASE=https://…/api/v1   ریشهٔ API (بدون اسلش انتهایی)
 *   VITE_API_TIMEOUT=6000            سقف انتظار هر درخواست (میلی‌ثانیه)
 *
 * قرارداد نقاط پایانی (پاسخ‌ها JSON):
 *   GET   {BASE}/products              → آرایهٔ محصولات یا {results|data:[…]}
 *   POST  {BASE}/orders                → {code, status?}   (ثبت سفارش)
 *   GET   {BASE}/orders/{code}         → {code, status}    (پیگیری)
 *   PATCH {BASE}/orders/{code}         → {code, status}    (تغییر وضعیت مدیر)
 *   POST  {BASE}/auth/register         → {ok, user?, token?}
 *   POST  {BASE}/auth/login            → {ok, user?, token?}
 *   GET   {BASE}/health                → پاسخ 2xx (تست اتصال)
 *
 * اصل طراحی: هر خطا یا غیابی بک‌اند، «بی‌صدا» به دادهٔ محلی برمی‌گردد تا
 * فروشگاه همیشه کار کند (همان رفتار نسخهٔ GitHub Pages). توکن JWT در صورت
 * بازگشت بک‌اند، در LocalStorage ذخیره و با «Authorization: Bearer» ارسال
 * می‌شود. هیچ کلید/رازی در این فایل نیست — آدرس بک‌اند عمومی است.
 */
import { reactive } from 'vue';
import { LS, toEn } from '../data/site';
import { products, applyAdminOverrides } from '../data/catalog';

const raw = v => String(v ?? '').trim();
export const API_BASE = raw(import.meta.env.VITE_API_BASE).replace(/\/+$/, '');
export const API_ENABLED =
  raw(import.meta.env.VITE_API_ENABLED).toLowerCase() === 'true' && !!API_BASE;
const API_TIMEOUT = Math.max(1000, Number(raw(import.meta.env.VITE_API_TIMEOUT)) || 6000);

/* وضعیت اتصال — برای نمایش/دیباگ در کنسول و استفادهٔ لایه‌های دیگر */
export const apiState = reactive({
  enabled: API_ENABLED,
  base: API_BASE,
  online: false,        // آخرین تلاش موفق بوده؟
  lastError: null,      // آخرین خطای ثبت‌شده
  lastSync: 0,          // زمان آخرین همگام‌سازی موفق محصولات
});

const TOKEN_KEY = 'apiToken';
const token = () => LS.get(TOKEN_KEY, null);
const setToken = t => (t ? LS.set(TOKEN_KEY, t) : LS.del(TOKEN_KEY));

function note(err) {
  apiState.online = false;
  apiState.lastError = (err && err.message) || String(err);
  if (apiState.enabled) console.info('[خانم گل] بک‌اند در دسترس نیست؛ از دادهٔ محلی استفاده می‌شود —', apiState.lastError);
  return null;
}

/* درخواست پایه با سقف زمانی (AbortController) و مدیریت متمرکز خطا */
async function req(path, { method = 'GET', body, timeout = API_TIMEOUT } = {}) {
  if (!API_ENABLED) throw new Error('API غیرفعال است');
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);
  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      signal: ctrl.signal,
      headers: {
        'Accept': 'application/json',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token() ? { 'Authorization': 'Bearer ' + token() } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    clearTimeout(timer);
    throw new Error(e.name === 'AbortError' ? 'پاسخ بک‌اند بیش از حد طول کشید' : 'اتصال به بک‌اند برقرار نشد');
  }
  clearTimeout(timer);
  if (!res.ok) throw new Error('پاسخ ' + res.status + ' از بک‌اند');
  const text = await res.text();
  try { return text ? JSON.parse(text) : null; }
  catch { throw new Error('پاسخ JSON نبود'); }
}

/* ---------------- محصولات ---------------- */

/* نرمال‌سازی یک محصولِ بک‌اند به ساختار داخلی (فیلدهای جایگزین پشتیبانی می‌شوند) */
function normalizeProduct(r, i) {
  if (!r || typeof r !== 'object') return null;
  const num = (v, d = 0) => { const n = Number(v); return Number.isFinite(n) ? n : d; };
  const list = v => (Array.isArray(v) ? v : String(v ?? '').split(',')).map(Number).filter(n => Number.isFinite(n) && n > 0);
  const name = String(r.name ?? r.title ?? '').trim();
  if (!name) return null;
  return {
    id: num(r.id, 1000 + i),
    name,
    cat: String(r.cat ?? r.category ?? r.category_id ?? 'ajil'),
    img: String(r.img ?? r.image ?? r.photo ?? r.url ?? ''),
    price: num(r.price),
    weights: list(r.weights ?? r.weight_options).length ? list(r.weights ?? r.weight_options) : [500],
    stock: num(r.stock, 0),
    disc: num(r.disc ?? r.discount, 0),
    grade: String(r.grade ?? 'درجه یک'),
    rate: num(r.rate ?? r.rating, 4.5),
    sold: num(r.sold ?? r.sales, 0),
    tags: Array.isArray(r.tags) ? r.tags.map(String) : [],
    sec: Array.isArray(r.sec ?? r.sections) ? (r.sec ?? r.sections).map(String) : [],
    desc: String(r.desc ?? r.description ?? ''),
    ...(r.hide != null ? { hide: !!r.hide } : {}),
  };
}

function extractList(json) {
  if (Array.isArray(json)) return json;
  if (json && Array.isArray(json.results)) return json.results;
  if (json && Array.isArray(json.data)) return json.data;
  return null;
}

/* همگام‌سازی فهرست محصولات از بک‌اند به آرایهٔ واکنش‌گرا؛ خطا → دادهٔ محلی */
export async function syncCatalog() {
  if (!API_ENABLED) return false;
  try {
    const list = extractList(await req('/products'));
    if (!list) throw new Error('ساختار پاسخ محصولات قابل خواندن نبود');
    const mapped = list.map(normalizeProduct).filter(Boolean);
    if (!mapped.length) throw new Error('فهرست محصولات خالی بود');
    products.splice(0, products.length, ...mapped);
    applyAdminOverrides();          // ویرایش‌های آزمایشی پنل مدیر حفظ شوند
    apiState.online = true;
    apiState.lastError = null;
    apiState.lastSync = Date.now();
    console.info('[خانم گل] فهرست محصولات از بک‌اند همگام شد (' + mapped.length + ' مورد).');
    return true;
  } catch (e) { note(e); return false; }
}

/* ---------------- سفارش‌ها ---------------- */

/* ثبت سفارش روی بک‌اند؛ موفق → {code, status?} ، ناموفق → null (سفارش محلی می‌ماند) */
export async function createOrderApi(order) {
  if (!API_ENABLED) return null;
  try {
    const res = await req('/orders', { method: 'POST', body: order });
    apiState.online = true;
    return res && typeof res === 'object' ? res : { ok: true };
  } catch (e) { note(e); return null; }
}

/* وضعیت لحظه‌ای سفارش از بک‌اند؛ ناموفق → null */
export async function fetchOrderStatusApi(code) {
  if (!API_ENABLED) return null;
  try {
    const res = await req('/orders/' + encodeURIComponent(String(code).toUpperCase()));
    apiState.online = true;
    const st = Number(res && res.status);
    return Number.isInteger(st) && st >= 0 && st <= 3 ? st : null;
  } catch (e) { note(e); return null; }
}

/* تغییر وضعیت سفارش از پنل مدیر؛ ناموفق → false */
export async function patchOrderStatusApi(code, status) {
  if (!API_ENABLED) return false;
  try {
    await req('/orders/' + encodeURIComponent(String(code).toUpperCase()), {
      method: 'PATCH', body: { status },
    });
    apiState.online = true;
    return true;
  } catch (e) { note(e); return false; }
}

/* ---------------- حساب کاربری ---------------- */

const okUser = u => u && typeof u === 'object' && u.name && u.phone;

/* ثبت‌نام روی بک‌اند؛ پاسخ: {ok, user?, msg?} — خطای شبکه → null (caller به محلی برمی‌گردد) */
export async function authRegisterApi(name, phone, pass) {
  if (!API_ENABLED) return null;
  try {
    const res = await req('/auth/register', { method: 'POST', body: { name, phone: toEn(phone).replace(/\D/g, ''), password: pass } });
    apiState.online = true;
    if (res && res.token) setToken(res.token);
    const user = okUser(res && res.user) ? { name: String(res.user.name), phone: toEn(String(res.user.phone)).replace(/\D/g, '') } : null;
    return { ok: !!(res && res.ok !== false), user };
  } catch (e) { note(e); return null; }
}

/* ورود روی بک‌اند؛ همان قرارداد authRegisterApi */
export async function authLoginApi(phone, pass) {
  if (!API_ENABLED) return null;
  try {
    const res = await req('/auth/login', { method: 'POST', body: { phone: toEn(phone).replace(/\D/g, ''), password: pass } });
    apiState.online = true;
    if (res && res.token) setToken(res.token);
    const user = okUser(res && res.user) ? { name: String(res.user.name), phone: toEn(String(res.user.phone)).replace(/\D/g, '') } : null;
    return { ok: !!user || !!(res && res.ok === true), user };
  } catch (e) { note(e); return null; }
}

/* ---------------- تست اتصال (برای عیب‌یابی) ---------------- */
export async function pingApi() {
  if (!API_ENABLED) return false;
  try { await req('/health', { timeout: 3000 }); apiState.online = true; return true; }
  catch (e) { note(e); return false; }
}

/* خروج: پاک‌سازی توکن بک‌اند */
export function apiLogout() { setToken(null); }
