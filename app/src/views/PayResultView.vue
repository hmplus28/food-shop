<template>
  <section class="section">
    <div class="container" style="max-width:560px">
      <div class="modal-body" style="background:#fff;border-radius:var(--r-md);text-align:center">
        <template v-if="state === 'wait'"><h3>در حال بررسی پرداخت شما…</h3><p>لطفاً صفحه را نبندید.</p></template>
        <template v-else-if="state === 'ok'">
          <h3>پرداخت با موفقیت انجام شد 🎉</h3>
          <p>سفارش شما نهایی شد. کد سفارش:</p>
          <span class="ord-code">{{ code }}</span>
          <p v-if="ref_">کد پیگیری بانکی: <b dir="ltr">{{ ref_ }}</b></p>
          <div class="co-actions">
            <RouterLink class="btn btn-brand" :to="{ path: '/track', query: { code } }">پیگیری سفارش</RouterLink>
            <RouterLink class="btn btn-light" to="/">بازگشت به فروشگاه</RouterLink>
          </div>
        </template>
        <template v-else>
          <h3>پرداخت انجام نشد</h3>
          <p>{{ msg }}</p>
          <p v-if="code" style="font-size:.85rem">سفارش <b>{{ code }}</b> ثبت شده و می‌توانید دوباره پرداخت کنید. اگر مبلغی کسر شده، تا ۷۲ ساعت به حساب شما برمی‌گردد.</p>
          <div class="co-actions">
            <button v-if="code" class="btn btn-brand" :disabled="busy" @click="retry">پرداخت دوباره</button>
            <RouterLink class="btn btn-light" to="/">بازگشت به فروشگاه</RouterLink>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { apiCall } from '../services/api';
import { startPayment } from '../stores/orders';

/* زیبال با GET: ?trackId=…&success=…&status=…&orderId=<کد سفارش> برمی‌گردد.
   فقط trackId/orderId خوانده می‌شود؛ نتیجه را verify سرور تعیین می‌کند، نه success مرورگر. */
const q = useRoute().query;
const code = ref(String(q.orderId || q.code || '').toUpperCase());
const state = ref("wait"), msg = ref(""), ref_ = ref(""), busy = ref(false);
onMounted(async () => {
  if (!code.value || !q.trackId) { state.value = 'fail'; msg.value = 'اطلاعات بازگشت از درگاه ناقص است.'; return; }
  const r = await apiCall('/orders/' + encodeURIComponent(code.value) + '/verify', { method: 'POST', body: { trackId: String(q.trackId) } });
  if (r.ok && r.pay_status === 'paid') { ref_.value = r.ref || ''; state.value = 'ok'; return; }
  state.value = 'fail';
  msg.value = String(q.success) === '0' ? 'پرداخت لغو یا ناموفق بود.' : (r.msg || 'پرداخت تأیید نشد.');
});
async function retry() { busy.value = true; const r = await startPayment(code.value); if (!r.ok) { msg.value = r.msg; busy.value = false; } }
</script>
