<template>
  <div class="admin-card">
    <h3 class="ad-h">کتابخانهٔ تصاویر</h3>
    <p class="ad-sub">تصاویر روی خود سرور شما ذخیره می‌شوند (JPG، PNG، WebP، GIF تا ۴ مگابایت). مسیر هر تصویر را در محصول، بنر، پک و خرید اطمینان هم می‌توانید مستقیم انتخاب کنید.</p>
    <div class="admin-toolbar">
      <label class="btn btn-gold btn-sm" :class="{ disabled: busy }">{{ busy ? 'در حال آپلود…' : '⬆ آپلود تصویر (چندتایی)' }}
        <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" multiple hidden :disabled="busy" @change="onFiles">
      </label>
      <button class="btn btn-light btn-sm" @click="load">به‌روزرسانی ⟳</button>
      <span class="sync-chip on">{{ toFa(files.length) }} تصویر · {{ totalMb }} مگابایت</span>
    </div>
    <div v-if="!files.length" class="up-empty"><svg class="icon"><use href="#i-box" /></svg><p>هنوز تصویری آپلود نشده است.</p></div>
    <div v-else class="mg">
      <div v-for="f in files" :key="f.id" class="mg-it">
        <img :src="imgSrc(f.path)" alt="" loading="lazy">
        <small dir="ltr">{{ f.path }}</small>
        <small>{{ f.original }} · {{ kb(f.size) }}</small>
        <div class="mg-btns">
          <button class="btn btn-light btn-sm" @click="copy(f.path)">کپی مسیر</button>
          <button class="btn btn-light btn-sm del" @click="remove(f)">حذف</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { toFa } from '../../data/site';
import { imgSrc, apiUpload, apiCall } from '../../services/api';
import { toast } from '../../stores/ui';
import '../../assets/admin.css';

const files = ref([]);
const busy = ref(false);
const kb = n => toFa(Math.max(1, Math.round(n / 1024))) + ' کیلوبایت';
const totalMb = computed(() => toFa((files.value.reduce((s, f) => s + f.size, 0) / 1048576).toFixed(1)));

async function load() {
  const r = await apiCall('/admin/media');
  if (r.ok) files.value = r.files; else toast(r.msg || 'دریافت تصاویر انجام نشد', 'err');
}
async function onFiles(e) {
  const list = [...(e.target.files || [])];
  e.target.value = '';
  busy.value = true;
  let ok = 0;
  for (const f of list) {
    const r = await apiUpload(f);
    if (r.ok) ok++; else toast(`«${f.name}»: ${r.msg}`, 'err', 5000);
  }
  busy.value = false;
  if (ok) toast(`${toFa(ok)} تصویر آپلود شد ✅`, 'ok');
  load();
}
function copy(p) {
  const done = () => toast('مسیر کپی شد', 'ok');
  if (navigator.clipboard) navigator.clipboard.writeText(p).then(done, done); else done();
}
async function remove(f) {
  if (!window.confirm('این تصویر حذف شود؟ اگر جایی استفاده شده باشد دیگر نمایش داده نمی‌شود.')) return;
  const r = await apiCall('/admin/media/' + f.id, { method: 'DELETE' });
  r.ok ? load() : toast(r.msg, 'err');
}
onMounted(load);
</script>

<style scoped>
.mg{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}
.mg-it{border:1px solid var(--line);border-radius:14px;padding:8px;display:grid;gap:5px;background:#fff}
.mg-it img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:10px;background:var(--bg-warm)}
.mg-it small{font-size:.66rem;color:var(--ink-3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mg-btns{display:flex;gap:6px}
label.btn.disabled{opacity:.55;pointer-events:none}
</style>
