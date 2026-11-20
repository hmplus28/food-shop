<template>
  <div class="order-card">
    <div class="oc-head">
      <span class="oc-code">{{ o.code }}</span>
      <span class="oc-date">{{ faDate(o.ts) }}</span>
      <span class="oc-status tag" :class="step === 3 ? 'green' : step === 4 ? 'red' : 'gold'">{{ STATUS[step] }}</span>
      <span v-if="needPay" class="oc-status tag red">{{ o.pay_status === 'failed' ? 'پرداخت ناموفق' : 'در انتظار پرداخت' }}</span>
      <span v-if="o.tracking" class="oc-track" dir="ltr">📦 {{ o.tracking }}</span>
    </div>
    <p class="oc-items-line">{{ itemsLine }}</p>
    <div class="mini-tl">
      <i v-for="i in 4" :key="i" :class="{ on: i - 1 <= step, cur: i - 1 === step && step < 3 }">{{ i - 1 < step ? '✓' : '' }}</i>
    </div>
    <div class="mini-tl-lbl"><b>ثبت</b><span>آماده‌سازی</span><span>ارسال</span><span>تحویل</span></div>
    <div class="oc-foot">
      <span class="oc-total">{{ money(o.total) }} <small>تومان</small></span>
      <div class="oc-actions">
        <RouterLink class="btn btn-light btn-sm" :to="{ path: '/track', query: { code: o.code } }">پیگیری</RouterLink>
        <button v-if="canCancel" class="btn btn-light btn-sm" :disabled="cancelBusy" @click="cancelNow">لغو سفارش</button>
        <button v-if="needPay" class="btn btn-brand btn-sm" :disabled="payBusy" @click="payNow">پرداخت آنلاین</button>
        <button class="btn btn-gold btn-sm" @click="reorder">سفارش مجدد</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { payStartApi, cancelOrderApi } from '../services/api';
import { toFa, money, weightLabel, faDate } from '../data/site';
import { prod } from '../data/catalog';
import { orderStep, STATUS } from '../stores/orders';
import { addToCart } from '../stores/cart';
import { openCart } from '../stores/ui';

const props = defineProps({ o: { type: Object, required: true } });
const step = computed(() => orderStep(props.o));
const itemsLine = computed(() => props.o.items.map(c => `${prod(c.pid)?.name || ''} (${weightLabel(c.w)} × ${toFa(c.qty)})`).join(' + '));
const needPay = computed(() => ['pending', 'failed', 'unpaid'].includes(props.o.pay_status) && step.value !== 4);
const cancelBusy = ref(false);
const canCancel = computed(() => props.o.fromServer && step.value === 0 && props.o.pay_status !== 'paid');
async function cancelNow() {
  if (!window.confirm('سفارش لغو شود؟ این کار قابل بازگشت نیست.')) return;
  cancelBusy.value = true;
  const r = await cancelOrderApi(props.o.code);
  cancelBusy.value = false;
  if (!r.ok) return alert(r.msg || 'لغو سفارش انجام نشد');
  props.o.status = 4;
}
const payBusy = ref(false);
async function payNow() {
  payBusy.value = true;
  const r = await payStartApi(props.o.code);
  if (r.ok && r.payUrl) { window.location.assign(r.payUrl); return; }
  payBusy.value = false; alert(r.msg || 'اتصال به درگاه پرداخت انجام نشد');
}
function reorder() { props.o.items.forEach(c => addToCart(c.pid, c.w, c.qty, true)); openCart(); }
</script>
