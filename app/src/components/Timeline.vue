<template>
  <div v-if="order" class="timeline open">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:12px">
      <b>سفارش {{ order.code }}</b>
      <span class="tag green">{{ STATUS[step] }}</span>
    </div>
    <div v-for="(s, i) in steps" :key="i" class="tl-item" :class="{ on: i <= step, cur: i === step && step < 3 }">
      <span class="tl-dot">
        <svg v-if="i < step" class="icon" style="width:13px;height:13px"><use href="#i-check" /></svg>
        <template v-else>●</template>
      </span>
      <div><b>{{ s.t }}</b><span>{{ s.s }}</span></div>
    </div>
    <div class="sms-note"><svg class="icon"><use href="#i-sms" /></svg><span>📱 پیامک وضعیت این سفارش به شماره {{ toFa(order.addr?.phone || ' شما ') }} ارسال شد.</span></div>
    <button v-if="step === 3" class="btn btn-gold btn-sm btn-block" @click="reorder">سفارش مجدد همین اقلام</button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { toFa, faDate, faTime } from '../data/site';
import { orderStep, STATUS } from '../stores/orders';
import { addToCart } from '../stores/cart';
import { openCart } from '../stores/ui';

const props = defineProps({ order: { type: Object, required: true } });
const step = computed(() => orderStep(props.order));
const steps = computed(() => [
  { t: 'ثبت سفارش', s: faDate(props.order.ts) + ' — ' + faTime(props.order.ts) },
  { t: 'آماده‌سازی و بسته‌بندی', s: 'وزن‌شدن روز، بسته‌بندی وکیوم بهداشتی' },
  { t: props.order.shipType === 'peyk' ? 'تحویل به پیک' : 'تحویل به پست', s: props.order.shipType === 'peyk' ? 'پیک فوری خانم گل در راه است 🛵' : 'کد رهگیری پستی پیامک می‌شود' },
  { t: 'تحویل شد ✅', s: 'امیدواریم لذت برده باشید! مرجوعی رایگان تا ۷ روز' },
]);
function reorder() {
  props.order.items.forEach(c => addToCart(c.pid, c.w, c.qty, true));
  openCart();
}
</script>
