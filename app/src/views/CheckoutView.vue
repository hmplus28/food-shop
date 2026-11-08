<template>
  <div class="section">
    <div class="container" style="max-width:860px">
      <nav class="crumbs" aria-label="مسیر صفحه">
        <RouterLink to="/">خانه</RouterLink> ‹ <RouterLink to="/cart">سبد خرید</RouterLink> ‹ <span>تکمیل خرید</span>
      </nav>
      <div class="co-steps">
        <span class="co-step" :class="{ on: step === 0, done: step > 0 }" data-n="۱">اطلاعات ارسال</span>
        <span class="co-step" :class="{ on: step === 1, done: step > 1 }" data-n="۲">پرداخت</span>
        <span class="co-step" :class="{ on: step === 2, done: step > 2 }" data-n="۳">تکمیل سفارش</span>
      </div>

      <!-- گام ۱: اطلاعات ارسال -->
      <div v-if="step === 0" class="modal-body" style="background:#fff;border-radius:var(--r-md)">
        <div class="f-grid c2">
          <div class="fld w"><label>نام و نام خانوادگی *</label><input v-model="f.name" type="text" placeholder="مثلاً سارا محمدی"></div>
          <div class="fld w"><label>شماره موبایل *</label><input v-model="f.phone" type="tel" inputmode="tel" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="rtl"></div>
          <div class="fld w"><label>استان</label>
            <select v-model="f.prov">
              <option>تهران</option><option>البرز</option><option>اصفهان</option><option>فارس</option>
              <option>خراسان رضوی</option><option>آذربایجان شرقی</option><option>سایر استان‌ها</option>
            </select>
          </div>
          <div class="fld w"><label>شهر</label><input v-model="f.city" type="text" placeholder="مثلاً تهران"></div>
          <div class="fld w" style="grid-column:1/-1"><label>آدرس کامل پستی *</label><textarea v-model="f.addr" rows="2" placeholder="خیابان، کوچه، پلاک، واحد…"></textarea></div>
        </div>
        <h4 style="margin:16px 0 10px;font-size:.92rem">روش ارسال:</h4>
        <div class="ship-opts">
          <label v-for="o in SHIP_OPTIONS" :key="o.type" class="ship-opt" :class="{ on: shipType === o.type }">
            <input v-model="shipType" type="radio" name="ship" :value="o.type">
            <span><b>{{ o.label }}</b><span>{{ o.hint }}</span></span>
            <span class="pr" :class="{ free: shipFree }">{{ shipFree ? 'رایگان 🎉' : money(o.cost) }}</span>
          </label>
        </div>
        <button class="btn btn-brand btn-lg btn-block co-pay-btn" @click="next">ادامه و مشاهده فاکتور</button>
      </div>

      <!-- گام ۲: فاکتور و پرداخت -->
      <div v-else-if="step === 1" class="modal-body" style="background:#fff;border-radius:var(--r-md)">
        <div class="co-summary">
          <b style="display:block;margin-bottom:8px">فاکتور سفارش شما</b>
          <div v-for="c in cart.items" :key="c.pid + '-' + c.w" style="display:flex;justify-content:space-between;gap:8px;font-size:.82rem;padding:3px 0">
            <span>{{ prod(c.pid)?.name }} <small style="color:var(--ink-3)">({{ weightLabel(c.w) }} × {{ toFa(c.qty) }})</small></span>
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
        <div class="sms-note" style="background:var(--gold-050);border-color:var(--gold-100);color:var(--gold-600)">
          <svg class="icon"><use href="#i-lock" /></svg> پرداخت به‌صورت امن از طریق درگاه بانکی انجام می‌شود (نسخه نمایشی؛ پرداخت واقعی انجام نمی‌شود).
        </div>
        <button class="btn btn-brand btn-lg btn-block co-pay-btn" :disabled="paying" @click="pay">
          <svg class="icon"><use href="#i-lock" /></svg> {{ paying ? 'در حال اتصال به درگاه پرداخت… ⏳' : 'پرداخت و ثبت نهایی سفارش' }}
        </button>
        <p class="pay-note"><svg class="icon"><use href="#i-shield" /></svg> با ثبت سفارش، قوانین فروشگاه خانم گل را می‌پذیرید.</p>
      </div>

      <!-- گام ۳: موفقیت -->
      <div v-else class="modal-body" style="background:#fff;border-radius:var(--r-md)">
        <div class="co-success">
          <div class="ok-ic"><svg class="icon"><use href="#i-check" /></svg></div>
          <h3>سفارش شما با موفقیت ثبت شد! 🎉</h3>
          <p style="font-size:.86rem;color:var(--ink-2)">کد سفارش شما:</p>
          <span class="ord-code">{{ placed?.code }}</span>
          <div class="sms-note"><svg class="icon"><use href="#i-sms" /></svg> <span>پیامک تأیید سفارش حاوی کد پیگیری به شماره <b>{{ toFa(placed?.addr?.phone || '') }}</b> ارسال شد. وضعیت سفارش هر لحظه از قسمت «پیگیری سفارش» قابل مشاهده است.</span></div>
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
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { toFa, toEn, money, weightLabel, priceOf, SHIP_OPTIONS, LS } from '../data/site';
import { prod } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import { cart, cartSub, couponVal, couponDef, shipFree } from '../stores/cart';
import { placeOrder } from '../stores/orders';
import { toast } from '../stores/ui';
import { auth } from '../stores/auth';

useSeo({ title: 'تکمیل خرید', description: 'تکمیل اطلاعات ارسال و پرداخت امن سفارش از فروشگاه خانم گل', path: '/checkout' });

const router = useRouter();
const step = ref(0);
const paying = ref(false);
const placed = ref(null);
const shipType = ref('peyk');
const f = reactive({ name: '', phone: '', prov: 'تهران', city: '', addr: '' });

onMounted(() => {
  if (!cart.items.length && step.value < 2) { toast('سبد خرید خالی است', 'err'); router.replace('/cart'); return; }
  if (auth.user) { f.name = f.name || auth.user.name; f.phone = f.phone || auth.user.phone; }
  const last = (LS.get('orders', []))[0];
  if (last?.addr) { f.name = f.name || last.addr.name || ''; f.phone = f.phone || last.addr.phone || ''; }
});

const shipOpt = computed(() => SHIP_OPTIONS.find(s => s.type === shipType.value) || SHIP_OPTIONS[0]);
const phoneEn = computed(() => toEn(f.phone).replace(/\D/g, ''));
const payShipCost = computed(() => (shipFree.value ? 0 : shipOpt.value.cost));
const payTotal = computed(() => Math.max(0, cartSub.value - couponVal.value.off + payShipCost.value));

function next() {
  if (!f.name.trim()) return toast('نام و نام خانوادگی را وارد کنید', 'err');
  if (!/^09\d{9}$/.test(phoneEn.value)) return toast('شماره موبایل معتبر وارد کنید (۰۹…)', 'err');
  if (!f.addr.trim() || !f.city.trim()) return toast('شهر و آدرس کامل را وارد کنید', 'err');
  step.value = 1;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function pay() {
  paying.value = true;
  setTimeout(() => {
    placed.value = placeOrder({ addr: { ...f, phone: phoneEn.value }, shipType: shipType.value });
    paying.value = false;
    step.value = 2;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => toast(`📱 پیامک تأیید سفارش ${placed.value.code} به شماره ${toFa(placed.value.addr.phone)} ارسال شد`, 'gold', 5200), 700);
  }, 1500);
}
</script>
