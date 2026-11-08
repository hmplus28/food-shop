/* ---------- حساب کاربری و پنل مدیر (نسخه نمایشی مبتنی بر LocalStorage) ----------
   بعداً که بک‌اند آماده شد، فقط بدنهٔ این توابع را با fetch عوض کنید؛
   بقیهٔ برنامه از این لایه استفاده می‌کند و چیزی عوض نمی‌شود. */
import { reactive } from 'vue';
import { LS, toEn } from '../data/site';

export const ADMIN_USER = 'admin';
export const ADMIN_PASS = 'admin1234';

export const auth = reactive({
  user: LS.get('user', null),          // {name, phone}
  isAdmin: LS.get('admin', false),
});

const users = () => LS.get('users', []);
const saveUsers = u => LS.set('users', u);

export function register(name, phone, pass) {
  const p = toEn(phone).replace(/\D/g, '');
  if (!name.trim()) return { ok: false, msg: 'نام و نام خانوادگی را وارد کنید' };
  if (!/^09\d{9}$/.test(p)) return { ok: false, msg: 'شماره موبایل معتبر وارد کنید (۰۹…)' };
  if ((pass || '').length < 4) return { ok: false, msg: 'رمز عبور حداقل ۴ کاراکتر باشد' };
  const list = users();
  if (list.some(u => u.phone === p)) return { ok: false, msg: 'این شماره قبلاً ثبت‌نام کرده است؛ وارد شوید' };
  list.push({ name: name.trim(), phone: p, pass });
  saveUsers(list);
  auth.user = { name: name.trim(), phone: p };
  LS.set('user', auth.user);
  return { ok: true };
}

export function login(phone, pass) {
  const p = toEn(phone).replace(/\D/g, '');
  const u = users().find(x => x.phone === p);
  if (!u || u.pass !== pass) return { ok: false, msg: 'شماره یا رمز عبور اشتباه است' };
  auth.user = { name: u.name, phone: u.phone };
  LS.set('user', auth.user);
  return { ok: true };
}

export function logout() {
  auth.user = null;
  LS.set('user', null);
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
