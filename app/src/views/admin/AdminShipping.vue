<template>
  <div class="admin-card">
    <h3 class="ad-h">هزینهٔ ارسال و سقف ارسال رایگان</h3>
    <p class="ad-sub">روش‌ها و هزینه‌ها همان‌جا که مشتری در سبد و تسویه می‌بیند اعمال می‌شود؛ سرور هنگام ثبت سفارش دوباره محاسبه می‌کند.</p>
    <div class="ad-grid" style="max-width:640px;margin-bottom:16px">
      <label class="chk full"><input v-model="freeEnabled" type="checkbox"> ارسال رایگان برای سفارش‌های بالای سقف فعال باشد</label>
      <div class="fld w"><label>سقف ارسال رایگان (تومان)</label><input v-model.number="freeFrom" type="number" min="0" step="50000" :disabled="!freeEnabled"></div>
      <div class="fld w" style="align-self:end"><button class="btn btn-brand btn-sm" :disabled="busy" @click="saveSettings">ذخیرهٔ سقف ارسال رایگان</button></div>
    </div>

    <div class="admin-toolbar">
      <b style="font-size:.9rem">روش‌های ارسال</b>
      <button class="btn btn-gold btn-sm" @click="startNew"><svg class="icon"><use href="#i-plus" /></svg> روش ارسال جدید</button>
    </div>
    <div class="tbl-wrap">
      <table class="tbl">
        <thead><tr><th>عنوان</th><th>هزینه</th><th>زمان تحویل</th><th>ترتیب</th><th>وضعیت</th><th></th></tr></thead>
        <tbody>
          <tr v-for="m in methods" :key="m.id">
            <td><b>{{ m.label }}</b><small style="display:block;color:var(--ink-3)" dir="ltr">{{ m.type }}</small></td>
            <td>{{ m.cost ? money(m.cost) + ' تومان' : 'رایگان' }}</td>
            <td>{{ m.days || '—' }}</td>
            <td>{{ toFa(m.sort) }}</td>
            <td><span class="tag" :class="m.active ? 'green' : 'red'">{{ m.active ? 'فعال' : 'غیرفعال' }}</span></td>
            <td class="td-acts">
              <button class="btn btn-light btn-sm" @click="edit(m)">ویرایش</button>
              <button class="btn btn-light btn-sm" @click="toggle(m)">{{ m.active ? 'غیرفعال' : 'فعال' }}</button>
              <button class="btn btn-light btn-sm del" @click="remove(m)">حذف</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="overlay" :class="{ open: !!ed }" @click.self="ed = null">
      <div class="modal" style="width:min(520px,100%)">
        <div class="modal-head"><b><svg class="icon"><use href="#i-truck" /></svg> {{ ed && ed.id ? 'ویرایش روش ارسال' : 'روش ارسال جدید' }}</b><button class="modal-x" aria-label="بستن" @click="ed = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
        <div class="modal-body" v-if="ed">
          <div class="ad-grid">
            <div class="fld w full"><label>عنوان *</label><input v-model="ed.label" type="text" maxlength="120" placeholder="مثلاً پیک موتوری (تهران)"></div>
            <div class="fld w"><label>شناسه (انگلیسی) *</label><input v-model="ed.type" type="text" dir="ltr" maxlength="20" :disabled="!!ed.id" placeholder="bike"></div>
            <div class="fld w"><label>هزینه (تومان) *</label><input v-model.number="ed.cost" type="number" min="0" step="1000"></div>
            <div class="fld w"><label>زمان تحویل</label><input v-model="ed.days" type="text" maxlength="60" placeholder="۲ تا ۴ روز کاری"></div>
            <div class="fld w"><label>ترتیب نمایش</label><input v-model.number="ed.sort" type="number" min="0"></div>
            <div class="fld w full"><label>توضیح کوتاه (زیر عنوان)</label><input v-model="ed.hint" type="text" maxlength="120"></div>
            <label class="chk full"><input v-model="ed.active" type="checkbox"> فعال (قابل انتخاب برای مشتری)</label>
          </div>
          <button class="btn btn-brand btn-block" style="margin-top:12px" :disabled="busy" @click="save">ذخیره</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { toFa, money } from '../../data/site';
import { apiCall } from '../../services/api';
import { toast } from '../../stores/ui';
import { loadShop } from '../../stores/shop';
import '../../assets/admin.css';

const methods = ref([]);
const freeFrom = ref(1500000);
const freeEnabled = ref(true);
const ed = ref(null);
const busy = ref(false);

async function load() {
  const r = await apiCall('/admin/shipping');
  if (!r.ok) return toast(r.msg || 'دریافت روش‌های ارسال انجام نشد', 'err');
  methods.value = r.methods; freeFrom.value = r.freeFrom; freeEnabled.value = r.freeEnabled;
}
async function done(msg) { toast(msg, 'ok'); await load(); loadShop(); }

async function saveSettings() {
  busy.value = true;
  const r = await apiCall('/admin/shipping/settings', { method: 'PUT', body: { freeFrom: freeFrom.value || 0, freeEnabled: freeEnabled.value } });
  busy.value = false;
  r.ok ? done('سقف ارسال رایگان ذخیره شد ✅') : toast(r.msg, 'err');
}
function startNew() { ed.value = { id: 0, type: '', label: '', cost: 0, days: '', hint: '', sort: methods.value.length, active: true }; }
function edit(m) { ed.value = { ...m }; }
async function save() {
  const e = ed.value;
  busy.value = true;
  const body = { type: e.type, label: e.label, cost: e.cost || 0, days: e.days, hint: e.hint, sort: e.sort || 0, active: e.active };
  const r = await apiCall(e.id ? '/admin/shipping/' + e.id : '/admin/shipping', { method: e.id ? 'PUT' : 'POST', body });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  ed.value = null; done('روش ارسال ذخیره شد ✅');
}
async function toggle(m) {
  const r = await apiCall('/admin/shipping/' + m.id, { method: 'PUT', body: { active: !m.active } });
  r.ok ? done(m.active ? 'روش غیرفعال شد' : 'روش فعال شد') : toast(r.msg, 'err');
}
async function remove(m) {
  if (!window.confirm(`روش «${m.label}» حذف شود؟`)) return;
  const r = await apiCall('/admin/shipping/' + m.id, { method: 'DELETE' });
  r.ok ? done('روش حذف شد') : toast(r.msg, 'err');
}
onMounted(load);
</script>
