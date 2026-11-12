<template>
  <div class="admin-card">
    <h3 class="ad-h">کارت شانس</h3>
    <p class="ad-sub">جایزه روی حساب کاربر و در سرور تعیین می‌شود و به‌صورت یک کد شخصی و یک‌بارمصرف صادر می‌شود. هر کاربر در بازهٔ زیر فقط یک‌بار می‌تواند کارت را باز کند.</p>
    <div class="ad-grid" style="max-width:700px;margin-bottom:16px">
      <label class="chk full"><input v-model="cfg.enabled" type="checkbox"> کارت شانس فعال باشد</label>
      <div class="fld w"><label>فاصلهٔ بین دو چرخش هر کاربر (ساعت)</label><input v-model.number="cfg.cooldownHours" type="number" min="1" max="2160"></div>
      <div class="fld w"><label>مهلت استفاده از جایزه (روز)</label><input v-model.number="cfg.validDays" type="number" min="1" max="365"></div>
      <div class="fld w"><button class="btn btn-brand btn-sm" :disabled="busy" @click="saveCfg">ذخیرهٔ تنظیمات</button></div>
    </div>

    <div class="admin-toolbar">
      <b style="font-size:.9rem">جایزه‌ها</b>
      <button class="btn btn-gold btn-sm" @click="startNew"><svg class="icon"><use href="#i-plus" /></svg> جایزهٔ جدید</button>
      <span class="sync-chip on">مجموع {{ toFa(totalPrizeWeight) }} وزن — شانس هر جایزه = وزن ÷ مجموع</span>
    </div>
    <div class="tbl-wrap">
      <table class="tbl">
        <thead><tr><th>عنوان</th><th>نوع</th><th>حداقل خرید</th><th>وزن (شانس)</th><th>وضعیت</th><th></th></tr></thead>
        <tbody>
          <tr v-for="p in prizes" :key="p.id">
            <td><b>{{ p.title }}</b><small style="display:block;color:var(--ink-3)">{{ p.desc }}</small></td>
            <td>{{ kindLabel(p) }}</td>
            <td>{{ p.min ? money(p.min) : '—' }}</td>
            <td>{{ toFa(p.weight) }} ({{ toFa(chance(p)) }}٪)</td>
            <td><span class="tag" :class="p.active ? 'green' : 'red'">{{ p.active ? 'فعال' : 'غیرفعال' }}</span></td>
            <td class="td-acts">
              <button class="btn btn-light btn-sm" @click="ed = { ...p }">ویرایش</button>
              <button class="btn btn-light btn-sm" @click="togglePrize(p)">{{ p.active ? 'غیرفعال' : 'فعال' }}</button>
              <button class="btn btn-light btn-sm del" @click="removePrize(p)">حذف</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <h3 class="ad-h" style="margin-top:20px">آخرین برنده‌ها ({{ toFa(totalWins) }} چرخش)</h3>
    <div v-if="!wins.length" class="up-empty"><svg class="icon"><use href="#i-gift" /></svg><p>هنوز کسی کارت شانس را باز نکرده است.</p></div>
    <div v-else class="tbl-wrap">
      <table class="tbl">
        <thead><tr><th>کاربر</th><th>جایزه</th><th>کد</th><th>وضعیت کد</th><th>زمان</th></tr></thead>
        <tbody>
          <tr v-for="(w, i) in wins" :key="i">
            <td>{{ w.user }}<small dir="ltr" style="display:block;color:var(--ink-3);text-align:end">{{ toFa(w.phone) }}</small></td>
            <td>{{ w.prize }}</td><td dir="ltr" style="text-align:end"><b>{{ w.code }}</b></td>
            <td><span class="tag" :class="w.used ? 'red' : 'green'">{{ w.used ? 'استفاده شده' : 'استفاده‌نشده' }}</span></td>
            <td style="white-space:nowrap">{{ jDateTime(w.at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="overlay" :class="{ open: !!ed }" @click.self="ed = null">
      <div class="modal" style="width:min(520px,100%)">
        <div class="modal-head"><b><svg class="icon"><use href="#i-gift" /></svg> {{ ed && ed.id ? 'ویرایش جایزه' : 'جایزهٔ جدید' }}</b><button class="modal-x" aria-label="بستن" @click="ed = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
        <div class="modal-body" v-if="ed">
          <div class="ad-grid">
            <div class="fld w full"><label>عنوان *</label><input v-model="ed.title" type="text" maxlength="80" placeholder="مثلاً ۱۰٪ تخفیف ویژه"></div>
            <div class="fld w full"><label>توضیح برای مشتری</label><input v-model="ed.desc" type="text" maxlength="200"></div>
            <div class="fld w"><label>نوع</label>
              <select v-model="ed.type"><option value="pct">درصدی</option><option value="cash">مبلغ ثابت (تومان)</option><option value="ship">ارسال رایگان</option><option value="day">ارسال همان روز</option></select>
            </div>
            <div v-if="ed.type === 'pct' || ed.type === 'cash'" class="fld w"><label>{{ ed.type === 'pct' ? 'درصد' : 'مبلغ (تومان)' }}</label><input v-model.number="ed.val" type="number" min="1"></div>
            <div class="fld w"><label>حداقل مبلغ سفارش (تومان)</label><input v-model.number="ed.min" type="number" min="0" step="10000"></div>
            <div class="fld w"><label>وزن / شانس (۱ تا ۱۰۰)</label><input v-model.number="ed.weight" type="number" min="1" max="100"></div>
            <label class="chk full"><input v-model="ed.active" type="checkbox"> فعال</label>
          </div>
          <button class="btn btn-brand btn-block" style="margin-top:12px" :disabled="busy" @click="savePrize">ذخیرهٔ جایزه</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { toFa, money } from '../../data/site';
import { jDateTime } from '../../data/jalali';
import { apiCall } from '../../services/api';
import { toast } from '../../stores/ui';
import { loadShop } from '../../stores/shop';
import '../../assets/admin.css';

const cfg = reactive({ enabled: true, cooldownHours: 24, validDays: 30 });
const prizes = ref([]);
const wins = ref([]);
const totalWins = ref(0);
const ed = ref(null);
const busy = ref(false);

const totalPrizeWeight = computed(() => prizes.value.filter(p => p.active).reduce((s, p) => s + p.weight, 0));
const chance = p => (p.active && totalPrizeWeight.value ? Math.round(p.weight / totalPrizeWeight.value * 100) : 0);
const kindLabel = p => ({ pct: `${toFa(p.val)}٪ تخفیف`, cash: `${money(p.val)} تومان اعتبار`, ship: 'ارسال رایگان', day: 'ارسال همان روز' }[p.type] || p.type);

async function load() {
  const r = await apiCall('/admin/lucky');
  if (!r.ok) return toast(r.msg || 'دریافت اطلاعات کارت شانس انجام نشد', 'err');
  Object.assign(cfg, r.settings); prizes.value = r.prizes; wins.value = r.wins; totalWins.value = r.totalWins;
}
async function saveCfg() {
  busy.value = true;
  const r = await apiCall('/admin/lucky', { method: 'PUT', body: { enabled: cfg.enabled, cooldownHours: cfg.cooldownHours, validDays: cfg.validDays } });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  toast('تنظیمات کارت شانس ذخیره شد ✅', 'ok'); loadShop();
}
function startNew() { ed.value = { id: 0, title: '', desc: '', type: 'pct', val: 10, min: 0, weight: 10, icon: 'i-gift', active: true }; }
async function savePrize() {
  const e = ed.value;
  busy.value = true;
  const body = { title: e.title, desc: e.desc, type: e.type, val: e.val || 0, min: e.min || 0, weight: e.weight, icon: e.icon, active: e.active };
  const r = await apiCall(e.id ? '/admin/lucky/prizes/' + e.id : '/admin/lucky', { method: e.id ? 'PUT' : 'POST', body });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  ed.value = null; toast('جایزه ذخیره شد ✅', 'ok'); load();
}
async function togglePrize(p) {
  const r = await apiCall('/admin/lucky/prizes/' + p.id, { method: 'PUT', body: { active: !p.active } });
  r.ok ? load() : toast(r.msg, 'err');
}
async function removePrize(p) {
  if (!window.confirm(`جایزهٔ «${p.title}» حذف شود؟`)) return;
  const r = await apiCall('/admin/lucky/prizes/' + p.id, { method: 'DELETE' });
  r.ok ? load() : toast(r.msg, 'err');
}
onMounted(load);
</script>
