/* ---------- حساب کاربری و پنل مدیر ----------
   اولویت با بک‌اند REST است (services/api.js): اگر VITE_API_ENABLED=true باشد
   ثبت‌نام/ورود به سرور می‌رود و توکن ذخیره می‌شود؛ در خطای شبکه یا غیاب
   بک‌اند، بی‌صدا به نسخهٔ آزمایشی LocalStorage برمی‌گردد تا فروشگاه همیشه
   کار کند. نقش مدیر (سوپریوزر) فقط از سرور می‌آید (role=admin)، نه از مقدار قابل‌دستکاریِ مرورگر. */
import { reactive } from 'vue';
import { LS, toEn } from '../data/site';
import { clearOrders } from './orders';
import { apiState, authRegisterApi, authLoginApi, apiLogout, adminLoginApi, meApi } from '../services/api';

export const auth = reactive({
  user: LS.get('user', null),          // {name, phone}
  isAdmin: false,                      // فقط پس از تأیید سرور true می‌شود (refreshSession / ورود)
});

const users = () => LS.get('users', []);
const saveUsers = u => LS.set('users', u);

export async function register(name, phone, pass) {
  const p = toEn(phone).replace(/\D/g, '');
  if (!name.trim()) return { ok: false, msg: 'نام و نام خانوادگی را وارد کنید' };
  if (!/^09\d{9}$/.test(p)) return { ok: false, msg: 'شماره موبایل معتبر وارد کنید (۰۹…)' };
  if ((pass || '').length < 4) return { ok: false, msg: 'رمز عبور حداقل ۴ کاراکتر باشد' };
  /* با بک‌اند فعال، فقط سرور تصمیم می‌گیرد؛ نسخهٔ محلی فقط برای دموی بدون سرور است */
  if (apiState.enabled) {
    const r = await authRegisterApi(name.trim(), p, pass);
    if (r) {
      if (!r.ok) return { ok: false, msg: r.msg || 'ثبت‌نام در سرور انجام نشد' };
      const user = r.user || { name: name.trim(), phone: p };
      if (auth.user && auth.user.phone !== user.phone) clearOrders();
      auth.user = user;
      LS.set('user', auth.user);
      return { ok: true };
    }
    return { ok: false, msg: 'اتصال به سرور برقرار نشد؛ لطفاً دوباره تلاش کنید' };   // حساب «فقط‌محلی» ساخته نمی‌شود
  }
  const list = users();
  if (list.some(u => u.phone === p)) return { ok: false, msg: 'این شماره قبلاً ثبت‌نام کرده است؛ وارد شوید' };
  list.push({ name: name.trim(), phone: p, pass });
  saveUsers(list);
  auth.user = { name: name.trim(), phone: p };
  LS.set('user', auth.user);
  return { ok: true };
}

export async function login(phone, pass) {
  const p = toEn(phone).replace(/\D/g, '');
  /* با بک‌اند فعال، فقط سرور تصمیم می‌گیرد؛ نسخهٔ محلی فقط برای دموی بدون سرور است */
  if (apiState.enabled) {
    const r = await authLoginApi(p, pass);
    if (r) {
      if (!r.ok) return { ok: false, msg: r.msg || 'شماره یا رمز عبور اشتباه است' };
      const user = r.user || (() => { const u = users().find(x => x.phone === p); return u ? { name: u.name, phone: p } : { name: 'کاربر', phone: p }; })();
      if (auth.user && auth.user.phone !== user.phone) clearOrders();
      auth.user = user;
      auth.isAdmin = user.role === 'admin';
      LS.set('user', auth.user);
      return { ok: true };
    }
    return { ok: false, msg: 'اتصال به سرور برقرار نشد؛ لطفاً دوباره تلاش کنید' };
  }
  const u = users().find(x => x.phone === p);
  if (!u || u.pass !== pass) return { ok: false, msg: 'شماره یا رمز عبور اشتباه است' };
  auth.user = { name: u.name, phone: u.phone };
  LS.set('user', auth.user);
  return { ok: true };
}

export function logout() {
  if (apiState.enabled) clearOrders();
  auth.user = null;
  auth.isAdmin = false;
  LS.set('user', null);
  apiLogout();          // توکن بک‌اند هم پاک شود
}

export function updateProfile(name, phone) {
  const p = toEn(phone).replace(/\D/g, '');
  if (p && !/^09\d{9}$/.test(p)) return { ok: false, msg: 'شماره موبایل معتبر نیست' };
  auth.user = { name: name.trim(), phone: p };
  LS.set('user', auth.user);
  const list = users();
  const u = list.find(x => x.phone === p);
  if (u) { u.name = name.trim(); saveUsers(list); }
  return { ok: true };
}

export function adminLogin(u, p) {
  return _adminLoginInner(u, p);
}

/* ورود مدیر (نام کاربری یا موبایل + رمز) — فقط با تأیید سرور؛ بدون حساب محلی/پیش‌فرض */
async function _adminLoginInner(u, p) {
  if (!apiState.enabled) return { ok: false, msg: 'پنل مدیریت به اتصال سرور نیاز دارد' };
  const r = await adminLoginApi(u.trim(), p);
  if (!r) return { ok: false, msg: 'اتصال به سرور برقرار نشد؛ دوباره تلاش کنید' };
  if (!r.ok) return { ok: false, msg: r.msg || 'نام کاربری یا رمز مدیر اشتباه است' };
  auth.isAdmin = true;
  return { ok: true, server: true };
}

export function adminLogout() {
  clearOrders();
  auth.isAdmin = false;
  apiLogout();
  auth.user = null;
  LS.set('user', null);
}

/* بررسی نشست با سرور هنگام بارگذاری: نقش واقعی را می‌گیرد؛ توکن باطل → خروج */
export async function refreshSession() {
  LS.del('admin');                       // پرچم قدیمیِ قابل‌دستکاری
  if (!apiState.enabled) return;
  const me = await meApi();
  if (!me) return;                       // بدون توکن/شبکه: وضعیت فعلی
  if (me.expired) { auth.user = null; auth.isAdmin = false; LS.set('user', null); return; }
  auth.user = { name: me.name, phone: me.phone, role: me.role };
  auth.isAdmin = me.role === 'admin';
  LS.set('user', auth.user);
}
