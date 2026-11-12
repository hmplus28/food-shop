/* ---------- ابزارهای مشترک خانم گل ---------- */
export const FA_D = '۰۱۲۳۴۵۶۷۸۹';
export const toFa = s => String(s).replace(/\d/g, d => FA_D[d]);
export const toEn = s => String(s).replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)));
export const money = n => toFa(Math.round(n).toLocaleString('en-US')).replace(/,/g, '٬');

/* ذخیره‌سازی محلی با نام‌فضای اختصاصی فروشگاه */
import { jDate, jTime, jDateTime } from './jalali';

export const LS = {
  get(k, def) { try { const v = localStorage.getItem('asalat_' + k); return v ? JSON.parse(v) : def; } catch (e) { return def; } },
  set(k, v) { try { localStorage.setItem('asalat_' + k, JSON.stringify(v)); } catch (e) {} },
  del(k) { try { localStorage.removeItem('asalat_' + k); } catch (e) {} }
};

export const weightLabel = w =>
  w === 1 ? 'عدد'
    : w >= 1000 ? (w % 1000 === 0 ? toFa(w / 1000) + ' کیلوگرم' : toFa((w / 1000).toFixed(1)).replace('.', '٫') + ' کیلوگرم')
      : toFa(w) + ' گرم';

/* قیمت‌گذاری خودکار بر اساس وزن (پایه: قیمت هر کیلوگرم/عدد) */
export const priceOf = (p, w) => {
  const base = Math.round(p.price * w / 1000);
  return p.disc ? Math.round(base * (100 - p.disc) / 100 / 1000) * 1000 : base;
};

export const FREE_SHIP = 1500000;      // سقف ارسال رایگان
export const BASE_SHIP = 89000;        // هزینه پیش‌فرض پیک
export const SHIP_OPTIONS = [
  { type: 'peyk',  label: 'پیک فوری (تهران)',          days: 'همان روز',        cost: 89000, hint: 'تحویل همان روز، ۲ تا ۵ ساعت کاری' },
  { type: 'post',  label: 'پست پیشتاز (سراسر کشور)',   days: '۲ تا ۴ روز کاری', cost: 59000, hint: '۲ تا ۴ روز کاری' },
  { type: 'tipax', label: 'تیپاکس (سراسر کشور)',       days: '۱ تا ۳ روز کاری', cost: 99000, hint: '۱ تا ۳ روز کاری، بسته‌های حجیم' }
];

export const fmtHMS = ms => {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = String(Math.floor(s / 3600)).padStart(2, '0');
  const m = String(Math.floor(s % 3600 / 60)).padStart(2, '0');
  const x = String(s % 60).padStart(2, '0');
  return toFa(`${h}:${m}:${x}`);
};

export const DAY_NAMES = ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه'];
export const WEEK_ORDER = [6, 0, 1, 2, 3, 4, 5]; // ترتیب هفته فارسی: شنبه تا جمعه

/* همهٔ تاریخ‌ها شمسی (jalali.js) */
export const faDate = ts => jDate(ts);
export const faTime = ts => jTime(ts);
export const faDateTime = ts => jDateTime(ts);
