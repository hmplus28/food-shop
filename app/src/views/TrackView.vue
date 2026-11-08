<template>
  <div class="section">
    <div class="container" style="max-width:640px">
      <nav class="crumbs" aria-label="مسیر صفحه"><RouterLink to="/">خانه</RouterLink> ‹ <span>پیگیری سفارش</span></nav>
      <div class="sec-head">
        <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-truck" /></svg></span>
          <div><h1 class="sec-title">پیگیری <i>سفارش</i></h1><span class="sec-sub">با کد سفارش یا شماره موبایل</span></div></span>
      </div>
      <form class="track-row" @submit.prevent="doTrack">
        <input v-model="q" class="fld" type="text" placeholder="کد سفارش مثل AS-1024 یا شماره موبایل" aria-label="کد سفارش یا موبایل">
        <button class="btn btn-brand" type="submit">جستجو</button>
      </form>
      <div v-if="found" style="margin-top:16px">
        <Timeline :order="found" />
      </div>
      <div v-else-if="searched" class="up-empty" style="margin-top:16px">
        <svg class="icon"><use href="#i-search" /></svg>
        <p>سفارشی با این کد/شماره پیدا نشد.</p>
        <button class="btn btn-light btn-sm" @click="demo">مشاهده نمونه پیش‌نمایش پیگیری</button>
      </div>
      <div v-if="demoOrder" style="margin-top:16px"><Timeline :order="demoOrder" /></div>
      <p class="hint" style="font-size:.8rem;color:var(--ink-3);margin-top:14px">نمونه آزمایشی: کد <b>AS-1024</b> را جستجو کنید و دکمه «نمونه پیش‌نمایش» را بزنید.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useSeo } from '../composables/useSeo';
import { findOrder, findByPhone } from '../stores/orders';
import Timeline from '../components/Timeline.vue';

useSeo({ title: 'پیگیری سفارش', description: 'پیگیری لحظه‌ای وضعیت سفارش‌های فروشگاه خانم گل با کد سفارش یا شماره موبایل', path: '/track' });

const route = useRoute();
const q = ref('');
const found = ref(null);
const demoOrder = ref(null);
const searched = ref(false);

function doTrack() {
  searched.value = true;
  demoOrder.value = null;
  const byPhone = findByPhone(q.value);
  found.value = byPhone[0] || findOrder(q.value) || null;
}
function demo() {
  demoOrder.value = { code: 'AS-1024', ts: Date.now() - 9 * 60000, shipType: 'peyk', addr: { phone: '۰۹۱۲۳۴۵۶۷۸۹' }, items: [] };
}
onMounted(() => { if (route.query.code) { q.value = String(route.query.code); doTrack(); } });
</script>
