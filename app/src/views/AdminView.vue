<template>
  <div class="section">
    <div class="container">
      <!-- ورود مدیر -->
      <div v-if="!auth.isAdmin" class="admin-login">
        <div class="auth-card">
          <h1 style="font-size:1.1rem;display:flex;align-items:center;gap:8px;margin-bottom:16px"><svg class="icon"><use href="#i-lock" /></svg> ورود مدیر فروشگاه</h1>
          <form class="auth-form" @submit.prevent="doAdmin">
            <div class="fld w"><label>نام کاربری یا موبایل</label><input v-model="au" type="text" autocomplete="username"></div>
            <div class="fld w"><label>رمز عبور</label><input v-model="ap" type="password" autocomplete="current-password"></div>
            <button class="btn btn-brand btn-block" type="submit" :disabled="loggingIn">{{ loggingIn ? 'در حال ورود…' : 'ورود به پنل مدیریت' }}</button>
          </form>
        </div>
      </div>

      <!-- پنل مدیریت -->
      <template v-else>
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-box" /></svg></span>
            <div><h1 class="sec-title">پنل <i>مدیریت</i> خانم گل</h1><span class="sec-sub">محصولات، سفارش‌ها، مشتریان، پنل پیامک و ظاهر سایت</span></div></span>
          <div class="sec-actions"><button class="btn btn-light btn-sm" @click="adminLogout(); toast('از پنل مدیر خارج شدید', 'ok')"><svg class="icon"><use href="#i-x" /></svg> خروج</button></div>
        </div>

        <div class="admin-stats">
          <div class="up-stat"><b>{{ toFa(stats.products ?? plist.length) }}</b><span>محصول</span></div>
          <div class="up-stat"><b>{{ toFa(stats.orders ?? 0) }}</b><span>سفارش</span></div>
          <div class="up-stat"><b>{{ toFa(stats.users ?? 0) }}</b><span>مشتری</span></div>
          <div class="up-stat"><b>{{ money(stats.revenue ?? 0) }}</b><span>فروش کل (تومان)</span></div>
          <div class="up-stat"><b>{{ toFa(stats.lowStock ?? 0) }}</b><span>موجودی کم (&lt;۱۰)</span></div>
        </div>

        <div class="admin-tabs">
          <button :class="{ on: tab === 'products' }" @click="tab = 'products'">محصولات</button>
          <button :class="{ on: tab === 'orders' }" @click="tab = 'orders'">سفارش‌ها</button>
          <button :class="{ on: tab === 'users' }" @click="tab = 'users'">مشتریان</button>
          <button :class="{ on: tab === 'sms' }" @click="tab = 'sms'">پنل پیامک</button>
          <button :class="{ on: tab === 'look' }" @click="tab = 'look'">ظاهر سایت</button>
        </div>

        <!-- محصولات -->
        <div v-if="tab === 'products'" class="admin-card">
          <div class="admin-toolbar">
            <button class="btn btn-gold btn-sm" @click="startNew"><svg class="icon"><use href="#i-plus" /></svg> افزودن محصول</button>
            <input v-model="pq" class="fld" type="search" placeholder="جستجوی محصول…" style="max-width:220px">
            <button class="btn btn-light btn-sm" @click="loadProducts">به‌روزرسانی ⟳</button>
          </div>
          <div v-if="!shownProducts.length" class="up-empty"><svg class="icon"><use href="#i-box" /></svg><p>محصولی پیدا نشد.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>محصول</th><th>دسته</th><th>قیمت پایه (کیلو)</th><th>تخفیف</th><th>موجودی</th><th></th></tr></thead>
              <tbody>
                <tr v-for="p in shownProducts" :key="p.id">
                  <td class="td-p"><img :src="p.img" alt=""><div><b>{{ p.name }}</b><span v-if="p.hide" class="badge-hide">پنهان</span><small>{{ p.grade }}</small></div></td>
                  <td>{{ catOf(p.cat)?.name || '—' }}</td>
                  <td>{{ money(p.price) }}</td>
                  <td>{{ p.disc ? '٪' + toFa(p.disc) : '—' }}</td>
                  <td><span class="tag" :class="p.stock >= 10 ? 'green' : 'red'">{{ toFa(p.stock) }}</span></td>
                  <td class="td-acts">
                    <button class="btn btn-light btn-sm" @click="startEdit(p)">ویرایش</button>
                    <button class="btn btn-light btn-sm" @click="toggleHide(p)">{{ p.hide ? 'نمایش' : 'پنهان' }}</button>
                    <button class="btn btn-light btn-sm del" @click="del(p)">حذف</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- سفارش‌ها -->
        <div v-else-if="tab === 'orders'" class="admin-card">
          <div class="admin-toolbar">
            <select v-model="ostatus" class="fld" style="max-width:170px" @change="loadOrders">
              <option value="">همهٔ وضعیت‌ها</option>
              <option v-for="(s, i) in STATUS" :key="i" :value="String(i)">{{ s }}</option>
            </select>
            <input v-model="oq" class="fld" type="search" placeholder="کد سفارش یا موبایل…" style="max-width:220px" @keydown.enter="loadOrders">
            <button class="btn btn-light btn-sm" @click="loadOrders">جست‌وجو / به‌روزرسانی ⟳</button>
          </div>
          <div v-if="!olist.length" class="up-empty"><svg class="icon"><use href="#i-doc" /></svg><p>سفارشی پیدا نشد.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>کد</th><th>تاریخ</th><th>اقلام</th><th>مبلغ</th><th>مشتری</th><th>وضعیت</th><th></th></tr></thead>
              <tbody>
                <tr v-for="o in olist" :key="o.code">
                  <td><b>{{ o.code }}</b></td>
                  <td>{{ faDate(o.ts) }}</td>
                  <td class="td-items">{{ o.items.map(c => `${c.pname || '?'} (${weightLabel(c.w)}×${toFa(c.qty)})`).join(' + ') }}</td>
                  <td>{{ money(o.total) }}</td>
                  <td>{{ o.addr.name }}<small style="display:block;color:var(--ink-3)">{{ toFa(o.addr.phone) }}</small></td>
                  <td>
                    <select class="fld" style="padding:5px 8px;font-size:.78rem" :value="String(o.status)" @change="changeStatus(o, Number($event.target.value))">
                      <option v-for="(s, i) in STATUS" :key="i" :value="String(i)">{{ s }}</option>
                    </select>
                  </td>
                  <td class="td-acts"><button class="btn btn-light btn-sm" @click="detail = o">جزئیات</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- مشتریان -->
        <div v-else-if="tab === 'users'" class="admin-card">
          <div class="admin-toolbar">
            <input v-model="uq" class="fld" type="search" placeholder="نام یا موبایل…" style="max-width:240px" @keydown.enter="loadUsers">
            <button class="btn btn-light btn-sm" @click="loadUsers">جست‌وجو / به‌روزرسانی ⟳</button>
            <span class="sync-chip on">{{ toFa(usersTotal) }} کاربر</span>
          </div>
          <div v-if="!ulist.length" class="up-empty"><svg class="icon"><use href="#i-user" /></svg><p>کاربری پیدا نشد.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>نام</th><th>موبایل</th><th>نقش</th><th>عضویت</th><th>سفارش‌ها</th><th>مجموع خرید</th></tr></thead>
              <tbody>
                <tr v-for="u in ulist" :key="u.id">
                  <td>{{ u.name }}</td>
                  <td dir="ltr" style="text-align:end">{{ toFa(u.phone) }}</td>
                  <td><span class="tag" :class="u.role === 'admin' ? 'red' : 'green'">{{ u.role === 'admin' ? 'مدیر' : 'مشتری' }}</span></td>
                  <td>{{ faDate(Date.parse(u.joined)) }}</td>
                  <td>{{ toFa(u.orders) }}</td>
                  <td>{{ money(u.spent) }} تومان</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ظاهر سایت -->
        <div v-else-if="tab === 'look'" class="admin-card">
          <SiteStudio inline />
        </div>

        <!-- پنل پیامک -->
        <div v-else class="admin-card">
          <div class="sms-head">
            <span class="sync-chip" :class="smsReady ? 'on' : 'off'">
              {{ smsReady ? `● سرویس پیامک: ${smsProviderLabel}` : '○ پنل پیامک متصل نیست (حالت توسعه)' }}
            </span>
            <button class="btn btn-light btn-sm" @click="loadSms">به‌روزرسانی ⟳</button>
          </div>

          <div class="sms-test">
            <input v-model="smsTestTo" class="fld" type="tel" inputmode="tel" placeholder="شماره برای پیامک آزمایشی (۰۹…)" dir="rtl" style="max-width:240px">
            <button class="btn btn-gold btn-sm" :disabled="smsSending" @click="sendTestSms">{{ smsSending ? 'در حال ارسال…' : 'ارسال پیامک تست' }}</button>
          </div>

          <div v-if="!smsRows.length" class="up-empty" style="margin-top:10px"><svg class="icon"><use href="#i-sms" /></svg><p>هنوز پیامکی ثبت نشده است.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>زمان</th><th>گیرنده</th><th>نوع</th><th>وضعیت</th><th>متن</th></tr></thead>
              <tbody>
                <tr v-for="(s, i) in smsRows" :key="i">
                  <td style="white-space:nowrap">{{ toFa(faTime(s.ts)) }} — {{ faDate(s.ts) }}</td>
                  <td dir="ltr" style="text-align:end">{{ toFa(s.to) }}</td>
                  <td>{{ smsTagLabel(s.tag) }}</td>
                  <td><span class="tag" :class="s.ok ? 'green' : 'red'">{{ s.ok ? 'موفق' : 'ناموفق' }}</span></td>
                  <td class="td-items" style="max-width:340px">{{ s.text }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>

  <!-- جزئیات سفارش -->
  <div class="overlay" :class="{ open: !!detail }" @click.self="detail = null">
    <div class="modal" style="width:min(620px,100%)">
      <div class="modal-head"><b><svg class="icon"><use href="#i-doc" /></svg> سفارش {{ detail && detail.code }}</b><button class="modal-x" aria-label="بستن" @click="detail = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="detail">
        <div class="od-grid">
          <div><b>گیرنده:</b>{{ detail.addr.name }}</div>
          <div><b>موبایل:</b><span dir="ltr">{{ toFa(detail.addr.phone) }}</span></div>
          <div><b>استان / شهر:</b>{{ detail.addr.prov }} {{ detail.addr.city }}</div>
          <div><b>تاریخ:</b>{{ faDate(detail.ts) }} {{ toFa(faTime(detail.ts)) }}</div>
          <div style="grid-column:1/-1"><b>آدرس:</b>{{ detail.addr.addr }}</div>
          <div><b>ارسال:</b>{{ detail.shipLabel }} ({{ detail.shipDays }})</div>
          <div><b>کد تخفیف:</b>{{ detail.coupon || '—' }}</div>
          <div v-if="detail.note" style="grid-column:1/-1"><b>توضیح مشتری:</b>{{ detail.note }}</div>
        </div>
        <div class="tbl-wrap">
          <table class="tbl" style="min-width:0">
            <thead><tr><th>کالا</th><th>وزن</th><th>تعداد</th><th>جمع</th></tr></thead>
            <tbody><tr v-for="(c, i) in detail.items" :key="i"><td>{{ c.pname }}</td><td>{{ weightLabel(c.w) }}</td><td>{{ toFa(c.qty) }}</td><td>{{ money(c.cost) }}</td></tr></tbody>
          </table>
        </div>
        <div class="od-grid" style="margin-top:12px">
          <div><b>جمع کالاها:</b>{{ money(detail.sub) }}</div>
          <div><b>تخفیف:</b>{{ money(detail.off) }}</div>
          <div><b>هزینه ارسال:</b>{{ money(detail.shipCost) }}</div>
          <div><b>قابل پرداخت:</b><strong>{{ money(detail.total) }} تومان</strong></div>
        </div>
      </div>
    </div>
  </div>

  <!-- مودال ویرایش/افزودن محصول -->
  <div class="overlay" :class="{ open: editing }" @click.self="editing = null">
    <div class="modal" style="width:min(620px,100%)">
      <div class="modal-head"><b><svg class="icon"><use href="#i-nut" /></svg> {{ editing && editing.id ? 'ویرایش محصول' : 'افزودن محصول' }}</b><button class="modal-x" aria-label="بستن" @click="editing = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="editing">
        <div class="f-grid c2">
          <div class="fld w" style="grid-column:1/-1"><label>نام محصول *</label><input v-model="editing.name" type="text"></div>
          <div class="fld w"><label>دسته‌بندی</label>
            <select v-model="editing.cat"><option v-for="c in CATS" :key="c.id" :value="c.id">{{ c.name }}</option></select>
          </div>
          <div class="fld w"><label>درجه</label><input v-model="editing.grade" type="text"></div>
          <div class="fld w"><label>قیمت پایه هر کیلو (تومان) *</label><input v-model.number="editing.price" type="number" min="0" step="10000"></div>
          <div class="fld w"><label>تخفیف (٪)</label><input v-model.number="editing.disc" type="number" min="0" max="90"></div>
          <div class="fld w"><label>موجودی</label><input v-model.number="editing.stock" type="number" min="0"></div>
          <div class="fld w"><label>امتیاز (۰ تا ۵)</label><input v-model.number="editing.rate" type="number" min="0" max="5" step="0.1"></div>
          <div class="fld w" style="grid-column:1/-1"><label>توضیحات</label><textarea v-model="editing.desc" rows="2"></textarea></div>
          <div class="fld w" style="grid-column:1/-1"><label>آدرس تصویر</label><input v-model="editing.img" type="text" dir="ltr" placeholder="/img/نام-فایل.jpg یا https://…"></div>
          <label class="chk" style="grid-column:1/-1"><input v-model="editing.hide" type="checkbox"> پنهان از فروشگاه (در سایت نمایش داده نشود)</label>
        </div>
        <button class="btn btn-brand btn-block" style="margin-top:12px" @click="save"><svg class="icon"><use href="#i-check" /></svg> ذخیره محصول</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { toFa, money, weightLabel, faDate, faTime, toEn } from '../data/site';
import { CATS, catOf, IMG } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import SiteStudio from '../components/SiteStudio.vue';
import { auth, adminLogin, adminLogout } from '../stores/auth';
import { STATUS } from '../stores/orders';
import { toast } from '../stores/ui';
import { adminStatsApi, ordersListApi, patchOrderStatusApi, adminSmsLogApi, adminSmsTestApi, adminUsersApi,
  adminProductsApi, productCreateApi, productUpdateApi, productDeleteApi, syncCatalog } from '../services/api';
import { pruneCart } from '../stores/cart';

useSeo({ title: 'پنل مدیریت', description: 'پنل مدیریت فروشگاه خانم گل', path: '/admin' });

const tab = ref('products');
const au = ref(''), ap = ref('');
const loggingIn = ref(false);
const editing = ref(null);
const detail = ref(null);
const stats = ref({});

async function loadStats() { const s = await adminStatsApi(); if (s) stats.value = s; }

/* ---------- محصولات (همیشه از سرور؛ شامل پنهان‌ها) ---------- */
const plist = ref([]);
const pq = ref('');
const shownProducts = computed(() => {
  const q = pq.value.trim();
  return q ? plist.value.filter(p => (p.name + ' ' + (catOf(p.cat)?.name || '')).includes(q)) : plist.value;
});
async function loadProducts() {
  const l = await adminProductsApi();
  if (l) plist.value = l; else toast('دریافت محصولات از سرور انجام نشد', 'err');
}
/* پس از هر تغییر، کاتالوگ عمومی و آمار هم تازه می‌شود */
async function afterChange() { await Promise.all([loadProducts(), loadStats(), syncCatalog().then(pruneCart)]); }

function startNew() {
  editing.value = { id: 0, name: '', cat: 'ajil', img: IMG + '66fd0cba7ee8.jpg', price: 1000000, weights: [250, 500, 1000, 2000], stock: 20, disc: 0, grade: 'درجه یک', rate: 4.5, sold: 0, tags: [], sec: [], desc: '', hide: false };
}
function startEdit(p) { editing.value = { ...p, tags: [...p.tags], sec: [...p.sec], weights: [...p.weights], hide: !!p.hide }; }

async function save() {
  const e = editing.value;
  if (!e.name.trim()) return toast('نام محصول را وارد کنید', 'err');
  if (!e.price || e.price <= 0) return toast('قیمت پایه معتبر وارد کنید', 'err');
  if (e.disc < 0 || e.disc > 90) return toast('تخفیف باید بین ۰ تا ۹۰ باشد', 'err');
  const res = e.id ? await productUpdateApi(e.id, e) : await productCreateApi(e);
  if (!res) return toast('ذخیرهٔ محصول روی سرور انجام نشد؛ دوباره وارد شوید یا اتصال را بررسی کنید', 'err');
  editing.value = null;
  toast('محصول ذخیره شد ✅', 'ok');
  afterChange();
}
async function toggleHide(p) {
  const res = await productUpdateApi(p.id, { ...p, hide: !p.hide });
  if (!res) return toast('تغییر انجام نشد', 'err');
  toast(p.hide ? 'محصول دوباره نمایش داده می‌شود' : 'محصول از فروشگاه پنهان شد', 'ok');
  afterChange();
}
async function del(p) {
  if (!window.confirm(`«${p.name}» برای همیشه حذف شود؟ (برای پنهان‌کردن موقت از دکمهٔ «پنهان» استفاده کنید)`)) return;
  if (!(await productDeleteApi(p.id))) return toast('حذف روی سرور انجام نشد', 'err');
  toast('محصول حذف شد', 'ok');
  afterChange();
}

/* ---------- سفارش‌ها ---------- */
const olist = ref([]);
const ostatus = ref('');
const oq = ref('');
function mapServerOrder(o) {
  return {
    code: o.code, ts: o.ts, status: o.status, sub: o.sub, off: o.off, coupon: o.coupon, note: o.note || '',
    shipCost: o.ship_cost, shipLabel: o.ship_label, shipDays: o.ship_days, total: o.total,
    items: (o.items || []).map(c => ({ pid: c.pid, w: c.w, qty: c.qty, pname: c.name, cost: c.cost })),
    addr: { name: '', phone: '', prov: '', city: '', addr: '', ...(o.addr || {}) },
  };
}
async function loadOrders() {
  const r = await ordersListApi({ limit: 200, status: ostatus.value, q: oq.value.trim() });
  if (r) olist.value = (r.results || []).map(mapServerOrder); else toast('دریافت سفارش‌ها از سرور انجام نشد', 'err');
}
async function changeStatus(o, st) {
  if (!(await patchOrderStatusApi(o.code, st))) { toast('تغییر وضعیت روی سرور انجام نشد', 'err'); return loadOrders(); }
  o.status = st;
  toast(`وضعیت سفارش ${o.code} به «${STATUS[st]}» تغییر کرد`, 'ok');
}

/* ---------- مشتریان ---------- */
const ulist = ref([]);
const uq = ref('');
const usersTotal = ref(0);
async function loadUsers() {
  const r = await adminUsersApi(uq.value.trim());
  if (r) { ulist.value = r.users || []; usersTotal.value = r.total || 0; } else toast('دریافت مشتریان از سرور انجام نشد', 'err');
}

/* ---------- ورود مدیر ---------- */
async function doAdmin() {
  loggingIn.value = true;
  const res = await adminLogin(au.value, ap.value);
  loggingIn.value = false;
  if (!res.ok) return toast(res.msg, 'err');
  toast('به پنل مدیریت خوش آمدید 👑', 'gold');
  loadAll();
}

/* ---------- پنل پیامک ---------- */
const smsRows = ref([]);
const smsMeta = ref(null);
const smsTestTo = ref('');
const smsSending = ref(false);
const smsReady = computed(() => !!(smsMeta.value && smsMeta.value.configured));
const smsProviderLabel = computed(() => ({
  console: 'حالت توسعه', kavenegar: 'کاوه‌نگار', smsir: 'SMS.ir', ghasedak: 'قاصدک', melipayamak: 'ملی پیامک',
}[smsMeta.value?.provider] || smsMeta.value?.provider || '—'));

const SMS_TAGS = { 'order-customer': 'تأیید سفارش', 'order-admin': 'اطلاع به مدیر', 'status-change': 'تغییر وضعیت', test: 'تست', send: 'ارسال' };
const smsTagLabel = t => SMS_TAGS[t] || t || '—';

async function loadSms() {
  const r = await adminSmsLogApi(50);
  if (!r) return;
  smsMeta.value = r.provider || null;
  smsRows.value = r.results || [];
}

async function sendTestSms() {
  const p = toEn(smsTestTo.value).replace(/\D/g, '');
  if (!/^09\d{9}$/.test(p)) return toast('شمارهٔ معتبر ۰۹… وارد کنید', 'err');
  smsSending.value = true;
  const r = await adminSmsTestApi(p);
  smsSending.value = false;
  if (!r) return toast('اتصال به سرور برقرار نشد', 'err');
  toast(r.ok && r.sent ? 'پیامک تست ارسال شد 📩' : 'ارسال پیامک ناموفق بود — تنظیمات پنل پیامک را بررسی کنید', r.ok && r.sent ? 'ok' : 'err');
  loadSms();
}

function loadAll() { loadStats(); loadProducts(); loadOrders(); loadUsers(); loadSms(); }
onMounted(() => { if (auth.isAdmin) loadAll(); });
watch(() => auth.isAdmin, v => { if (v) loadAll(); });
</script>

<style scoped>
.admin-login{max-width:460px;margin:0 auto}
.admin-stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:16px 0}
.admin-tabs{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.admin-tabs button{padding:9px 18px;border-radius:12px;font-weight:700;font-size:.88rem;background:var(--bg-warm);color:var(--ink-2);border:1px solid var(--line)}
.admin-tabs button.on{background:var(--brand-050);color:var(--brand-700);border-color:var(--brand-100)}
.admin-card{background:#fff;border:1px solid var(--line);border-radius:var(--r-md);box-shadow:var(--sh-sm);padding:14px}
.admin-toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
.sync-chip{font-size:.72rem;padding:6px 12px;border-radius:999px;font-weight:700}
.sync-chip.on{background:var(--brand-050);color:var(--brand-700);border:1px solid var(--brand-100)}
.sync-chip.off{background:var(--bg-warm);color:var(--ink-3);border:1px solid var(--line)}
.tbl-wrap{overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;font-size:.82rem;min-width:640px}
.tbl th{background:var(--bg-warm);padding:9px 10px;text-align:start;color:var(--ink-2);font-size:.76rem;white-space:nowrap}
.tbl td{padding:9px 10px;border-top:1px solid var(--line);vertical-align:middle}
.td-p{display:flex;align-items:center;gap:9px;min-width:200px}
.td-p img{width:38px;height:38px;border-radius:9px;object-fit:cover;flex:none}
.td-p small{display:block;color:var(--ink-3)}
.td-acts{white-space:nowrap}
.td-acts .del{color:var(--red);border-color:#f7cdc9}
.td-items{max-width:280px;font-size:.74rem;color:var(--ink-2)}
.sms-head{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap}
.chk{display:flex;align-items:center;gap:8px;font-size:.84rem;color:var(--ink-2)}
.od-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;font-size:.84rem;margin-bottom:12px}
.od-grid b{color:var(--ink-3);font-weight:600;margin-inline-end:4px}
.badge-hide{background:var(--bg-warm);color:var(--ink-3);border:1px solid var(--line);border-radius:999px;font-size:.66rem;padding:1px 8px;margin-inline-start:6px}
.sms-hint{font-size:.78rem;color:var(--ink-2);background:var(--bg-warm);border:1px dashed var(--line);border-radius:12px;padding:10px 14px;margin-bottom:12px;line-height:2}
.sms-hint code{background:#fff;border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:.74rem}
.sms-test{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
@media(max-width:767px){.admin-stats{grid-template-columns:repeat(2,1fr)}.od-grid{grid-template-columns:1fr}}
</style>
