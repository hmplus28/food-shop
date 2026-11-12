<template>
  <div class="order-card">
    <div class="oc-head">
      <span class="oc-code">{{ o.code }}</span>
      <span class="oc-date">{{ faDate(o.ts) }}</span>
      <span class="oc-status tag" :class="step === 3 ? 'green' : step === 4 ? 'red' : 'gold'">{{ STATUS[step] }}</span>
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
        <button class="btn btn-gold btn-sm" @click="reorder">سفارش مجدد</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { toFa, money, weightLabel, faDate } from '../data/site';
import { prod } from '../data/catalog';
import { orderStep, STATUS } from '../stores/orders';
import { addToCart } from '../stores/cart';
import { openCart } from '../stores/ui';

const props = defineProps({ o: { type: Object, required: true } });
const step = computed(() => orderStep(props.o));
const itemsLine = computed(() => props.o.items.map(c => `${prod(c.pid)?.name || ''} (${weightLabel(c.w)} × ${toFa(c.qty)})`).join(' + '));
function reorder() { props.o.items.forEach(c => addToCart(c.pid, c.w, c.qty, true)); openCart(); }
</script>
