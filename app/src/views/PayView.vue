<template>
  <div class="section">
    <div class="container" style="max-width:560px">
      <nav class="crumbs" aria-label="مسیر صفحه"><RouterLink to="/">خانه</RouterLink> ‹ <span>نتیجهٔ پرداخت</span></nav>
      <div class="modal-body" style="background:#fff;border-radius:var(--r-md);margin-top:10px">

        <!-- در حال بررسی تراکنش -->
        <div v-if="phase === 'checking'" class="co-success">
          <div class="pay-spin"></div>
          <h3 style="font-size:1.02rem">در حال بررسی تراکنش…</h3>
          <p style="font-size:.84rem;color:var(--ink-2)">لطفاً این صفحه را نبندید؛ وضعیت پرداخت از درگاه زیبال بررسی می‌شود.</p>
        </div>

        <!-- پرداخت موفق -->
        <div v-else-if="phase === 'paid'" class="co-success">
          <div class="ok-ic"><svg class="icon"><use href="#i-check" /></svg></div>
          <h3>پرداخت با موفقیت انجام شد! 🎉</h3>
          <p style="font-size:.86rem;color:var(--ink-2)">سفارش شما پرداخت شد و در صف آماده‌سازی قرار گرفت:</p>
          <span class="ord-code">{{ orderCode }}</span>
          <div class="pay-sum"><span>مبلغ پرداخت‌شده</span><b>{{ money(paidAmount) }} تومان</b></div>
          <div class="sms-note"><svg class="icon"><use href="#i-sms" /></svg> <span>پیامک تأیید پرداخت برایتان ارسال می‌شود.</span></div>
          <div class="co-actions">
            <RouterLink class="btn btn-brand" :to="{ path: '/track', query: { code: orderCode } }">پیگیری سفارش</RouterLink>
            <RouterLink class="btn btn-gold" to="/">بازگشت به فروشگاه</RouterLink>
          </div>
        </div>

        <!-- پرداخت ناموفق / لغو -->
        <div v-else class="co-success">
          <div class="ok-ic fail"><svg class="icon"><use href="#i-x" /></svg></div>
          <h3>پرداخت انجام نشد</h3>
          <div class="id-note err" style="text-align:right">{{ failMsg }}</div>
          <template v-if="orderCode">
            <p style="font-size:.84rem;color:var(--ink-2)">نگران نباشید؛ سفارش <b>{{ orderCode }}</b> ثبت است و می‌توانید دوباره پرداخت کنید:</p>
            <button class="btn btn-brand btn-lg btn-block co-pay-btn" :disabled="retrying" @click="retryPay">
              {{ retrying ? 'در حال اتصال به درگاه… ⏳' : 'تلاش دوباره برای پرداخت 💳' }}
            </button>
            <div class="co-actions">
              <RouterLink class="btn btn-light" :to="{ path: '/track', query: { code: orderCode } }">پیگیری سفارش</RouterLink>
              <RouterLink class="btn btn-light" to="/account">پنل کاربری</RouterLink>
            </div>
          </template>
          <div v-else class="co-actions">
            <RouterLink class="btn btn-brand" to="/">بازگشت به فروشگاه</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useSeo } from '../composables/useSeo';
import { money } from '../data/site';
import { payVerifyApi, payStartApi } from '../services/api';

useSeo({
  title: 'نتیجهٔ پرداخت', path: '/pay',
  description: 'نتیجهٔ پرداخت آنلاین سفارش از درگاه زیبال در فروشگاه خانم گل',
});

const route = useRoute();
const phase = ref('checking');          // checking | paid | failed
const orderCode = ref('');
const paidAmount = ref(0);
const failMsg = ref('');
const retrying = ref(false);

const okBody = r => {
  orderCode.value = r.order?.code || orderCode.value || String(route.query.order || '');
  paidAmount.value = Number(r.amount) || 0;
  phase.value = 'paid';
};

async function verify(trackId) {
  phase.value = 'checking';
  const r = await payVerifyApi(String(route.query.order || ''), trackId);
  if (r.ok && r.state === 'paid') return okBody(r);
  failMsg.value = r.msg || 'تأیید تراکنش انجام نشد';
  phase.value = 'failed';
}

async function retryPay() {
  retrying.value = true;
  const r = await payStartApi(orderCode.value);
  if (r.ok && r.payUrl) { window.location.assign(r.payUrl); return; }
  retrying.value = false;
  failMsg.value = r.msg || 'اتصال به درگاه پرداخت انجام نشد';
}

onMounted(() => {
  orderCode.value = String(route.query.order || '');
  const trackId = String(route.query.trackId || route.query.TrackId || '').trim();
  const success = String(route.query.success ?? '1') !== '0';
  if (trackId && success) { verify(trackId); return; }
  if (trackId && !success) { failMsg.value = 'پرداخت در درگاه زیبال ناتمام ماند یا لغو شد؛ می‌توانید دوباره تلاش کنید.'; }
  else { failMsg.value = 'اطلاعات بازگشت از درگاه پرداخت کامل نیست.'; }
  phase.value = 'failed';
});
</script>

<style scoped>
.ok-ic.fail{background:#fdeceb;color:var(--red)}
.pay-spin{width:58px;height:58px;margin:26px auto 18px;border-radius:50%;border:4px solid var(--brand-050);border-top-color:var(--brand);animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.pay-sum{display:flex;justify-content:space-between;align-items:center;max-width:300px;margin:12px auto;padding:8px 14px;background:var(--brand-050);border:1px solid var(--brand-100);border-radius:12px;font-size:.9rem}
.pay-sum b{color:var(--brand-700)}
.ok-ic.fail :deep(svg), .ok-ic svg{width:42px;height:42px}
</style>
