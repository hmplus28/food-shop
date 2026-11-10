<template>
  <div id="brandTuner" :class="{ open }">
    <div class="bt-panel">
      <div class="bt-h">🎛 تنظیم سبز برند <small>(ابزار موقت)</small></div>
      <p class="bt-p">روشنایی را تا رسیدن به رنگ دلخواه کم و زیاد کنید؛ بعد «کپی کد» را بزنید و کد را برای من بفرستید تا دقیقاً همان را در قالب اصلی (HTML و Vue) اعمال کنم.</p>
      <div class="bt-row">
        <button type="button" @click="shift(2)">☀️ روشن‌تر (+۲)</button>
        <button type="button" @click="shift(-2)">🌙 تیره‌تر (−۲)</button>
        <button type="button" @click="shift(1)">＋۱ نرم</button>
        <button type="button" @click="shift(-1)">−۱ نرم</button>
      </div>
      <div class="bt-chips">
        <button v-for="(h, i) in cur" :key="keys[i]" type="button" class="bt-chip" title="کلیک = کپی" @click="copy(h)">
          <i :style="{ background: h }"></i>
          <small>{{ labels[i] }}</small>
          <b>{{ h }}</b>
        </button>
      </div>
      <button type="button" class="bt-copy" @click="copyCode">📋 کپی کد برای ارسال</button>
      <button type="button" class="bt-reset" @click="reset">بازگشت به رنگ فعلی قالب</button>
    </div>
    <button type="button" class="bt-btn" aria-label="تنظیم سبز برند (موقت)" @click="open = !open">🎨</button>
  </div>
</template>

<script setup>
/* ابزار موقت تنظیم روشنایی سبز برند — هم‌رفتار و هم‌کلید با نسخهٔ HTML.
   کد کپی‌شده (مثل ‎--brand:#48b500; …) را کاربر می‌فرستد و همان در سورس
   اصلی هر دو نسخه اعمال و این ابزار حذف می‌شود. */
import { ref, onMounted } from 'vue';
import { toast } from '../stores/ui';

const keys = ['--brand', '--brand-600', '--brand-700', '--brand-800'];
const labels = ['اصلی', '۶۰۰', '۷۰۰', '۸۰۰'];
const STORE_KEY = 'asalat_brandtune';          // هم‌نام با نسخهٔ HTML

const open = ref(false);
const cur = ref(['', '', '', '']);
let base = [];

/* hex → [r,g,b] و برعکس */
const h2rgb = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const clamp01 = v => Math.max(0, Math.min(1, v));

function rgb2hsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
  let h = 0; const l = (mx + mn) / 2, d = mx - mn;
  const s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
  if (d !== 0) {
    if (mx === r) h = ((g - b) / d) % 6;
    else if (mx === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60; if (h < 0) h += 360;
  }
  return [h, s, l];
}

function hsl2rgb(h, s, l) {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs((h / 60) % 2 - 1));
  const m = l - c / 2;
  let r, g, b;
  if (h < 60) { r = c; g = x; b = 0 }
  else if (h < 120) { r = x; g = c; b = 0 }
  else if (h < 180) { r = 0; g = c; b = x }
  else if (h < 240) { r = 0; g = x; b = c }
  else if (h < 300) { r = x; g = 0; b = c }
  else { r = c; g = 0; b = x }
  return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
}

function shiftHex(hex, delta) {
  const [r, g, b] = h2rgb(hex);
  const [h, s, l] = rgb2hsl(r, g, b);
  const [nr, ng, nb] = hsl2rgb(h, s, clamp01(l + delta / 100));
  return '#' + [nr, ng, nb].map(v => ('0' + v.toString(16)).slice(-2)).join('');
}

function shift(delta) {
  cur.value = cur.value.map(hex => shiftHex(hex, delta));
  apply(); persist();
}

function apply() {
  keys.forEach((k, i) => document.documentElement.style.setProperty(k, cur.value[i]));
}

function persist() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(cur.value)); } catch (e) {}
}

function reset() {
  cur.value = base.slice();
  try { localStorage.removeItem(STORE_KEY); } catch (e) {}
  keys.forEach(k => document.documentElement.style.removeProperty(k));
  toast('به رنگ فعلی قالب برگشت', 'gold');
}

function copy(t) {
  const ok = () => toast('کد کپی شد ✅', 'gold');
  const fallback = () => {
    const ta = document.createElement('textarea');
    ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); ok(); } catch (e) { toast('کپی نشد؛ کد را دستی بردارید', 'err'); }
    document.body.removeChild(ta);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(ok, fallback);
  else fallback();
}

const copyCode = () => copy(keys.map((k, i) => k + ':' + cur.value[i]).join('; ') + ';');

onMounted(() => {
  base = keys.map(k => getComputedStyle(document.documentElement).getPropertyValue(k).trim());
  cur.value = base.slice();
  try {
    const s = localStorage.getItem(STORE_KEY);
    if (s) {
      const a = JSON.parse(s);
      if (Array.isArray(a) && a.length === 4 && a.every(h => /^#[0-9a-f]{6}$/i.test(h))) cur.value = a;
    }
  } catch (e) {}
  apply();
});
</script>

<style scoped>
#brandTuner{position:fixed;inset-inline-end:14px;bottom:18px;z-index:9990}
#brandTuner .bt-btn{width:52px;height:52px;border-radius:16px;border:0;background:var(--brand);color:#fff;font-size:23px;display:grid;place-items:center;cursor:pointer;box-shadow:0 8px 22px rgba(72,181,0,.4);transition:transform .2s ease}
#brandTuner .bt-btn:hover{transform:translateY(-2px)}
#brandTuner .bt-panel{position:absolute;bottom:calc(100% + 10px);inset-inline-end:0;width:min(320px,88vw);background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:0 24px 60px rgba(30,43,22,.25);padding:14px 15px;display:none}
#brandTuner.open .bt-panel{display:block;animation:fadeUp .22s ease}
#brandTuner .bt-h{font-size:.85rem;font-weight:800;color:var(--ink);margin-bottom:3px}
#brandTuner .bt-h small{font-weight:600;color:var(--gold-600);font-size:.7rem}
#brandTuner .bt-p{font-size:.7rem;color:var(--ink-3);line-height:1.9;margin-bottom:10px}
#brandTuner .bt-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px}
#brandTuner .bt-row button{border:1.5px solid var(--line);background:var(--bg-warm);border-radius:11px;padding:8px 6px;font-size:.76rem;font-weight:700;cursor:pointer;font-family:inherit;color:var(--ink-2);transition:var(--tr)}
#brandTuner .bt-row button:hover{border-color:var(--brand);color:var(--brand-700);background:var(--brand-soft)}
#brandTuner .bt-chips{display:grid;gap:6px;margin-bottom:10px}
#brandTuner .bt-chip{display:flex;align-items:center;gap:8px;background:var(--bg-warm);border:1px solid var(--line);border-radius:11px;padding:6px 9px;cursor:pointer;transition:var(--tr);font-family:inherit;text-align:start}
#brandTuner .bt-chip:hover{border-color:var(--brand)}
#brandTuner .bt-chip i{width:20px;height:20px;border-radius:7px;flex:none;border:1px solid rgba(0,0,0,.08)}
#brandTuner .bt-chip small{font-size:.68rem;color:var(--ink-3)}
#brandTuner .bt-chip b{margin-inline-start:auto;font-size:.74rem;direction:ltr;color:var(--ink-2);font-family:monospace;font-weight:700}
#brandTuner .bt-copy{width:100%;border:0;background:var(--brand);color:#fff;border-radius:12px;padding:11px;font-size:.82rem;font-weight:800;cursor:pointer;font-family:inherit;transition:var(--tr)}
#brandTuner .bt-copy:hover{background:var(--brand-600)}
#brandTuner .bt-reset{width:100%;border:1.5px solid var(--line);background:#fff;border-radius:12px;padding:9px;font-size:.75rem;font-weight:700;cursor:pointer;margin-top:7px;color:var(--ink-3);font-family:inherit}
#brandTuner .bt-reset:hover{color:var(--red);border-color:var(--red)}
@media(max-width:767px){#brandTuner{bottom:82px}}
@media print{#brandTuner{display:none!important}}
</style>
