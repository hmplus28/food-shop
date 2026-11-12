<template>
  <div class="admin-card">
    <div class="subtabs">
      <button :class="{ on: sub === 'banners' }" @click="sub = 'banners'">بنر اصلی</button>
      <button :class="{ on: sub === 'packs' }" @click="sub = 'packs'">پک‌های تخفیفی</button>
      <button :class="{ on: sub === 'trust' }" @click="sub = 'trust'">خرید اطمینان</button>
      <button :class="{ on: sub === 'sections' }" @click="sub = 'sections'">بخش‌ها، عناوین و ترتیب</button>
    </div>

    <!-- ===== بنرها ===== -->
    <div v-if="sub === 'banners'">
      <p class="ad-sub">اسلایدهای بالای صفحهٔ اصلی. اگر بیش از یک بنر فعال باشد، به‌صورت خودکار می‌چرخند.</p>
      <div class="admin-toolbar"><button class="btn btn-gold btn-sm" @click="ban = blankBanner()"><svg class="icon"><use href="#i-plus" /></svg> بنر جدید</button></div>
      <div v-if="!banners.length" class="up-empty"><p>بنری تعریف نشده است؛ بالای صفحهٔ اصلی خالی می‌ماند.</p></div>
      <div v-else class="tbl-wrap"><table class="tbl">
        <thead><tr><th>تصویر</th><th>عنوان</th><th>دکمه‌ها</th><th>ترتیب</th><th>وضعیت</th><th></th></tr></thead>
        <tbody><tr v-for="b in banners" :key="b.id">
          <td><img class="th" :src="imgSrc(b.image)" alt=""></td>
          <td><b>{{ b.title }} <i v-if="b.titleEm">{{ b.titleEm }}</i></b><small style="display:block;color:var(--ink-3)">{{ b.tag }}</small></td>
          <td class="td-items">{{ [b.cta1.label, b.cta2.label].filter(Boolean).join(' | ') || '—' }}</td>
          <td>{{ toFa(b.sort) }}</td>
          <td><span class="tag" :class="b.active ? 'green' : 'red'">{{ b.active ? 'نمایش' : 'مخفی' }}</span></td>
          <td class="td-acts"><button class="btn btn-light btn-sm" @click="ban = JSON.parse(JSON.stringify(b))">ویرایش</button>
            <button class="btn btn-light btn-sm" @click="toggleBanner(b)">{{ b.active ? 'مخفی' : 'نمایش' }}</button>
            <button class="btn btn-light btn-sm del" @click="delBanner(b)">حذف</button></td>
        </tr></tbody></table></div>
    </div>

    <!-- ===== پک‌ها ===== -->
    <div v-else-if="sub === 'packs'">
      <p class="ad-sub">هر پک قیمت و موجودی خودش را دارد و شمارش معکوسش روی سرور است؛ برای همهٔ بازدیدکنندگان یکسان است. پک «چرخه‌ای» پس از پایان خودکار دوباره از اول شروع می‌شود.</p>
      <div class="admin-toolbar"><button class="btn btn-gold btn-sm" @click="pk = blankPack()"><svg class="icon"><use href="#i-plus" /></svg> پک جدید</button></div>
      <div v-if="!packs.length" class="up-empty"><p>پکی تعریف نشده است.</p></div>
      <div v-else class="tbl-wrap"><table class="tbl">
        <thead><tr><th>پک</th><th>قیمت</th><th>شمارش معکوس</th><th>موجودی</th><th>وضعیت</th><th></th></tr></thead>
        <tbody><tr v-for="p in packs" :key="p.id">
          <td class="td-p"><img class="th" :src="imgSrc(p.image)" alt=""><div><b>{{ p.name }}</b><small style="display:block;color:var(--ink-3)">{{ p.sub }}</small></div></td>
          <td><del style="color:var(--ink-3)">{{ money(p.old) }}</del> <b>{{ money(p.now) }}</b></td>
          <td>{{ p.cycleHours ? 'هر ' + toFa(p.cycleHours) + ' ساعت' : 'تاریخ ثابت' }}<small style="display:block;color:var(--ink-3)">پایان: {{ p.endsAt ? jDateTime(p.endsAt) : 'تمام شده' }}</small></td>
          <td><span class="tag" :class="p.stock > 0 ? 'green' : 'red'">{{ toFa(p.stock) }}</span></td>
          <td><span class="tag" :class="p.active ? 'green' : 'red'">{{ p.active ? 'نمایش' : 'مخفی' }}</span></td>
          <td class="td-acts"><button class="btn btn-light btn-sm" @click="editPack(p)">ویرایش</button>
            <button v-if="p.cycleHours" class="btn btn-light btn-sm" @click="restartPack(p)">شروع مجدد شمارش</button>
            <button class="btn btn-light btn-sm del" @click="delPack(p)">حذف</button></td>
        </tr></tbody></table></div>
    </div>

    <!-- ===== خرید اطمینان ===== -->
    <div v-else-if="sub === 'trust'">
      <p class="ad-sub">برای هر روز هفته یک کالای منتخب؛ مشتری همان روز را به‌عنوان «پیشنهاد امروز» می‌بیند و می‌تواند روزهای دیگر را هم ببیند. متن «چرا این‌جا؟» و عناوین از تب «بخش‌ها» ویرایش می‌شود.</p>
      <div class="admin-toolbar"><button class="btn btn-gold btn-sm" @click="tr = blankTrust()"><svg class="icon"><use href="#i-plus" /></svg> کالای جدید</button></div>
      <div class="tbl-wrap"><table class="tbl">
        <thead><tr><th>روز</th><th>کالا</th><th>قیمت</th><th>موجودی</th><th>وضعیت</th><th></th></tr></thead>
        <tbody><tr v-for="t in trust" :key="t.id">
          <td><b>{{ DAY_NAMES[t.day] }}</b></td>
          <td class="td-p"><img class="th" :src="imgSrc(t.image)" alt=""><b>{{ t.name }}</b></td>
          <td><del style="color:var(--ink-3)">{{ money(t.old) }}</del> <b>{{ money(t.price) }}</b></td>
          <td><span class="tag" :class="t.stock > 0 ? 'green' : 'red'">{{ toFa(t.stock) }}</span></td>
          <td><span class="tag" :class="t.active ? 'green' : 'red'">{{ t.active ? 'نمایش' : 'مخفی' }}</span></td>
          <td class="td-acts"><button class="btn btn-light btn-sm" @click="editTrust(t)">ویرایش</button><button class="btn btn-light btn-sm del" @click="delTrust(t)">حذف</button></td>
        </tr></tbody></table></div>
    </div>

    <!-- ===== بخش‌ها ===== -->
    <div v-else>
      <p class="ad-sub">ترتیب بخش‌های صفحهٔ اصلی، روشن/خاموش بودن هر بخش، و عنوان/توضیح‌هایشان. «بنر اصلی» همیشه بالاست.</p>
      <div v-for="(key, idx) in cfg.order" :key="key" class="sec-box">
        <div class="sec-box-h">
          <b>{{ LABELS[key] }}</b>
          <span class="sec-box-btns">
            <button class="btn btn-light btn-sm" :disabled="idx === 0" @click="move(idx, -1)">▲</button>
            <button class="btn btn-light btn-sm" :disabled="idx === cfg.order.length - 1" @click="move(idx, 1)">▼</button>
          </span>
          <label class="chk"><input v-model="cfg[key].on" type="checkbox"> نمایش</label>
        </div>
        <div class="ad-grid">
          <div v-if="'title' in cfg[key]" class="fld w"><label>عنوان</label><input v-model="cfg[key].title" type="text" maxlength="80"></div>
          <div v-if="'titleEm' in cfg[key]" class="fld w"><label>بخش رنگی عنوان</label><input v-model="cfg[key].titleEm" type="text" maxlength="60"></div>
          <div v-if="'titleTail' in cfg[key]" class="fld w"><label>ادامهٔ عنوان</label><input v-model="cfg[key].titleTail" type="text" maxlength="80"></div>
          <div v-if="'sub' in cfg[key]" class="fld w full"><label>توضیح زیر عنوان</label><input v-model="cfg[key].sub" type="text" maxlength="200"></div>
          <template v-if="key === 'amazing'">
            <div class="fld w"><label>برچسب (مثلاً تا ٪۳۰)</label><input v-model="cfg.amazing.badge" type="text" maxlength="40"></div>
            <div class="fld w full"><label>متن کنار شمارنده</label><input v-model="cfg.amazing.text" type="text" maxlength="200"></div>
            <label class="chk"><input v-model="cfg.amazing.countdown" type="checkbox"> شمارش معکوس تا نیمه‌شب نمایش داده شود</label>
          </template>
          <div v-if="'limit' in cfg[key]" class="fld w"><label>حداکثر تعداد محصول</label><input v-model.number="cfg[key].limit" type="number" min="1" max="24"></div>
          <template v-if="key === 'trust'">
            <div class="fld w"><label>برچسب کوچک کارت</label><input v-model="cfg.trust.kicker" type="text" maxlength="80"></div>
            <div class="fld w full"><label>متن «چرا این‌جا؟»</label><textarea v-model="cfg.trust.why" rows="2" maxlength="500"></textarea></div>
          </template>
          <template v-if="key === 'why'">
            <div v-for="(it, i) in cfg.why.items" :key="i" class="fld w full why-row">
              <select v-model="it.icon"><option v-for="ic in ICONS" :key="ic" :value="ic">{{ ic.replace('i-', '') }}</option></select>
              <input v-model="it.title" type="text" placeholder="عنوان" maxlength="80">
              <input v-model="it.text" type="text" placeholder="توضیح" maxlength="300">
              <button class="btn btn-light btn-sm del" @click="cfg.why.items.splice(i, 1)">حذف</button>
            </div>
            <div class="full"><button class="btn btn-light btn-sm" :disabled="cfg.why.items.length >= 8" @click="cfg.why.items.push({ icon: 'i-leaf', title: '', text: '' })">+ مورد جدید</button></div>
          </template>
        </div>
      </div>
      <button class="btn btn-brand" style="margin-top:12px" :disabled="busy" @click="saveSections">{{ busy ? 'در حال ذخیره…' : 'ذخیرهٔ بخش‌ها' }}</button>
    </div>

    <!-- مودال بنر -->
    <div class="overlay" :class="{ open: !!ban }" @click.self="ban = null"><div class="modal" style="width:min(640px,100%)">
      <div class="modal-head"><b>{{ ban && ban.id ? 'ویرایش بنر' : 'بنر جدید' }}</b><button class="modal-x" aria-label="بستن" @click="ban = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="ban"><div class="ad-grid">
        <div class="full"><ImageField v-model="ban.image" /></div>
        <div class="fld w"><label>برچسب کوچک</label><input v-model="ban.tag" type="text" maxlength="80"></div>
        <div class="fld w"><label>ترتیب</label><input v-model.number="ban.sort" type="number" min="0"></div>
        <div class="fld w"><label>عنوان</label><input v-model="ban.title" type="text" maxlength="120"></div>
        <div class="fld w"><label>بخش رنگی عنوان</label><input v-model="ban.titleEm" type="text" maxlength="60"></div>
        <div class="fld w full"><label>توضیح</label><textarea v-model="ban.text" rows="2" maxlength="300"></textarea></div>
        <div class="fld w"><label>دکمهٔ ۱ — متن</label><input v-model="ban.cta1.label" type="text" maxlength="40"></div>
        <div class="fld w"><label>دکمهٔ ۱ — پیوند (/products یا https://…)</label><input v-model="ban.cta1.link" type="text" dir="ltr" maxlength="190"></div>
        <div class="fld w"><label>دکمهٔ ۲ — متن</label><input v-model="ban.cta2.label" type="text" maxlength="40"></div>
        <div class="fld w"><label>دکمهٔ ۲ — پیوند</label><input v-model="ban.cta2.link" type="text" dir="ltr" maxlength="190"></div>
        <label class="chk full"><input v-model="ban.active" type="checkbox"> نمایش داده شود</label>
      </div><button class="btn btn-brand btn-block" style="margin-top:12px" :disabled="busy" @click="saveBanner">ذخیرهٔ بنر</button></div>
    </div></div>

    <!-- مودال پک -->
    <div class="overlay" :class="{ open: !!pk }" @click.self="pk = null"><div class="modal" style="width:min(620px,100%)">
      <div class="modal-head"><b>{{ pk && pk.id ? 'ویرایش پک' : 'پک جدید' }}</b><button class="modal-x" aria-label="بستن" @click="pk = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="pk"><div class="ad-grid">
        <div class="full"><ImageField v-model="pk.image" /></div>
        <div class="fld w"><label>نام پک *</label><input v-model="pk.name" type="text" maxlength="80"></div>
        <div class="fld w"><label>توضیح</label><input v-model="pk.sub" type="text" maxlength="160"></div>
        <div class="fld w"><label>قیمت قبل (تومان)</label><input v-model.number="pk.old" type="number" min="0" step="1000"></div>
        <div class="fld w"><label>قیمت فعلی (تومان) *</label><input v-model.number="pk.now" type="number" min="1" step="1000"></div>
        <div class="fld w"><label>موجودی</label><input v-model.number="pk.stock" type="number" min="0"></div>
        <div class="fld w"><label>ترتیب</label><input v-model.number="pk.sort" type="number" min="0"></div>
        <div class="fld w"><label>چرخهٔ شمارش (ساعت؛ ۰ = تاریخ ثابت)</label><input v-model.number="pk.cycleHours" type="number" min="0" max="720"></div>
        <div v-if="!pk.cycleHours" class="fld w"><label>پایان شمارش (شمسی ۱۴۰۵/۱۲/۲۹)</label><input v-model="pk.endJ" type="text" dir="ltr" placeholder="۱۴۰۵/۱۲/۲۹" maxlength="10">
          <input v-model="pk.endT" type="text" dir="ltr" placeholder="ساعت ۲۳:۵۹" maxlength="5" style="margin-top:6px"></div>
        <label class="chk full"><input v-model="pk.active" type="checkbox"> نمایش داده شود</label>
      </div><button class="btn btn-brand btn-block" style="margin-top:12px" :disabled="busy" @click="savePack">ذخیرهٔ پک</button></div>
    </div></div>

    <!-- مودال خرید اطمینان -->
    <div class="overlay" :class="{ open: !!tr }" @click.self="tr = null"><div class="modal" style="width:min(600px,100%)">
      <div class="modal-head"><b>{{ tr && tr.id ? 'ویرایش کالا' : 'کالای جدید' }}</b><button class="modal-x" aria-label="بستن" @click="tr = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="tr"><div class="ad-grid">
        <div class="full"><ImageField v-model="tr.image" /></div>
        <div class="fld w full"><label>نام کالا *</label><input v-model="tr.name" type="text" maxlength="160"></div>
        <div class="fld w"><label>روز هفته</label><select v-model.number="tr.day"><option v-for="d in WEEK_ORDER" :key="d" :value="d">{{ DAY_NAMES[d] }}</option></select></div>
        <div class="fld w"><label>موجودی</label><input v-model.number="tr.stock" type="number" min="0"></div>
        <div class="fld w"><label>قیمت قبل (تومان)</label><input v-model.number="tr.old" type="number" min="0" step="1000"></div>
        <div class="fld w"><label>قیمت ویژه (تومان) *</label><input v-model.number="tr.price" type="number" min="1" step="1000"></div>
        <label class="chk full"><input v-model="tr.active" type="checkbox"> نمایش داده شود</label>
      </div><button class="btn btn-brand btn-block" style="margin-top:12px" :disabled="busy" @click="saveTrust">ذخیرهٔ کالا</button></div>
    </div></div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { toFa, money, DAY_NAMES, WEEK_ORDER } from '../../data/site';
import { jDateTime, jalaliInputToIso, toEnDigits, isoToJalaliInput } from '../../data/jalali';
import { apiCall, imgSrc } from '../../services/api';
import { toast } from '../../stores/ui';
import { loadShop, DEFAULT_HOME } from '../../stores/shop';
import ImageField from '../../components/ImageField.vue';
import '../../assets/admin.css';

const sub = ref('banners');
const busy = ref(false);
const LABELS = { packs: 'پک‌های تخفیفی', cats: 'دسته‌بندی‌های محبوب', amazing: 'پیشنهاد شگفت‌انگیز', best: 'پرفروش‌ترین محصولات', trust: 'خرید اطمینان', consult: 'مشاوره خرید و پیگیری', why: 'چرا ما؟ (مزایا)' };
const ICONS = ['i-leaf', 'i-box', 'i-truck', 'i-scale', 'i-shield', 'i-percent', 'i-gift', 'i-star', 'i-heart', 'i-wallet', 'i-headset', 'i-fire'];

const banners = ref([]), packs = ref([]), trust = ref([]);
const ban = ref(null), pk = ref(null), tr = ref(null);
const cfg = reactive(JSON.parse(JSON.stringify(DEFAULT_HOME)));

const done = async (msg) => { toast(msg, 'ok'); await loadAll(); loadShop(); };

/* ---- بنر ---- */
const blankBanner = () => ({ id: 0, image: '', tag: '', title: '', titleEm: '', text: '', cta1: { label: 'مشاهده محصولات', link: '/products' }, cta2: { label: '', link: '' }, active: true, sort: banners.value.length });
async function saveBanner() {
  const b = ban.value; busy.value = true;
  const r = await apiCall(b.id ? '/admin/banners/' + b.id : '/admin/banners', { method: b.id ? 'PUT' : 'POST', body: b });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  ban.value = null; done('بنر ذخیره شد ✅');
}
async function toggleBanner(b) { const r = await apiCall('/admin/banners/' + b.id, { method: 'PUT', body: { active: !b.active } }); r.ok ? done(b.active ? 'بنر مخفی شد' : 'بنر نمایش داده می‌شود') : toast(r.msg, 'err'); }
async function delBanner(b) { if (!window.confirm('این بنر حذف شود؟')) return; const r = await apiCall('/admin/banners/' + b.id, { method: 'DELETE' }); r.ok ? done('بنر حذف شد') : toast(r.msg, 'err'); }

/* ---- پک ---- */
const blankPack = () => ({ id: 0, name: '', sub: '', image: '', old: 0, now: 0, stock: 20, sort: packs.value.length, cycleHours: 24, endJ: '', endT: '23:59', active: true });
function editPack(p) { pk.value = { ...p, endJ: p.fixedEnd ? isoToJalaliInput(p.fixedEnd) : '', endT: p.fixedEnd ? new Date(p.fixedEnd).toTimeString().slice(0, 5) : '23:59' }; }
async function savePack() {
  const p = pk.value;
  const body = { name: p.name, sub: p.sub, image: p.image, old: p.old || 0, now: p.now || 0, stock: p.stock ?? 0, sort: p.sort || 0, cycleHours: p.cycleHours || 0, active: p.active };
  if (!body.cycleHours) {
    const iso = jalaliInputToIso(p.endJ);
    if (!iso) return toast('تاریخ پایان را شمسی و به شکل ۱۴۰۵/۱۲/۲۹ وارد کنید', 'err');
    const t = toEnDigits(p.endT).match(/^(\d{1,2}):(\d{2})$/);
    if (!t) return toast('ساعت را به شکل ۲۳:۵۹ وارد کنید', 'err');
    body.fixedEnd = `${iso}T${t[1].padStart(2, '0')}:${t[2]}:00`;
  }
  busy.value = true;
  const r = await apiCall(p.id ? '/admin/packs/' + p.id : '/admin/packs', { method: p.id ? 'PUT' : 'POST', body });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  pk.value = null; done('پک ذخیره شد ✅');
}
async function restartPack(p) { const r = await apiCall('/admin/packs/' + p.id, { method: 'POST' }); r.ok ? done('شمارش معکوس از همین لحظه شروع شد') : toast(r.msg, 'err'); }
async function delPack(p) { if (!window.confirm(`پک «${p.name}» حذف شود؟`)) return; const r = await apiCall('/admin/packs/' + p.id, { method: 'DELETE' }); r.ok ? done('پک حذف شد') : toast(r.msg, 'err'); }

/* ---- خرید اطمینان ---- */
const blankTrust = () => ({ id: 0, day: (WEEK_ORDER.find(d => !trust.value.some(t => t.day === d)) ?? 6), name: '', image: '', old: 0, price: 0, stock: 8, active: true });
const editTrust = t => { tr.value = { ...t }; };
async function saveTrust() {
  const t = tr.value; busy.value = true;
  const body = { day: t.day, name: t.name, image: t.image, old: t.old || 0, price: t.price || 0, stock: t.stock ?? 0, active: t.active };
  const r = await apiCall(t.id ? '/admin/trust/' + t.id : '/admin/trust', { method: t.id ? 'PUT' : 'POST', body });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  tr.value = null; done('کالا ذخیره شد ✅');
}
async function delTrust(t) { if (!window.confirm(`«${t.name}» حذف شود؟`)) return; const r = await apiCall('/admin/trust/' + t.id, { method: 'DELETE' }); r.ok ? done('کالا حذف شد') : toast(r.msg, 'err'); }

/* ---- بخش‌ها ---- */
function move(i, d) { const o = cfg.order; [o[i], o[i + d]] = [o[i + d], o[i]]; }
async function saveSections() {
  busy.value = true;
  const body = JSON.parse(JSON.stringify(cfg));
  const r = await apiCall('/admin/home', { method: 'PUT', body });
  busy.value = false;
  r.ok ? done('بخش‌های صفحهٔ اصلی ذخیره شد ✅') : toast(r.msg, 'err');
}

async function loadAll() {
  const [b, p, t, h] = await Promise.all([apiCall('/admin/banners'), apiCall('/admin/packs'), apiCall('/admin/trust'), apiCall('/admin/home')]);
  if (b.ok) banners.value = b.banners; if (p.ok) packs.value = p.packs; if (t.ok) trust.value = t.items;
  if (h.ok) { const fresh = JSON.parse(JSON.stringify(h.home)); Object.keys(cfg).forEach(k => delete cfg[k]); Object.assign(cfg, fresh); }
}
onMounted(loadAll);
</script>

<style scoped>
.th{width:46px;height:46px;border-radius:10px;object-fit:cover;background:var(--bg-warm)}
.sec-box{border:1px solid var(--line);border-radius:14px;padding:12px;margin-bottom:10px;background:#fff}
.sec-box-h{display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap}
.sec-box-btns{display:flex;gap:4px;margin-inline-start:auto}
.why-row{display:grid;grid-template-columns:110px 1fr 1.6fr auto;gap:6px}
@media(max-width:767px){.why-row{grid-template-columns:1fr}}
</style>
