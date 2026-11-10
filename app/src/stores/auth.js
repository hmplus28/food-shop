/* ---------- حساب کاربری و پنل مدیر ----------
   اولویت با بک‌اند REST است (services/api.js): اگر VITE_API_ENABLED=true باشد
   ثبت‌نام/ورود به سرور می‌رود و توکن ذخیره می‌شود؛ در خطای شبکه یا غیاب
   بک‌اند، بی‌صدا به نسخهٔ آزمایشی LocalStorage برمی‌گردد تا فروشگاه همیشه
   کار کند. ورود با «کد پیامکی» فقط سمت بک‌اند انجام می‌شود (پنل پیامک). */
import { reactive } from 'vue';
import { LS, toEn } from '../data/site';
import { apiState, authRegisterApi, authLoginApi, apiLogout, authOtpRequestApi, authOtpVerifyApi, adminLoginApi } from '../services/api';

export const ADMIN_USER = 'admin';
export const ADMIN_PASS = 'admin1234';

export const auth = reactive({
  user: LS.get('user', null),          // {name, phone}
  isAdmin: LS.get('admin', false),
});

const users = () => LS.get('users', []);
const saveUsers = u => LS.set('users', u);

export async function register(name, phone, pass) {
  const p = toEn(phone).replace(/\D/g, '');
  if (!name.trim()) return { ok: false, msg: 'نام و نام خانوادگی را وارد کنید' };
  if (!/^09\d{9}$/.test(p)) return { ok: false, msg: 'شماره موبایل معتبر وارد کنید (۰۹…)' };
  if ((pass || '').length < 4) return { ok: false, msg: 'رمز عبور حداقل ۴ کاراکتر باشد' };
  /* اول بک‌اند (اگر فعال است) — خطای شبکه → نسخهٔ محلی */
  if (apiState.enabled) {
    const r = await authRegisterApi(name.trim(), p, pass);
    if (r) {
      if (!r.ok) return { ok: false, msg: r.msg || 'ثبت‌نام در سرور انجام نشد' };
      const user = r.user || { name: name.trim(), phone: p };
      mirrorLocalUser(user.name, user.phone, pass);   // برای ورود آفلاین بعدی
      auth.user = user;
      LS.set('user', auth.user);
      return { ok: true };
    }
  }
  const list = users();
  if (list.some(u => u.phone === p)) return { ok: false, msg: 'این شماره قبلاً ثبت‌نام کرده است؛ وارد شوید' };
  list.push({ name: name.trim(), phone: p, pass });
  saveUsers(list);
  auth.user = { name: name.trim(), phone: p };
  LS.set('user', auth.user);
  return { ok: true };
}

/* نگه‌داشتن نسخهٔ محلی حساب، تا در نبود بک‌اند هم ورود کار کند */
function mirrorLocalUser(name, phone, pass) {
  const list = users();
  if (!list.some(u => u.phone === phone)) { list.push({ name, phone, pass }); saveUsers(list); }
}

export async function login(phone, pass) {
  const p = toEn(phone).replace(/\D/g, '');
  /* اول بک‌اند (اگر فعال است) — خطای شبکه → نسخهٔ محلی */
  if (apiState.enabled) {
    const r = await authLoginApi(p, pass);
    if (r) {
      if (!r.ok) return { ok: false, msg: r.msg || 'شماره یا رمز عبور اشتباه است' };
      const user = r.user || (() => { const u = users().find(x => x.phone === p); return u ? { name: u.name, phone: p } : { name: 'کاربر', phone: p }; })();
      mirrorLocalUser(user.name, p, pass);
      auth.user = user;
      LS.set('user', auth.user);
      return { ok: true };
    }
  }
  const u = users().find(x => x.phone === p);
  if (!u || u.pass !== pass) return { ok: false, msg: 'شماره یا رمز عبور اشتباه است' };
  auth.user = { name: u.name, phone: u.phone };
  LS.set('user', auth.user);
  return { ok: true };
}

export function logout() {
  auth.user = null;
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

/* درخواست کد ورود پیامکی — فقط با بک‌اند (پنل پیامک سمت سرور است) */
export async function otpRequest(phone) {
  const p = toEn(phone).replace(/\D/g, '');
  if (!/^09\d{9}$/.test(p)) return { ok: false, msg: 'شماره موبایل معتبر وارد کنید (۰۹…)' };
  const r = await authOtpRequestApi(p);
  if (!r) return { ok: false, msg: 'اتصال به سرور برقرار نشد؛ دوباره تلاش کنید' };
  return r;                     // {ok, msg?, expiresIn?, cooldown?, devCode?}
}

/* بررسی کد پیامکی و ورود/ثبت‌نام خودکار */
export async function otpVerify(phone, code) {
  const p = toEn(phone).replace(/\D/g, '');
  const c = toEn(code).replace(/\D/g, '');
  if (!/^09\d{9}$/.test(p)) return { ok: false, msg: 'شماره موبایل معتبر نیست' };
  if (!/^\d{4,6}$/.test(c)) return { ok: false, msg: 'کد ۴ تا ۶ رقمی پیامک‌شده را وارد کنید' };
  const r = await authOtpVerifyApi(p, c);
  if (!r) return { ok: false, msg: 'اتصال به سرور برقرار نشد؛ دوباره تلاش کنید' };
  if (!r.ok) return r;
  auth.user = r.user;
  LS.set('user', auth.user);
  return { ok: true, created: r.created };
}

export function adminLogin(u, p) {
  return _adminLoginInner(u, p);
}

/* ورود مدیر: اول بک‌اند (توکن نقش admin)؛ در غیاب/خطای شبکه فالبک محلی دمو */
async function _adminLoginInner(u, p) {
  if (apiState.enabled) {
    const r = await adminLoginApi(u.trim(), p);
    if (r) {
      if (!r.ok) return { ok: false, msg: r.msg || 'نام کاربری یا رمز مدیر اشتباه است' };
      auth.isAdmin = true;
      LS.set('admin', true);
      return { ok: true, server: true };
    }
  }
  if (u.trim() === ADMIN_USER && p === ADMIN_PASS) {
    auth.isAdmin = true;
    LS.set('admin', true);
    return { ok: true };
  }
  return { ok: false, msg: 'نام کاربری یا رمز مدیر اشتباه است' };
}

export function adminLogout() {
  auth.isAdmin = false;
  LS.set('admin', false);
}
