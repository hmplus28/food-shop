/* ---------- تقویم شمسی (جلالی) ----------
   نمایش: همیشه با تقویم persian و ارقام فارسی (مستقل از پیش‌فرض مرورگر).
   ورودی مدیر: «۱۴۰۵/۱۲/۲۹» ↔ تاریخ میلادی ISO برای سرور. */

const DIGITS = '۰۱۲۳۴۵۶۷۸۹';
export const toEnDigits = s => String(s ?? '').replace(/[۰-۹]/g, d => DIGITS.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));

const fmtDate = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { year: 'numeric', month: '2-digit', day: '2-digit' });
const fmtTime = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { hour: '2-digit', minute: '2-digit', hour12: false });
const fmtLong = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
const fmtYear = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { year: 'numeric' });

const toDate = v => (v instanceof Date ? v : new Date(v));
/* ۱۴۰۵/۰۸/۲۳ */
export const jDate = v => fmtDate.format(toDate(v));
/* ۱۴:۳۰ */
export const jTime = v => fmtTime.format(toDate(v));
/* ۱۴۰۵/۰۸/۲۳ — ۱۴:۳۰ */
export const jDateTime = v => `${jDate(v)} — ${jTime(v)}`;
/* شنبه ۲۳ آبان ۱۴۰۵ */
export const jLong = v => fmtLong.format(toDate(v));
export const jYear = (v = new Date()) => fmtYear.format(toDate(v));

/* ---- تبدیل (الگوریتم استاندارد جلالی) ---- */
export function gregorianToJalali(gy, gm, gd) {
  const gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  const gy2 = gm > 2 ? gy + 1 : gy;
  let days = 355666 + 365 * gy + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100) + Math.floor((gy2 + 399) / 400) + gd + gdm[gm - 1];
  let jy = -1595 + 33 * Math.floor(days / 12053);
  days %= 12053;
  jy += 4 * Math.floor(days / 1461);
  days %= 1461;
  if (days > 365) { jy += Math.floor((days - 1) / 365); days = (days - 1) % 365; }
  const jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30);
  const jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30);
  return [jy, jm, jd];
}

export function jalaliToGregorian(jy, jm, jd) {
  jy += 1595;
  let days = -355668 + 365 * jy + Math.floor(jy / 33) * 8 + Math.floor(((jy % 33) + 3) / 4) + jd + (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186);
  let gy = 400 * Math.floor(days / 146097);
  days %= 146097;
  if (days > 36524) { gy += 100 * Math.floor(--days / 36524); days %= 36524; if (days >= 365) days++; }
  gy += 4 * Math.floor(days / 1461);
  days %= 1461;
  if (days > 365) { gy += Math.floor((days - 1) / 365); days = (days - 1) % 365; }
  let gd = days + 1;
  const sal = [0, 31, (gy % 4 === 0 && gy % 100 !== 0) || gy % 400 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let gm = 0;
  for (; gm < 13 && gd > sal[gm]; gm++) gd -= sal[gm];
  return [gy, gm, gd];
}

/* «۱۴۰۵/۱۲/۲۹» (یا با - و .) → 'YYYY-MM-DD' میلادی؛ نامعتبر → null؛ خالی → '' */
export function jalaliInputToIso(text) {
  const t = toEnDigits(text).trim();
  if (!t) return '';
  const m = t.match(/^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})$/);
  if (!m) return null;
  const [jy, jm, jd] = [+m[1], +m[2], +m[3]];
  if (jy < 1300 || jy > 1600 || jm < 1 || jm > 12 || jd < 1 || jd > (jm <= 6 ? 31 : jm <= 11 ? 30 : 30)) return null;
  const [gy, gm, gd] = jalaliToGregorian(jy, jm, jd);
  /* اسفند ۳۰ فقط در سال کبیسه معتبر است: رفت‌وبرگشت بررسی می‌شود */
  const back = gregorianToJalali(gy, gm, gd);
  if (back[0] !== jy || back[1] !== jm || back[2] !== jd) return null;
  return `${gy}-${String(gm).padStart(2, '0')}-${String(gd).padStart(2, '0')}`;
}

/* ISO/تاریخ (سرور) → «۱۴۰۵/۱۲/۲۹» برای فیلد ورودی مدیر؛ خالی → '' */
export function isoToJalaliInput(v) {
  if (!v) return '';
  return jDate(v);
}
