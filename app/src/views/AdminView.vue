<template>
  <div class="section">
    <div class="container">
      <!-- ورود مدیر -->
      <div v-if="!auth.isAdmin" class="admin-login">
        <div class="auth-card">
          <h1 style="font-size:1.1rem;display:flex;align-items:center;gap:8px"><svg class="icon"><use href="#i-lock" /></svg> ورود مدیر فروشگاه</h1>
          <p style="font-size:.8rem;color:var(--ink-3);margin:6px 0 16px">اگر بک‌اند فعال باشد احراز هویت سمت سرور انجام می‌شود؛ در غیر این صورت نسخهٔ نمایشی محلی (admin / admin1234) استفاده می‌شود.</p>
          <form class="auth-form" @submit.prevent="doAdmin">
            <div class="fld w"><label>نام کاربری</label><input v-model="au" type="text" autocomplete="username"></div>
            <div class="fld w"><label>رمز عبور</label><input v-model="ap" type="password" autocomplete="current-password"></div>
            <button class="btn btn-brand btn-block" type="submit">ورود به پنل مدیریت</button>
          </form>
        </div>
      </div>

      <!-- پنل مدیریت -->
      <template v-else>
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-box" /></svg></span>
            <div><h1 class="sec-title">پنل <i>مدیریت</i> خانم گل</h1><span class="sec-sub">مدیریت محصولات، سفارش‌ها، وضعیت ارسال و پنل پیامک</span></div></span>
          <div class="sec-actions"><button class="btn btn-light btn-sm" @click="adminLogout(); toast('از پنل مدیر خارج شدید', 'ok')"><svg class="icon"><use href="#i-x" /></svg> خروج</button></div>
        </div>

        <div class="admin-stats">
          <div class="up-stat"><b>{{ toFa(statProducts) }}</b><span>محصول</span></div>
          <div class="up-stat"><b>{{ toFa(statOrders) }}</b><span>سفارش</span></div>
          <div class="up-stat"><b>{{ money(statRevenue) }}</b><span>فروش کل (تومان)</span></div>
          <div class="up-stat"><b>{{ toFa(statLow) }}</b><span>موجودی کم (&lt;۱۰)</span></div>
        </div>

        <div class="admin-tabs">
          <button :class="{ on: tab === 'products' }" @click="tab = 'products'">مدیریت محصولات</button>
          <button :class="{ on: tab === 'orders' }" @click="tab = 'orders'">مدیریت سفارش‌ها</button>
          <button :class="{ on: tab === 'sms' }" @click="tab = 'sms'">پنل پیامک</button>
        </div>

        <!-- محصولات -->
        <div v-if="tab === 'products'" class="admin-card">
          <div class="admin-toolbar">
            <button class="btn btn-gold btn-sm" @click="startNew"><svg class="icon"><use href="#i-plus" /></svg> افزودن محصول</button>
            <button class="btn btn-light btn-sm" @click="resetAll">بازگردانی محصولات پیش‌فرض</button>
            <span class="sync-chip" :class="serverMode ? 'on' : 'off'">{{ serverMode ? '● همگام با بک‌اند' : '○ ذخیرهٔ محلی مرورگر' }}</span>
          </div>
          <div class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>محصول</th><th>دسته</th><th>قیمت پایه (کیلو)</th><th>تخفیف</th><th>موجودی</th><th></th></tr></thead>
              <tbody>
                <tr v-for="p in products" :key="p.id">
                  <td class="td-p"><img :src="p.img" alt=""><div><b>{{ p.name }}</b><small>{{ p.grade }}</small></div></td>
                  <td>{{ catOf(p.cat)?.name || '—' }}</td>
                  <td>{{ money(p.price) }}</td>
                  <td>{{ p.disc ? '٪' + toFa(p.disc) : '—' }}</td>
                  <td><span class="tag" :class="p.stock >= 10 ? 'green' : 'red'">{{ toFa(p.stock) }}</span></td>
                  <td class="td-acts">
                    <button class="btn btn-light btn-sm" @click="startEdit(p)">ویرایش</button>
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
            <span class="sync-chip" :class="serverMode ? 'on' : 'off'">{{ serverMode ? '● سفارش‌ها از سرور' : '○ سفارش‌های محلی مرورگر' }}</span>
            <button v-if="serverMode" class="btn btn-light btn-sm" @click="loadServerData">به‌روزرسانی ⟳</button>
          </div>
          <div v-if="!displayOrders.length" class="up-empty"><svg class="icon"><use href="#i-doc" /></svg><p>هنوز سفارشی ثبت نشده است. بعد از ثبت سفارش از سمت مشتری‌ها این‌جا نمایش داده می‌شود.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>کد</th><th>تاریخ</th><th>اقلام</th><th>مبلغ</th><th>مشتری</th><th>وضعیت</th></tr></thead>
              <tbody>
                <tr v-for="o in displayOrders" :key="o.code">
                  <td><b>{{ o.code }}</b></td>
                  <td>{{ faDate(o.ts) }}</td>
                  <td class="td-items">{{ o.items.map(c => `${c.pname || prod(c.pid)?.name || '?'} (${weightLabel(c.w)}×${toFa(c.qty)})`).join(' + ') }}</td>
                  <td>{{ money(o.total) }}</td>
                  <td>{{ toFa(o.addr.phone) }}</td>
                  <td>
                    <select class="fld" style="padding:5px 8px;font-size:.78rem" :value="String(orderStep(o))" @change="changeStatus(o, Number($event.target.value))">
                      <option v-for="(s, i) in STATUS" :key="i" :value="String(i)">{{ s }}</option>
                    </select>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- پنل پیامک -->
        <div v-else class="admin-card">
          <div class="sms-head">
            <span class="sync-chip" :class="smsReady ? 'on' : 'off'">
              {{ smsReady ? `● سرویس پیامک: ${smsProviderLabel}` : '○ پنل پیامک متصل نیست (حالت توسعه)' }}
            </span>
            <button class="btn btn-light btn-sm" @click="loadSms">به‌روزرسانی ⟳</button>
          </div>

          <div v-if="!smsReady" class="sms-hint">
            برای اتصال پنل پیامک، در <code dir="ltr">backend/.env</code> مقدار <code dir="ltr">SMS_PROVIDER</code> و کلید سرویس‌دهنده (کاوه‌نگار / SMS.ir / قاصدک / ملی پیامک) را تنظیم کنید. تا آن موقع پیامک‌ها فقط در همین گزارش ثبت می‌شوند.
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
          <div class="fld w" style="grid-column:1/-1"><label>آدرس تصویر</label><input v-model="editing.img" type="url" dir="ltr"></div>
        </div>
        <button class="btn btn-brand btn-block" style="margin-top:12px" @click="save"><svg class="icon"><use href="#i-check" /></svg> ذخیره محصول</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { toFa, money, weightLabel, faDate, faTime, toEn } from '../data/site';
import { products, CATS, catOf, prod, persistProducts, resetProducts } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import { auth, adminLogin, adminLogout } from '../stores/auth';
import { orders as localOrders, setStatus, orderStep, STATUS, spentTotal } from '../stores/orders';
import { toast } from '../stores/ui';
import { apiState, adminStatsApi, ordersListApi, patchOrderStatusApi, adminSmsLogApi, adminSmsTestApi, productCreateApi, productUpdateApi, productDeleteApi } from '../services/api';

useSeo({ title: 'پنل مدیریت', description: 'پنل مدیریت فروشگاه خانم گل', path: '/admin' });

const tab = ref('products');
const au = ref(''), ap = ref('');
const editing = ref(null);

/* ---------- آمار: اول سرور، بعد محلی ---------- */
const serverStats = ref(null);
const serverMode = computed(() => !!serverStats.value);
const statProducts = computed(() => serverStats.value?.products ?? products.length);
const statOrders = computed(() => serverStats.value?.orders ?? localOrders.length);
const statRevenue = computed(() => serverStats.value?.revenue ?? spentTotal());
const statLow = computed(() => serverStats.value?.lowStock ?? products.filter(p => p.stock < 10).length);

async function loadServerData() {
  const [stats, list] = await Promise.all([adminStatsApi(), ordersListApi({ limit: 200 })]);
  if (stats) serverStats.value = stats;
  if (list) {
    remoteOrders.value = (list.results || []).map(mapServerOrder);
    const serverKeys = new Set(remoteOrders.value.flatMap(o => [o.code, o.client_code].filter(Boolean)));
    const extras = localOrders.filter(o => !serverKeys.has(o.code) && !serverKeys.has(o.remoteCode));
    remoteOrders.value.push(...extras.map(o => ({ ...o, _server: false })));
  }
}

/* ---------- سفارش‌ها ---------- */
const remoteOrders = ref([]);
const displayOrders = computed(() => (serverMode.value && remoteOrders.value.length) ? remoteOrders.value : localOrders);

function mapServerOrder(o) {
  return {
    code: o.code,
    client_code: o.client_code || '',
    ts: o.ts, status: o.status, sub: o.sub, off: o.off, coupon: o.coupon,
    shipCost: o.ship_cost, shipType: o.ship_type, shipLabel: o.ship_label, shipDays: o.ship_days,
    total: o.total,
    items: (o.items || []).map(c => ({ pid: c.pid, w: c.w, qty: c.qty, pname: c.name })),
    addr: o.addr || { phone: '' },
    _server: true,
  };
}

async function changeStatus(o, st) {
  if (o._server) {
    const doneOk = await patchOrderStatusApi(o.code, st);
    if (!doneOk) return toast('تغییر وضعیت روی سرور انجام نشد', 'err');
    o.status = st;
    toast(`وضعیت سفارش ${o.code} به «${STATUS[st]}» تغییر کرد (سرور)`, 'ok');
  } else {
    setStatus(o.code, st);
  }
}

/* ---------- محصولات: ذخیرهٔ محلی + ارسال به بک‌اند ---------- */
function startNew() {
  editing.value = { id: 0, name: '', cat: 'ajil', img: 'https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/66fd0cba7ee8.jpg', price: 1000000, weights: [250, 500, 1000, 2000], stock: 20, disc: 0, grade: 'درجه یک', rate: 4.5, sold: 0, tags: [], sec: [], desc: '' };
}
function startEdit(p) { editing.value = { ...p, tags: [...p.tags], sec: [...p.sec], weights: [...p.weights] }; }

async function save() {
  const e = editing.value;
  if (!e.name.trim()) return toast('نام محصول را وارد کنید', 'err');
  if (!e.price || e.price <= 0) return toast('قیمت پایه معتبر وارد کنید', 'err');
  const isNew = !e.id;
  if (isNew) { e.id = Math.max(100, ...products.map(p => p.id)) + 1; products.push(e); }
  else {
    const i = products.findIndex(p => p.id === e.id);
    if (i > -1) products.splice(i, 1, e);
  }
  persistProducts();
  editing.value = null;
  toast('محصول ذخیره شد ✅', 'ok');
  /* همگام‌سازی با بک‌اند (اگر فعال باشد) */
  if (apiState.enabled) {
    const res = isNew ? await productCreateApi(e) : await productUpdateApi(e.id, e);
    if (isNew && res && res.id) { e.id = res.id; persistProducts(); }   // شناسهٔ رسمی سرور
    toast(isNew ? (res ? 'محصول روی سرور هم ساخته شد' : 'همگام‌سازی سرور انجام نشد') : (res ? 'محصول روی سرور به‌روزرسانی شد' : 'همگام‌سازی سرور انجام نشد'), res ? 'ok' : 'err');
    if (res) loadServerData();
  }
}

async function del(p) {
  if (p.id <= 28 || (p.id >= 90 && p.id <= 96)) return toast('محصولات پایه فقط قابل ویرایش‌اند؛ برای حذف، موجودی را صفر کنید', 'err', 4600);
  const i = products.findIndex(x => x.id === p.id);
  if (i > -1) products.splice(i, 1);
  persistProducts();
  toast('محصول حذف شد', 'ok');
  if (apiState.enabled) {
    const okDel = await productDeleteApi(p.id);
    if (!okDel) toast('حذف روی سرور انجام نشد', 'err');
  }
}

function resetAll() {
  resetProducts();
  toast('محصولات پیش‌فرض بازگردانی شد', 'ok');
}

/* ---------- ورود مدیر ---------- */
async function doAdmin() {
  const res = await adminLogin(au.value, ap.value);
  if (!res.ok) return toast(res.msg, 'err');
  toast(res.server ? 'به پنل مدیریت خوش آمدید 👑 (احراز هویت سرور)' : 'به پنل مدیریت خوش آمدید 👑 (حالت نمایشی)', 'gold');
  await loadServerData();
  loadSms();
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

const SMS_TAGS = { otp: 'کد ورود', 'order-customer': 'تأیید سفارش', 'order-admin': 'اطلاع به مدیر', 'status-change': 'تغییر وضعیت', test: 'تست', send: 'ارسال' };
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
  toast(r.ok && r.sent ? 'پیامک تست ارسال شد 📩 (گزارش پایین صفحه)' : 'ارسال پیامک ناموفق بود — تنظیمات پنل پیامک را بررسی کنید', r.ok && r.sent ? 'ok' : 'err');
  loadSms();
}

onMounted(() => {
  if (auth.isAdmin) { loadServerData(); loadSms(); }
});
watch(tab, t => { if (t === 'sms') loadSms(); });
</script>

<style scoped>
.admin-login{max-width:460px;margin:0 auto}
.admin-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}
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
.sms-hint{font-size:.78rem;color:var(--ink-2);background:var(--bg-warm);border:1px dashed var(--line);border-radius:12px;padding:10px 14px;margin-bottom:12px;line-height:2}
.sms-hint code{background:#fff;border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:.74rem}
.sms-test{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
@media(max-width:767px){.admin-stats{grid-template-columns:repeat(2,1fr)}}
</style>
