<template>
  <div class="imgf">
    <div class="imgf-row">
      <div class="imgf-prev"><img v-if="modelValue" :src="imgSrc(modelValue)" alt=""><span v-else>بدون تصویر</span></div>
      <div class="imgf-ctl">
        <input :value="modelValue" type="text" class="fld" dir="ltr" placeholder="media/… یا img/… یا https://…" @input="$emit('update:modelValue', $event.target.value.trim())">
        <div class="imgf-btns">
          <label class="btn btn-gold btn-sm" :class="{ disabled: busy }">{{ busy ? 'در حال آپلود…' : '⬆ آپلود تصویر' }}
            <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" hidden :disabled="busy" @change="onFile">
          </label>
          <button type="button" class="btn btn-light btn-sm" @click="openLib">انتخاب از کتابخانه</button>
          <button v-if="modelValue" type="button" class="btn btn-light btn-sm del" @click="$emit('update:modelValue', '')">حذف تصویر</button>
        </div>
      </div>
    </div>
    <div class="overlay" :class="{ open: lib }" @click.self="lib = false">
      <div class="modal" style="width:min(720px,100%)">
        <div class="modal-head"><b>کتابخانهٔ تصاویر</b><button class="modal-x" type="button" aria-label="بستن" @click="lib = false"><svg class="icon"><use href="#i-x" /></svg></button></div>
        <div class="modal-body">
          <div v-if="!files.length" class="up-empty"><p>تصویری آپلود نشده است؛ از دکمهٔ «آپلود تصویر» استفاده کنید.</p></div>
          <div v-else class="imgf-grid">
            <button v-for="f in files" :key="f.id" type="button" class="imgf-it" @click="pick(f.path)"><img :src="imgSrc(f.path)" alt="" loading="lazy"><small>{{ f.original }}</small></button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { imgSrc, apiUpload, apiCall } from '../services/api';
import { toast } from '../stores/ui';

defineProps({ modelValue: { type: String, default: '' } });
const emit = defineEmits(['update:modelValue']);
const busy = ref(false);
const lib = ref(false);
const files = ref([]);

async function onFile(e) {
  const f = e.target.files && e.target.files[0];
  e.target.value = '';
  if (!f) return;
  busy.value = true;
  const r = await apiUpload(f);
  busy.value = false;
  if (!r.ok) return toast(r.msg || 'آپلود انجام نشد', 'err');
  emit('update:modelValue', r.file.path);
  toast('تصویر آپلود شد ✅', 'ok');
}
async function openLib() {
  const r = await apiCall('/admin/media');
  files.value = r.ok ? r.files : [];
  lib.value = true;
}
function pick(p) { emit('update:modelValue', p); lib.value = false; }
</script>

<style scoped>
.imgf-row{display:grid;grid-template-columns:96px 1fr;gap:12px;align-items:start}
.imgf-prev{width:96px;height:96px;border-radius:14px;border:1px dashed var(--line);background:var(--bg-warm);display:grid;place-items:center;overflow:hidden;font-size:.68rem;color:var(--ink-3)}
.imgf-prev img{width:100%;height:100%;object-fit:cover}
.imgf-ctl{display:grid;gap:8px}
.imgf-btns{display:flex;gap:6px;flex-wrap:wrap}
label.btn.disabled{opacity:.55;pointer-events:none}
.imgf-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px}
.imgf-it{border:1px solid var(--line);border-radius:12px;background:#fff;padding:6px;cursor:pointer;display:grid;gap:4px;font-family:inherit}
.imgf-it:hover{border-color:var(--brand)}
.imgf-it img{width:100%;aspect-ratio:1;object-fit:cover;border-radius:8px}
.imgf-it small{font-size:.64rem;color:var(--ink-3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
</style>
