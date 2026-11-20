<template>
  <div class="section">
    <div class="container" style="max-width:860px">
      <nav class="crumbs" aria-label="مسیر صفحه">
        <RouterLink to="/">خانه</RouterLink> ‹ <RouterLink to="/cart">سبد خرید</RouterLink> ‹ <span>تکمیل خرید</span>
      </nav>
      <div class="co-steps">
        <span class="co-step" :class="{ on: step === 0, done: step > 0 }" data-n="۱">ورود / ثبت‌نام</span>
        <span class="co-step" :class="{ on: step === 1, done: step > 1 }" data-n="۲">اطلاعات ارسال</span>
        <span class="co-step" :class="{ on: step === 2, done: step > 2 }" data-n="۳">فاکتور و ثبت</span>
        <span class="co-step" :class="{ on: step === 3 }" data-n="۴">تکمیل سفارش</span>
      </div>

      <!-- گام ۱: شمارهٔ موبایل → ورود یا ساخت حساب -->
      <div v-if="step === 0" class="modal-body" style="background:#fff;border-radius:var(--r-md)">
        <form class="auth-form" @submit.prevent="onIdentity">
          <div class="fld w">
            <label>شماره موبایل شما *</label>
            <input v-model="idPhone" type="tel" inputmode="tel" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="rtl" autocomplete="username" :disabled="phase !== 'phone'">
          </div>
          <template v-if="phase === 'login'">
            <div class="id-note ok">حسابی با این شماره دارید ✅ — رمز عبورتان را وارد کنید.</div>
            <div class="fld w"><label>رمز عبور</label><input ref="passInput" v-model="idPass" type="password" autocomplete="current-password"></div>
          </template>
          <template v-else-if="phase === 'register'">
            <div class="id-note">حسابی با این شماره پیدا نشد؛ با تعیین یک رمز عبور همین حالا برایتان ساخته می‌شود.</div>
            <div class="fld w"><label>نام و نام خانوادگی *</label><input v-model="idName" type="text" autocomplete="name" placeholder="مثلاً سارا محمدی"></div>
            <div class="fld w"><label>رمز عبور (حداقل ۴ کاراکتر) *</label><input v-model="idPass" type="password" autocomplete="new-password"></div>
          </template>
          <button class="btn btn-brand btn-lg btn-block co-pay-btn" type="submit" :disabled="busy">{{ idLabel }}</button>
          <button v-if="phase !== 'phone'" type="button" class="btn btn-light btn-sm btn-block" @click="resetIdentity">تغییر شماره</button>
        </form>
      </div>

      <!-- گام ۲: اطلاعات ارسال -->
      <div v-else-if="step === 1" class="modal-body" style="background:#fff;border-radius:var(--r-md)">
        <div class="f-grid c2">
          <div class="fld w"><label>نام و نام خانوادگی گیرنده *</label><input v-model="f.name" type="text" placeholder="مثلاً سارا محمدی"></div>
          <div class="fld w"><label>موبایل گیرنده *</label><input v-model="f.phone" type="tel" inputmode="tel" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="rtl"></div>
          <div class="fld w"><label>استان</label>
            <select v-model="f.prov">
              <option>تهران</option><option>البرز</option><option>اصفهان</option><option>فارس</option>
              <option>خراسان رضوی</option><option>آذربایجان شرقی</option><option>سایر استان‌ها</option>
            </select>
          </div>
          <div class="fld w"><label>شهر</label><input v-model="f.city" type="text" placeholder="مثلاً تهران"></div>
          <div class="fld w" style="grid-column:1/-1"><label>آدرس کامل پستی *</label><textarea v-model="f.addr" rows="2" placeholder="خیابان، کوچه، پلاک، واحد…"></textarea></div>
          <div class="fld w" style="grid-column:1/-1"><label>توضیح سفارش (اختیاری)</label><input v-model="f.note" type="text" maxlength="300" placeholder="مثلاً زمان مناسب تحویل"></div>
        </div>
        <h4 style="margin:16px 0 10px;font-size:.92rem">روش ارسال:</h4>
        <div class="ship-opts">
          <label v-for="o in shipMethods" :key="o.type" class="ship-opt" :class="{ on: shipType === o.type }">
            <input v-model="shipType" type="radio" name="ship" :value="o.type">
            <span><b>{{ o.label }}</b><span>{{ o.hint }}</span></span>
            <span class="pr" :class="{ free: shipFree || !o.cost }">{{ (shipFree || !o.cost) ? 'رایگان 🎉' : money(o.cost) }}</span>
          </label>
        </div>
        <button class="btn btn-brand btn-lg btn-block co-pay-btn" @click="next">ادامه و مشاهده فاکتور</button>
      </div>

      <!-- گام ۳: فاکتور، کد تخفیف و ثبت -->
      <div v-else-if="step === 2" class="modal-body" style="background:#fff;border-radius:var(--r-md)">
        <div class="co-summary">
          <b style="display:block;margin-bottom:8px">فاکتور سفارش شما</b>
          <div v-for="c in cart.items" :key="c.pid + '-' + c.w" style="display:flex;justify-content:space-between;gap:8px;font-size:.82rem;padding:3px 0">
            <span>{{ prod(c.pid)?.name }} <small style="color:var(--ink-3)">({{ weightLabel(c.w, prod(c.pid)?.unit) }} × {{ toFa(c.qty) }})</small></span>
            <b>{{ money(priceOf(prod(c.pid), c.w) * c.qty) }}</b>
          </div>
          <div style="border-top:1px dashed var(--line);margin:8px 0;padding-top:8px"></div>
          <div style="display:flex;justify-content:space-between"><span>جمع کالاها</span><b>{{ money(cartSub) }}</b></div>
          <div v-if="couponVal.off" style="display:flex;justify-content:space-between;color:var(--red)"><span>تخفیف ({{ cart.coupon }})</span><b>−{{ money(couponVal.off) }}</b></div>
          <div style="display:flex;justify-content:space-between">
            <span>ارسال ({{ shipOpt.label }} — {{ shipOpt.days }})</span>
            <b>{{ payShipCost === 0 ? 'رایگان 🎉' : money(payShipCost) }}</b>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:1rem;padding-top:8px"><b>قابل پرداخت</b><b style="color:var(--brand-700)">{{ money(payTotal) }} تومان</b></div>
          <div style="margin-top:10px;font-size:.78rem;color:var(--ink-2)">📍 {{ f.prov }}، {{ f.city }}، {{ f.addr }} — {{ f.name }} ({{ toFa(phoneEn) }})</div>
        </div>
        <!-- کد تخفیف (فقط بعد از ورود) -->
        <div class="coupon-row" style="margin:12px 0">
          <input v-model="couponInput" class="fld" type="text" :placeholder="cart.coupon ? 'کد اعمال‌شده: ' + cart.coupon : 'کد تخفیف…'" aria-label="کد تخفیف" @keydown.enter.prevent="useCoupon">
          <button class="btn btn-brand btn-sm" type="button" @click="useCoupon">اعمال</button>
        </div>
        <div v-if="errMsg" class="id-note err">{{ errMsg }}</div>
        <button class="btn btn-brand btn-lg btn-block co-pay-btn" :disabled="paying" @click="pay">
          <svg class="icon"><use href="#i-check" /></svg> {{ paying ? 'در حال ثبت سفارش… ⏳' : 'ثبت نهایی سفارش' }}
        </button>
        <p class="pay-note"><svg class="icon"><use href="#i-shield" /></svg> با ثبت سفارش، <RouterLink to="/page/terms">قوانین فروشگاه</RouterLink> را می‌پذیرید.</p>
      </div>

      <!-- گام ۴: موفقیت (+ پرداخت آنلاین زیبال اگر درگاه فعال باشد) -->
      <div v-else class="modal-body" style="background:#fff;border-radius:var(--r-md)">
        <div class="co-success">
          <div class="ok-ic"><svg class="icon"><use href="#i-check" /></svg></div>
          <h3 v-if="payEnabled && placed?.fromServer">سفارش ثبت شد؛ در انتظار پرداخت ⏳</h3>
          <h3 v-else>سفارش شما با موفقیت ثبت شد! 🎉</h3>
          <p style="font-size:.86rem;color:var(--ink-2)">کد سفارش شما:</p>
          <span class="ord-code">{{ placed?.code }}</span>
          <div class="sms-note"><svg class="icon"><use href="#i-sms" /></svg> <span>پیامک تأیید سفارش حاوی کد پیگیری به شماره <b>{{ toFa(auth.user?.phone || placed?.addr?.phone || '') }}</b> ارسال می‌شود.</span></div>

          <!-- پرداخت آنلاین با زیبال (فقط سفارش‌های سمت سرور وقتی درگاه فعال است) -->
          <div v-if="payEnabled && placed?.fromServer" class="zibal-box">
            <div class="zibal-sum">
              <span>مبلغ قابل پرداخت</span>
              <b>{{ money(placed?.total) }} تومان</b>
            </div>
            <button class="btn btn-brand btn-lg btn-block co-pay-btn" :disabled="zibalBusy" @click="startZibalPay">
              {{ zibalBusy ? 'در حال اتصال به درگاه… ⏳' : 'پرداخت آنلاین با زیبال 💳' }}
            </button>
            <button v-if="zibalErr" class="btn btn-light btn-sm btn-block" @click="startZibalPay">تلاش دوباره</button>
            <div v-if="zibalErr" class="id-note err">{{ zibalErr }}</div>
            <p class="pay-note">پرداخت امن از طریق درگاه رسمی زیبال؛ پس از پرداخت به سایت برمی‌گردید.</p>
          </div>

          <div class="co-actions">
            <RouterLink class="btn btn-brand" :to="{ path: '/track', query: { code: placed?.code } }">پیگیری سفارش</RouterLink>
            <RouterLink class="btn btn-gold" to="/account">مشاهده پنل کاربری</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { toFa, toEn, money, weightLabel, priceOf } from '../data/site';
import { prod } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import { cart, cartSub, couponVal, shipFree, applyCoupon } from '../stores/cart';
import { placeOrder, placeOrderServer } from '../stores/orders';
import { toast } from '../stores/ui';
import { auth, login, register } from '../stores/auth';
import { shipMethods } from '../stores/shop';
import { apiState, phoneCheckApi, payConfigApi, payStartApi } from '../services/api';

useSeo({ title: 'تکمیل خرید', description: 'تکمیل اطلاعات ارسال و ثبت سفارش از فروشگاه خانم گل', path: '/checkout' });

const router = useRouter();
const needAccount = () => apiState.enabled && !auth.user;     // ثبت سفارش فقط با حساب کاربری
const step = ref(needAccount() ? 0 : 1);
const paying = ref(false);
const placed = ref(null);
const errMsg = ref('');
const shipType = ref('');
const f = reactive({ name: '', phone: '', prov: 'تهران', city: '', addr: '', note: '' });
const couponInput = ref('');

/* ---- درگاه پرداخت زیبال (فقط وقتی بک‌اند فعال و درگاه روشن باشد) ---- */
const payEnabled = ref(false);
const zibalBusy = ref(false);
const zibalErr = ref('');

async function startZibalPay() {
  zibalErr.value = '';
  zibalBusy.value = true;
  try {
    const r = await payStartApi(placed.value.code);
    if (r.ok && r.payUrl) {
      window.location.assign(r.payUrl);          // ریدایرکت به درگاه زیبال
      return;
    }
    zibalErr.value = r.msg || 'اتصال به درگاه پرداخت انجام نشد';
  } catch { zibalErr.value = 'اتصال به سرور برقرار نشد؛ دوباره تلاش کنید'; }
  zibalBusy.value = false;
}


/* ---- گام ۱: شناسایی با شماره موبایل ---- */
const phase = ref('phone');            // phone → login | register
const idPhone = ref(''), idPass = ref(''), idName = ref('');
const busy = ref(false);
const passInput = ref(null);
const idLabel = computed(() => (busy.value ? 'لطفاً صبر کنید…' : phase.value === 'phone' ? 'ادامه' : phase.value === 'login' ? 'ورود و ادامه ثبت سفارش' : 'ساخت حساب و ادامه ثبت سفارش'));
function resetIdentity() { phase.value = 'phone'; idPass.value = ''; idName.value = ''; }

async function onIdentity() {
  const p = toEn(idPhone.value).replace(/\D/g, '');
  if (!/^09\d{9}$/.test(p)) return toast('شماره موبایل معتبر وارد کنید (۰۹…)', 'err');
  busy.value = true;
  try {
    if (phase.value === 'phone') {
      const r = await phoneCheckApi(p);
      if (!r.ok) return toast(r.msg || 'بررسی شماره انجام نشد؛ دوباره تلاش کنید', 'err');
      phase.value = r.exists ? 'login' : 'register';
      await nextTick();
      passInput.value && passInput.value.focus();
      return;
    }
    const res = phase.value === 'login' ? await login(p, idPass.value) : await register(idName.value, p, idPass.value);
    if (!res.ok) return toast(res.msg, 'err');
    toast(phase.value === 'login' ? 'خوش آمدید! 🌰' : 'حساب شما ساخته شد 🌰', 'gold');
    fillFromAccount();
    step.value = 1;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } finally { busy.value = false; }
}

function fillFromAccount() {
  if (auth.user) { f.name = f.name || auth.user.name; f.phone = f.phone || auth.user.phone; }
}

onMounted(() => {
  if (!cart.items.length && step.value < 3) { toast('سبد خرید خالی است', 'err'); router.replace('/cart'); return; }
  fillFromAccount();
  shipType.value = shipMethods.value[0]?.type || '';
  if (apiState.enabled) payConfigApi().then(r => { payEnabled.value = !!r?.enabled; }).catch(() => {});
});

const shipOpt = computed(() => shipMethods.value.find(m => m.type === shipType.value) || shipMethods.value[0] || { label: '', days: '', cost: 0 });
const phoneEn = computed(() => toEn(f.phone).replace(/\D/g, ''));
const payShipCost = computed(() => (shipFree.value ? 0 : shipOpt.value.cost));
const payTotal = computed(() => Math.max(0, cartSub.value - couponVal.value.off + payShipCost.value));

function next() {
  if (!f.name.trim()) return toast('نام و نام خانوادگی را وارد کنید', 'err');
  if (!/^09\d{9}$/.test(phoneEn.value)) return toast('شماره موبایل معتبر وارد کنید (۰۹…)', 'err');
  if (!f.city.trim()) return toast('شهر را وارد کنید', 'err');
  if (f.addr.trim().length < 10) return toast('آدرس کامل پستی را وارد کنید (حداقل ۱۰ نویسه: خیابان، کوچه، پلاک)', 'err');
  if (!shipType.value) return toast('روش ارسال را انتخاب کنید', 'err');
  errMsg.value = '';
  step.value = 2;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function useCoupon() {
  if (!couponInput.value.trim()) return;
  await applyCoupon(couponInput.value);
  couponInput.value = '';
}

async function pay() {
  errMsg.value = '';
  paying.value = true;
  try {
    let order;
    if (apiState.enabled) {
      const r = await placeOrderServer({ addr: { ...f, phone: phoneEn.value }, shipType: shipType.value, note: f.note });
      if (!r.ok) {
        if (r.status === 401) { step.value = 0; return toast('نشست شما منقضی شده؛ دوباره وارد شوید', 'err'); }
        if (/آدرس|شهر|نام|موبایل|شماره/.test(r.msg || '')) { step.value = 1; window.scrollTo({ top: 0, behavior: 'smooth' }); return toast(r.msg, 'err', 5200); }
        errMsg.value = r.msg;
        return toast(r.msg, 'err', 5200);
      }
      order = r.order;
    } else {
      order = placeOrder({ addr: { ...f, phone: phoneEn.value }, shipType: shipType.value });
    }
    placed.value = order;
    step.value = 3;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (order.fromServer) {                       // درگاه روشن است؟ مستقیم به درگاه برویم
      const c = await payConfigApi().catch(() => null);
      payEnabled.value = !!c?.enabled;
      if (payEnabled.value) { paying.value = true; await startZibalPay(); }
    }
  } finally { paying.value = false; }
}
</script>


<style scoped>
.zibal-box{margin:16px auto 6px;max-width:420px;background:var(--brand-050);border:1.5px solid var(--brand-100);border-radius:var(--r-md);padding:16px 14px}
.zibal-box .co-pay-btn{margin-top:10px}
.zibal-box .id-note.err{margin-top:10px}
.zibal-box .btn-light{margin-top:10px}
.zibal-sum{display:flex;justify-content:space-between;align-items:center;font-size:.88rem;padding:8px 4px;background:#fff;border-radius:10px;border:1px solid var(--line)}
.zibal-sum b{color:var(--brand-700)}
</style>
