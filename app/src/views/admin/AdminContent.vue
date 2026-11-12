<template>
  <div class="admin-card">
    <div class="subtabs">
      <button :class="{ on: sub === 'info' }" @click="sub = 'info'">اطلاعات تماس و متن‌های اصلی</button>
      <button :class="{ on: sub === 'pages' }" @click="sub = 'pages'">صفحات راهنما و قوانین</button>
    </div>

    <!-- اطلاعات و متن‌ها -->
    <div v-if="sub === 'info'">
      <p class="ad-sub">این موارد در بالای سایت، فوتر، صفحهٔ اصلی، مشاوره و صفحهٔ «تماس با ما» نمایش داده می‌شوند.</p>
      <h3 class="ad-h">اطلاعات تماس</h3>
      <div class="ad-grid">
        <div class="fld w"><label>نام فروشگاه</label><input v-model="info.shopName" type="text" maxlength="80"></div>
        <div class="fld w"><label>تلفن (نمایشی، مثلاً ۰۲۱-۹۱۰۹۲۰۰۰)</label><input v-model="info.phone" type="text" maxlength="40"></div>
        <div class="fld w"><label>تلفن برای تماس (فقط عدد انگلیسی)</label><input v-model="info.phoneTel" type="text" dir="ltr" maxlength="20" placeholder="02191092000"></div>
        <div class="fld w"><label>واتس‌اپ (با کد کشور، مثلاً 989120000000)</label><input v-model="info.whatsapp" type="text" dir="ltr" maxlength="20"></div>
        <div class="fld w"><label>ایمیل</label><input v-model="info.email" type="text" dir="ltr" maxlength="120"></div>
        <div class="fld w"><label>ساعت پاسخگویی</label><input v-model="info.hours" type="text" maxlength="120"></div>
        <div class="fld w full"><label>نشانی</label><input v-model="info.address" type="text" maxlength="300"></div>
        <div class="fld w"><label>اینستاگرام (https://…)</label><input v-model="info.instagram" type="url" dir="ltr" maxlength="200" placeholder="https://instagram.com/..."></div>
        <div class="fld w"><label>تلگرام (https://…)</label><input v-model="info.telegram" type="url" dir="ltr" maxlength="200" placeholder="https://t.me/..."></div>
      </div>
      <h3 class="ad-h" style="margin-top:18px">متن‌های سایت</h3>
      <div class="ad-grid">
        <div class="fld w full"><label>پیام نوار بالای سایت</label><input v-model="info.topbarMsg" type="text" maxlength="160"></div>
        <div class="fld w"><label>برچسب بنر اصلی</label><input v-model="info.heroTag" type="text" maxlength="80"></div>
        <div class="fld w"><label>عنوان بنر اصلی</label><input v-model="info.heroTitle" type="text" maxlength="120"></div>
        <div class="fld w"><label>بخش برجسته‌شدهٔ عنوان</label><input v-model="info.heroTitleEm" type="text" maxlength="60"></div>
        <div class="fld w full"><label>توضیح بنر اصلی</label><textarea v-model="info.heroText" rows="2" maxlength="300"></textarea></div>
        <div class="fld w full"><label>متن بخش مشاوره خرید</label><textarea v-model="info.consultText" rows="2" maxlength="400"></textarea></div>
        <div class="fld w full"><label>دربارهٔ فروشگاه (فوتر)</label><textarea v-model="info.footerAbout" rows="3" maxlength="600"></textarea></div>
        <div class="fld w full"><label>جملهٔ مرجوعی (سبد خرید و صفحهٔ محصول)</label><input v-model="info.returnsNote" type="text" maxlength="160"></div>
      </div>
      <button class="btn btn-brand" style="margin-top:14px" :disabled="busy" @click="saveInfo">{{ busy ? 'در حال ذخیره…' : 'ذخیرهٔ اطلاعات و متن‌ها' }}</button>
    </div>

    <!-- صفحات -->
    <div v-else class="ad-split">
      <div>
        <button class="btn btn-gold btn-sm btn-block" style="margin-bottom:8px" @click="startNew"><svg class="icon"><use href="#i-plus" /></svg> صفحهٔ جدید</button>
        <div class="ad-list">
          <button v-for="p in pages" :key="p.id" :class="{ on: ed && ed.id === p.id }" @click="pick(p)">
            {{ p.title }}<small>{{ groupLabel[p.group] }} · {{ p.active ? 'نمایش' : 'مخفی' }}</small>
          </button>
        </div>
      </div>
      <div v-if="ed">
        <div class="ad-grid">
          <div class="fld w full"><label>عنوان صفحه *</label><input v-model="ed.title" type="text" maxlength="120"></div>
          <div class="fld w"><label>نشانی (انگلیسی) *</label><input v-model="ed.slug" type="text" dir="ltr" maxlength="60" placeholder="how-to-order"></div>
          <div class="fld w"><label>گروه (محل نمایش در فوتر)</label>
            <select v-model="ed.group"><option value="guide">راهنمای خرید</option><option value="about">دربارهٔ ما</option><option value="legal">قوانین</option></select>
          </div>
          <div class="fld w"><label>نوع صفحه</label>
            <select v-model="ed.kind">
              <option value="text">متنی</option><option value="faq">سوالات متداول</option>
              <option value="shipping">ارسال (جدول زندهٔ هزینه‌ها زیر متن)</option><option value="contact">تماس (کارت‌های اطلاعات تماس)</option>
            </select>
          </div>
          <div class="fld w"><label>ترتیب نمایش</label><input v-model.number="ed.sort" type="number" min="0"></div>
          <label class="chk full"><input v-model="ed.active" type="checkbox"> صفحه نمایش داده شود</label>
          <div class="fld w full">
            <label>متن صفحه <small style="color:var(--ink-3)">— «## عنوان»، «- مورد»، «1. گام»، **پررنگ**؛ بین پاراگراف‌ها یک خط خالی</small></label>
            <textarea v-model="ed.body" rows="12" maxlength="20000"></textarea>
          </div>
        </div>
        <div v-if="ed.kind === 'faq'" style="margin-top:12px">
          <h3 class="ad-h">سوال و جواب‌ها</h3>
          <div v-for="(it, i) in ed.items" :key="i" class="faq-edit">
            <input v-model="it.q" type="text" class="fld" placeholder="سوال" maxlength="250">
            <textarea v-model="it.a" class="fld" rows="2" placeholder="پاسخ" maxlength="3000"></textarea>
            <button class="btn btn-light btn-sm del" @click="ed.items.splice(i, 1)">حذف</button>
          </div>
          <button class="btn btn-light btn-sm" @click="ed.items.push({ q: '', a: '' })">+ سوال جدید</button>
        </div>
        <h3 class="ad-h" style="margin-top:14px">پیش‌نمایش متن</h3>
        <div class="preview rich" v-html="preview"></div>
        <div class="admin-toolbar" style="margin-top:12px">
          <button class="btn btn-brand" :disabled="busy" @click="savePage">{{ busy ? 'در حال ذخیره…' : 'ذخیرهٔ صفحه' }}</button>
          <RouterLink v-if="ed.id" class="btn btn-light btn-sm" :to="'/page/' + ed.slug" target="_blank">مشاهدهٔ صفحه</RouterLink>
          <button v-if="ed.id" class="btn btn-light btn-sm del" @click="removePage">حذف صفحه</button>
        </div>
      </div>
      <div v-else class="up-empty"><svg class="icon"><use href="#i-doc" /></svg><p>یک صفحه را از فهرست انتخاب کنید یا صفحهٔ جدید بسازید.</p></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { apiCall } from '../../services/api';
import { toast } from '../../stores/ui';
import { shop, loadShop, DEFAULT_INFO } from '../../stores/shop';
import { renderRichText } from '../../utils/richtext';
import '../../assets/admin.css';

const sub = ref('info');
const busy = ref(false);
const info = reactive({ ...DEFAULT_INFO });
const pages = ref([]);
const ed = ref(null);
const groupLabel = { guide: 'راهنمای خرید', about: 'دربارهٔ ما', legal: 'قوانین' };
const preview = computed(() => (ed.value ? renderRichText(ed.value.body) : ''));

async function loadInfo() {
  const r = await apiCall('/admin/info');
  if (r.ok) Object.assign(info, DEFAULT_INFO, r.info);
}
async function saveInfo() {
  busy.value = true;
  const r = await apiCall('/admin/info', { method: 'PUT', body: { ...info } });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  toast('اطلاعات و متن‌های سایت ذخیره شد ✅', 'ok'); loadShop();
}

async function loadPages() {
  const r = await apiCall('/admin/pages');
  if (!r.ok) return toast(r.msg || 'دریافت صفحات انجام نشد', 'err');
  pages.value = r.pages;
  if (ed.value && ed.value.id) { const cur = pages.value.find(p => p.id === ed.value.id); if (cur) pick(cur); }
}
const pick = p => { ed.value = JSON.parse(JSON.stringify(p)); };
function startNew() { ed.value = { id: 0, slug: '', title: '', kind: 'text', group: 'guide', body: '', items: [], sort: pages.value.length, active: true }; }
async function savePage() {
  const e = ed.value;
  busy.value = true;
  const body = { slug: e.slug, title: e.title, kind: e.kind, group: e.group, body: e.body, items: e.items, sort: e.sort || 0, active: e.active };
  const r = await apiCall(e.id ? '/admin/pages/' + e.id : '/admin/pages', { method: e.id ? 'PUT' : 'POST', body });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  toast('صفحه ذخیره شد ✅', 'ok');
  ed.value = JSON.parse(JSON.stringify(r.page));
  await loadPages(); loadShop();
}
async function removePage() {
  if (!window.confirm(`صفحهٔ «${ed.value.title}» حذف شود؟`)) return;
  const r = await apiCall('/admin/pages/' + ed.value.id, { method: 'DELETE' });
  if (!r.ok) return toast(r.msg, 'err');
  ed.value = null; toast('صفحه حذف شد', 'ok'); await loadPages(); loadShop();
}
onMounted(() => { loadInfo(); loadPages(); });
</script>

<style scoped>
.faq-edit{display:grid;grid-template-columns:1fr 1.4fr auto;gap:8px;align-items:start;margin-bottom:8px}
@media(max-width:767px){.faq-edit{grid-template-columns:1fr}}
</style>
