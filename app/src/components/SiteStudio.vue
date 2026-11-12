<template>
  <div v-if="auth.isAdmin" :class="inline ? 'ss-inline' : 'ss-float'" :data-open="inline || open ? '1' : '0'">
    <div class="ss-panel" role="dialog" aria-label="تنظیم قالب و رنگ سایت">
      <div class="ss-h">🎨 قالب و رنگ سایت <small>(فقط مدیر؛ برای همهٔ بازدیدکنندگان اعمال می‌شود)</small></div>
      <div class="ss-themes">
        <button v-for="t in THEMES" :key="t.id" type="button" class="ss-dot" :class="{ on: draftTheme === t.id }"
          :title="t.name" :aria-label="t.name" @click="choose(t.id)"><i :style="{ background: t.color }"></i></button>
      </div>
      <div class="ss-row">
        <button type="button" @click="shift(2)">☀️ روشن‌تر</button>
        <button type="button" @click="shift(-2)">🌙 تیره‌تر</button>
      </div>
      <div class="ss-chips">
        <span v-for="(h, i) in shown" :key="i" class="ss-chip" :title="h"><i :style="{ background: h }"></i><b>{{ h }}</b></span>
      </div>
      <div class="ss-act">
        <button type="button" class="ss-save" :disabled="saving || !dirty" @click="save">{{ saving ? 'در حال ذخیره…' : 'ذخیره برای کل سایت' }}</button>
        <button type="button" class="ss-cancel" :disabled="!dirty" @click="cancel">انصراف</button>
      </div>
    </div>
    <button v-if="!inline" type="button" class="ss-btn" aria-label="تنظیم قالب و رنگ سایت" @click="toggle">🎨</button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { auth } from '../stores/auth';
import { look, applyLook, saveLook } from '../stores/ui';
import { THEMES } from '../data/catalog';
import { shiftHex } from '../data/color';

defineProps({ inline: { type: Boolean, default: false } });

const KEYS = ['--brand', '--brand-600', '--brand-700', '--brand-800'];
const open = ref(false);
const saving = ref(false);
const draftTheme = ref(look.theme);
const draftTune = ref(look.tune ? [...look.tune] : null);

const dirty = computed(() => draftTheme.value !== look.theme || JSON.stringify(draftTune.value) !== JSON.stringify(look.tune));

/* رنگ‌های پایهٔ یک تم (بدون تنظیم دستی) از CSS محاسبه‌شده */
function baseColors(themeId) {
  const root = document.documentElement;
  const prevTheme = root.dataset.theme;
  const prevVars = KEYS.map(k => root.style.getPropertyValue(k));
  KEYS.forEach(k => root.style.removeProperty(k));
  if (themeId && themeId !== 'default') root.dataset.theme = themeId; else delete root.dataset.theme;
  const cs = getComputedStyle(root);
  const out = KEYS.map(k => cs.getPropertyValue(k).trim());
  if (prevTheme) root.dataset.theme = prevTheme; else delete root.dataset.theme;
  KEYS.forEach((k, i) => prevVars[i] ? root.style.setProperty(k, prevVars[i]) : null);
  return out;
}

const shown = computed(() => {
  void draftTheme.value; void draftTune.value;
  return draftTune.value || baseColors(draftTheme.value);
});

const preview = () => applyLook({ theme: draftTheme.value, tune: draftTune.value });
function choose(id) { draftTheme.value = id; draftTune.value = null; preview(); }
function shift(d) {
  const cur = draftTune.value || baseColors(draftTheme.value);
  draftTune.value = cur.map(h => shiftHex(h, d));
  preview();
}
function cancel() { draftTheme.value = look.theme; draftTune.value = look.tune ? [...look.tune] : null; applyLook(); }
async function save() {
  saving.value = true;
  const ok = await saveLook(draftTheme.value, draftTune.value);
  saving.value = false;
  if (ok) { open.value = false; }
}
function toggle() { open.value = !open.value; if (!open.value) cancel(); }

/* خروج مدیر یا تغییر ظاهر از بیرون: پیش‌نمایش ذخیره‌نشده را برگردان */
watch(() => auth.isAdmin, v => { if (!v) { open.value = false; applyLook(); } });
watch(() => [look.theme, look.tune], () => { if (!dirty.value) cancel(); });
</script>

<style scoped>
.ss-float{position:fixed;inset-inline-end:14px;bottom:18px;z-index:9990}
.ss-btn{width:52px;height:52px;border-radius:16px;border:0;background:var(--brand);color:#fff;font-size:23px;display:grid;place-items:center;cursor:pointer;box-shadow:0 8px 22px rgba(30,43,22,.35);transition:transform .2s ease}
.ss-btn:hover{transform:translateY(-2px)}
.ss-float .ss-panel{position:absolute;bottom:calc(100% + 10px);inset-inline-end:0;width:min(330px,88vw);display:none}
.ss-float[data-open="1"] .ss-panel{display:block;animation:fadeUp .22s ease}
.ss-panel{background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:0 24px 60px rgba(30,43,22,.25);padding:14px 15px}
.ss-inline .ss-panel{max-width:420px;box-shadow:var(--sh-sm)}
.ss-h{font-size:.88rem;font-weight:800;color:var(--ink);margin-bottom:10px}
.ss-h small{display:block;font-weight:600;color:var(--ink-3);font-size:.7rem;margin-top:2px}
.ss-themes{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-bottom:10px}
.ss-dot{display:grid;place-items:center;height:38px;border-radius:11px;border:1.5px solid var(--line);background:#fff;cursor:pointer;position:relative}
.ss-dot i{width:20px;height:20px;border-radius:50%;display:block}
.ss-dot.on{border-color:var(--gold);box-shadow:0 0 0 3px var(--gold-100)}
.ss-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px}
.ss-row button{border:1.5px solid var(--line);background:var(--bg-warm);border-radius:11px;padding:8px 6px;font-size:.78rem;font-weight:700;cursor:pointer;font-family:inherit;color:var(--ink-2)}
.ss-row button:hover{border-color:var(--brand);color:var(--brand-700)}
.ss-chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.ss-chip{display:flex;align-items:center;gap:5px;background:var(--bg-warm);border:1px solid var(--line);border-radius:9px;padding:3px 7px}
.ss-chip i{width:14px;height:14px;border-radius:5px;border:1px solid rgba(0,0,0,.1)}
.ss-chip b{font-size:.68rem;direction:ltr;font-family:monospace;color:var(--ink-2)}
.ss-act{display:grid;grid-template-columns:2fr 1fr;gap:8px}
.ss-save{border:0;background:var(--brand);color:#fff;border-radius:12px;padding:10px;font-size:.82rem;font-weight:800;cursor:pointer;font-family:inherit}
.ss-save:disabled{opacity:.45;cursor:default}
.ss-cancel{border:1.5px solid var(--line);background:#fff;border-radius:12px;padding:9px;font-size:.78rem;font-weight:700;cursor:pointer;font-family:inherit;color:var(--ink-3)}
.ss-cancel:disabled{opacity:.45;cursor:default}
@media(max-width:767px){.ss-float{bottom:82px}}
@media print{.ss-float{display:none!important}}
</style>
