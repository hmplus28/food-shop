<template>
  <div class="admin-card">
    <div class="subtabs">
      <button :class="{ on: sub === 'cats' }" @click="sub = 'cats'">دسته‌های منو (هدر و منوی موبایل)</button>
      <button :class="{ on: sub === 'links' }" @click="sub = 'links'">پیوندهای منو</button>
    </div>

    <!-- دسته‌های منو -->
    <div v-if="sub === 'cats'">
      <p class="ad-sub">این دسته‌ها در <b>منوی هدر دسکتاپ</b>، <b>منوی موبایل</b>، بخش «دسته‌بندی‌های محبوب» صفحهٔ اصلی، فیلترهای صفحهٔ فروشگاه و فوتر نمایش داده می‌شوند؛ نام، آیکن، زیرشاخه‌ها، ترتیب و روشن‌خاموشی هر کدام را می‌توانید تغییر دهید. «شناسه» همان دستهٔ محصولات است — با تغییر آن، محصولات خودکار جابه‌جا می‌شوند.</p>
      <div class="admin-toolbar">
        <button class="btn btn-gold btn-sm" @click="newCat"><svg class="icon"><use href="#i-plus" /></svg> دستهٔ جدید</button>
        <span class="ad-sub" style="margin:0">برای کاهش آیتم‌های هدر، دسته‌ها را مخفی کنید (چک‌باکس «نمایش داده شود») — منو بدون اسکرول به چند ردیف می‌شکند.</span>
      </div>
      <div class="ad-split">
        <div class="ad-list">
          <button v-for="c in cats" :key="c.id" :class="{ on: ed && ed.id === c.id }" @click="pick(c)">
            <svg class="icon"><use :href="'#' + c.icon" /></svg> {{ c.name }}
            <small>{{ c.slug }} · ترتیب {{ toFa(c.sort) }} · {{ c.active ? 'نمایش' : 'مخفی' }}<template v-if="c.products"> · {{ toFa(c.products) }} محصول</template></small>
          </button>
          <div v-if="!cats.length" class="up-empty"><p>دسته‌ای ثبت نشده است؛ «دستهٔ جدید» بسازید.</p></div>
        </div>
        <div v-if="ed">
          <div class="ad-grid">
            <div class="fld w"><label>عنوان دسته *</label><input v-model="ed.name" type="text" maxlength="60"></div>
            <div class="fld w"><label>شناسه (انگلیسی، با خط تیره) * <small style="color:var(--ink-3)">مثلاً pistachio</small></label>
              <input v-model="ed.slug" type="text" dir="ltr" maxlength="40" placeholder="pistachio"></div>
          </div>
          <h3 class="ad-h" style="margin-top:14px">آیکن دسته</h3>
          <div class="icogrid">
            <button v-for="ic in ICONS" :key="ic.id" type="button" :class="{ on: ed.icon === ic.id }" :title="ic.id" @click="ed.icon = ic.id">
              <svg class="icon"><use :href="'#' + ic.id" /></svg><small>{{ ic.t }}</small>
            </button>
          </div>
          <h3 class="ad-h" style="margin-top:14px">زیرشاخه‌ها <small style="color:var(--ink-3);font-weight:500">(هر خط یک زیرشاخه — حداکثر ۱۲)</small></h3>
          <textarea v-model="ed.subsText" rows="5" maxlength="800" placeholder="پسته اکبری&#10;پسته احمدآقایی&#10;…"></textarea>
          <h3 class="ad-h" style="margin-top:14px">باکس ویژهٔ مگامنو (اختیاری)</h3>
          <div class="ad-grid">
            <div class="fld w full"><label>تصویر ویژه</label><ImageField v-model="ed.featImg" /></div>
            <div class="fld w"><label>عنوان باکس</label><input v-model="ed.featTitle" type="text" maxlength="80"></div>
            <div class="fld w"><label>توضیح باکس</label><input v-model="ed.featSub" type="text" maxlength="120"></div>
            <div class="fld w"><label>ترتیب نمایش</label><input v-model.number="ed.sort" type="number" min="0" max="99"></div>
          </div>
          <div style="display:flex;gap:18px;margin-top:10px;flex-wrap:wrap">
            <label class="chk"><input v-model="ed.active" type="checkbox"> نمایش در سایت</label>
            <label class="chk"><input v-model="ed.hot" type="checkbox"> برچسب «داغ»</label>
          </div>
          <div class="admin-toolbar" style="margin-top:14px">
            <button class="btn btn-brand" :disabled="busy" @click="saveCat">{{ busy ? 'در حال ذخیره…' : 'ذخیرهٔ دسته' }}</button>
            <button v-if="ed.id" class="btn btn-light btn-sm del" @click="removeCat">حذف دسته</button>
          </div>
        </div>
        <div v-else class="up-empty"><svg class="icon"><use href="#i-menu" /></svg><p>یک دسته را انتخاب کنید یا دستهٔ جدید بسازید.</p></div>
      </div>
    </div>

    <!-- پیوندهای منو -->
    <div v-else>
      <p class="ad-sub">این پیوندها در <b>پایین منوی موبایل</b> (کنار شماره تلفن) نمایش داده می‌شوند؛ برای هر پیوند می‌توانید عنوان، آیکن و مقصد تعیین کنید. پیوند داخلی با «/» شروع شود (مثلاً /track) و پیوند بیرونی با https://.</p>
      <div class="admin-toolbar">
        <button class="btn btn-gold btn-sm" @click="newLink"><svg class="icon"><use href="#i-plus" /></svg> پیوند جدید</button>
      </div>
      <div class="ad-split">
        <div class="ad-list">
          <button v-for="m in links" :key="m.id" :class="{ on: edL && edL.id === m.id }" @click="pickLink(m)">
            <svg class="icon"><use :href="'#' + m.icon" /></svg> {{ m.label }}
            <small>{{ m.link }} · ترتیب {{ toFa(m.sort) }} · {{ m.active ? 'نمایش' : 'مخفی' }}</small>
          </button>
          <div v-if="!links.length" class="up-empty"><p>پیوندی ثبت نشده است؛ «پیوند جدید» بسازید.</p></div>
        </div>
        <div v-if="edL">
          <div class="ad-grid">
            <div class="fld w"><label>عنوان *</label><input v-model="edL.label" type="text" maxlength="60"></div>
            <div class="fld w"><label>پیوند * <small style="color:var(--ink-3)">/track یا https://…</small></label><input v-model="edL.link" type="text" dir="ltr" maxlength="200" placeholder="/track"></div>
          </div>
          <h3 class="ad-h" style="margin-top:14px">آیکن پیوند</h3>
          <div class="icogrid">
            <button v-for="ic in ICONS" :key="ic.id" type="button" :class="{ on: edL.icon === ic.id }" :title="ic.id" @click="edL.icon = ic.id">
              <svg class="icon"><use :href="'#' + ic.id" /></svg><small>{{ ic.t }}</small>
            </button>
          </div>
          <div class="ad-grid" style="margin-top:12px">
            <div class="fld w"><label>ترتیب نمایش</label><input v-model.number="edL.sort" type="number" min="0" max="99"></div>
          </div>
          <label class="chk" style="margin-top:10px"><input v-model="edL.active" type="checkbox"> نمایش در منو</label>
          <div class="admin-toolbar" style="margin-top:14px">
            <button class="btn btn-brand" :disabled="busy" @click="saveLink">{{ busy ? 'در حال ذخیره…' : 'ذخیرهٔ پیوند' }}</button>
            <button v-if="edL.id" class="btn btn-light btn-sm del" @click="removeLink">حذف پیوند</button>
          </div>
        </div>
        <div v-else class="up-empty"><svg class="icon"><use href="#i-pin" /></svg><p>یک پیوند را انتخاب کنید یا پیوند جدید بسازید.</p></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { apiCall } from '../../services/api';
import { toast } from '../../stores/ui';
import { loadShop } from '../../stores/shop';
import { toFa } from '../../data/site';
import ImageField from '../../components/ImageField.vue';
import '../../assets/admin.css';

const sub = ref('cats');
const busy = ref(false);
const cats = ref([]);
const links = ref([]);
const ed = ref(null);      // دستهٔ در حال ویرایش
const edL = ref(null);     // پیوند در حال ویرایش

/* آیکن‌های موجود در قالب (IconSprite) با نام فارسی برای انتخاب راحت مدیر */
const ICONS = [
  { id: 'i-nut', t: 'آجیل' }, { id: 'i-leaf', t: 'برگ' }, { id: 'i-fire', t: 'داغ' }, { id: 'i-gift', t: 'هدیه' },
  { id: 'i-star', t: 'ستاره' }, { id: 'i-box', t: 'بسته' }, { id: 'i-truck', t: 'ارسال' }, { id: 'i-shield', t: 'سپر' },
  { id: 'i-tag', t: 'برچسب' }, { id: 'i-percent', t: 'درصد' }, { id: 'i-wallet', t: 'کیف پول' }, { id: 'i-scale', t: 'ترازو' },
  { id: 'i-phone', t: 'تلفن' }, { id: 'i-headset', t: 'پشتیبانی' }, { id: 'i-sms', t: 'پیام' }, { id: 'i-doc', t: 'سند' },
  { id: 'i-search', t: 'جستجو' }, { id: 'i-heart', t: 'علاقه‌مندی' }, { id: 'i-user', t: 'کاربر' }, { id: 'i-cart', t: 'سبد' },
  { id: 'i-pin', t: 'مکان' }, { id: 'i-clock', t: 'ساعت' }, { id: 'i-refresh', t: 'تازه‌سازی' }, { id: 'i-lock', t: 'قفل' },
  { id: 'i-check', t: 'تیک' }, { id: 'i-palette', t: 'رنگ' }, { id: 'i-instagram', t: 'اینستاگرام' }, { id: 'i-telegram', t: 'تلگرام' },
  { id: 'i-whatsapp', t: 'واتساپ' },
];

/* ---------- دسته‌ها ---------- */
async function loadCats() {
  const r = await apiCall('/admin/cats');
  if (!r.ok) return toast(r.msg || 'دریافت دسته‌ها انجام نشد', 'err');
  cats.value = r.cats;
  if (ed.value && ed.value.id) { const cur = cats.value.find(c => c.id === ed.value.id); if (cur) pick(cur); }
}
const pick = c => {
  ed.value = { ...JSON.parse(JSON.stringify(c)), subsText: (c.subs || []).join('\n'), featImg: (c.feat && c.feat.img) || '', featTitle: (c.feat && c.feat.t) || '', featSub: (c.feat && c.feat.s) || '' };
};
function newCat() {
  ed.value = { id: 0, slug: '', name: '', icon: 'i-nut', subsText: '', featImg: '', featTitle: '', featSub: '', hot: false, active: true, sort: cats.value.length, products: 0 };
}
async function saveCat() {
  const e = ed.value;
  busy.value = true;
  const body = {
    slug: (e.slug || '').trim(), name: (e.name || '').trim(), icon: e.icon,
    subs: e.subsText.split('\n').map(s => s.trim()).filter(Boolean),
    feat: { img: e.featImg || '', t: e.featTitle || '', s: e.featSub || '' },
    hot: !!e.hot, active: !!e.active, sort: e.sort || 0,
  };
  const r = await apiCall(e.id ? '/admin/cats/' + e.id : '/admin/cats', { method: e.id ? 'PUT' : 'POST', body });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  toast('دسته ذخیره شد ✅', 'ok');
  ed.value = { ...JSON.parse(JSON.stringify(r.cat)), subsText: (r.cat.subs || []).join('\n'), featImg: (r.cat.feat && r.cat.feat.img) || '', featTitle: (r.cat.feat && r.cat.feat.t) || '', featSub: (r.cat.feat && r.cat.feat.s) || '' };
  await loadCats(); loadShop();
}
async function removeCat() {
  const c = ed.value;
  const msg = c.products ? `دستهٔ «${c.name}» حذف شود؟ (این دسته ${toFa(c.products)} محصول دارد — سرور اجازهٔ حذف نمی‌دهد تا اول محصولات جابه‌جا شوند)` : `دستهٔ «${c.name}» حذف شود؟`;
  if (!window.confirm(msg)) return;
  const r = await apiCall('/admin/cats/' + c.id, { method: 'DELETE' });
  if (!r.ok) return toast(r.msg, 'err');
  ed.value = null; toast('دسته حذف شد', 'ok');
  await loadCats(); loadShop();
}

/* ---------- پیوندها ---------- */
async function loadLinks() {
  const r = await apiCall('/admin/menu');
  if (!r.ok) return toast(r.msg || 'دریافت پیوندها انجام نشد', 'err');
  links.value = r.menu;
}
const pickLink = m => { edL.value = JSON.parse(JSON.stringify(m)); };
function newLink() { edL.value = { id: 0, label: '', icon: 'i-leaf', link: '', active: true, sort: links.value.length }; }
async function saveLink() {
  const e = edL.value;
  busy.value = true;
  const body = { label: (e.label || '').trim(), icon: e.icon, link: (e.link || '').trim(), active: !!e.active, sort: e.sort || 0 };
  const r = await apiCall(e.id ? '/admin/menu/' + e.id : '/admin/menu', { method: e.id ? 'PUT' : 'POST', body });
  busy.value = false;
  if (!r.ok) return toast(r.msg, 'err');
  toast('پیوند ذخیره شد ✅', 'ok');
  edL.value = JSON.parse(JSON.stringify(r.link));
  await loadLinks(); loadShop();
}
async function removeLink() {
  if (!window.confirm(`پیوند «${edL.value.label}» حذف شود؟`)) return;
  const r = await apiCall('/admin/menu/' + edL.value.id, { method: 'DELETE' });
  if (!r.ok) return toast(r.msg, 'err');
  edL.value = null; toast('پیوند حذف شد', 'ok');
  await loadLinks(); loadShop();
}

onMounted(() => { loadCats(); loadLinks(); });
</script>

<style scoped>
/* انتخابگر آیکن — شبکه‌ای از آیکن‌های واقعی قالب */
.icogrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(58px,1fr));gap:6px}
.icogrid button{display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 4px;border:1px solid var(--line);
  border-radius:10px;background:#fff;cursor:pointer;font-family:inherit;color:var(--ink-2)}
.icogrid button .icon{width:20px;height:20px;color:var(--gold-600)}
.icogrid button small{font-size:.6rem;color:var(--ink-3)}
.icogrid button.on{background:var(--brand-050);border-color:var(--brand);color:var(--brand-700)}
.icogrid button.on .icon{color:var(--brand-700)}
.ad-list button .icon{width:14px;height:14px;color:var(--gold-600)}
</style>
