<template>
  <div v-if="order" class="timeline open">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:12px">
      <b>سفارش {{ order.code }}</b>
      <span class="tag" :class="cancelled ? 'red' : 'green'">{{ STATUS[step] }}</span>
    </div>
    <div v-if="order.tracking" class="tl-track">📦 کد رهگیری مرسوله: <b dir="ltr">{{ order.tracking }}</b></div>
    <template v-if="cancelled">
      <div class="tl-cancel">این سفارش لغو شده است. اگر نیاز به راهنمایی دارید با پشتیبانی تماس بگیرید.</div>
    </template>
    <template v-else>
      <div v-for="(s, i) in steps" :key="i" class="tl-item" :class="{ on: i <= step, cur: i === step && step < 3 }">
        <span class="tl-dot">
          <svg v-if="i < step" class="icon" style="width:13px;height:13px"><use href="#i-check" /></svg>
          <template v-else>●</template>
        </span>
        <div><b>{{ s.t }}</b><span>{{ s.s }}</span></div>
      </div>
    </template>
    <div v-if="history.length" class="tl-hist">
      <b>تاریخچهٔ وضعیت</b>
      <div v-for="(e, i) in history" :key="i" class="tl-h"><span>{{ faDateTime(e.ts) }}</span> — {{ e.label }}<template v-if="e.note">: {{ e.note }}</template></div>
    </div>
    <div v-if="order.addr?.phone" class="sms-note"><svg class="icon"><use href="#i-sms" /></svg><span>📱 پیامک وضعیت این سفارش به شماره {{ toFa(order.addr.phone) }} ارسال می‌شود.</span></div>
    <button v-if="step === 3" class="btn btn-gold btn-sm btn-block" @click="reorder">سفارش مجدد همین اقلام</button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { toFa, faDate, faTime, faDateTime } from '../data/site';
import { orderStep, STATUS } from '../stores/orders';
import { addToCart } from '../stores/cart';
import { openCart } from '../stores/ui';

const props = defineProps({ order: { type: Object, required: true } });
const step = computed(() => orderStep(props.order));
const cancelled = computed(() => step.value === 4);
const history = computed(() => (props.order.events || []).filter(e => e.note || e.status > 0));
const steps = computed(() => [
  { t: 'ثبت سفارش', s: faDate(props.order.ts) + ' — ' + faTime(props.order.ts) },
  { t: 'آماده‌سازی و بسته‌بندی', s: 'وزن‌شدن روز، بسته‌بندی وکیوم بهداشتی' },
  { t: props.order.shipType === 'peyk' ? 'تحویل به پیک' : 'تحویل به پست', s: props.order.shipType === 'peyk' ? 'پیک فوری خانم گل در راه است 🛵' : 'کد رهگیری پستی پیامک می‌شود' },
  { t: 'تحویل شد ✅', s: 'امیدواریم لذت برده باشید! از مرجوعی رایگان‌مان در صورت نیاز استفاده کنید' },
]);
function reorder() {
  props.order.items.forEach(c => addToCart(c.pid, c.w, c.qty, true));
  openCart();
}
</script>

<style scoped>
.tl-track{background:var(--brand-050);border:1px solid var(--brand-100);border-radius:12px;padding:9px 12px;font-size:.84rem;margin-bottom:10px}
.tl-cancel{background:#fdeceb;border:1px solid #f7cdc9;color:var(--red);border-radius:12px;padding:10px 12px;font-size:.84rem;margin-bottom:10px}
.tl-hist{margin-top:12px;border-top:1px dashed var(--line);padding-top:10px;font-size:.78rem;color:var(--ink-2);display:grid;gap:4px}
.tl-h span{color:var(--ink-3)}
</style>
