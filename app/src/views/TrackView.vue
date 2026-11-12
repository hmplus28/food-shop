<template>
  <div class="section">
    <div class="container" style="max-width:640px">
      <nav class="crumbs" aria-label="مسیر صفحه"><RouterLink to="/">خانه</RouterLink> ‹ <span>پیگیری سفارش</span></nav>
      <div class="sec-head">
        <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-truck" /></svg></span>
          <div><h1 class="sec-title">پیگیری <i>سفارش</i></h1><span class="sec-sub">با کد سفارشی که پیامک شده</span></div></span>
      </div>
      <form class="track-row" @submit.prevent="doTrack">
        <input v-model="q" class="fld" type="text" placeholder="کد سفارش مثل KG-12345" aria-label="کد سفارش">
        <button class="btn btn-brand" type="submit">جستجو</button>
      </form>
      <div v-if="found" style="margin-top:16px">
        <Timeline :order="found" />
      </div>
      <div v-else-if="searched" class="up-empty" style="margin-top:16px">
        <svg class="icon"><use href="#i-search" /></svg>
        <p>سفارشی با این کد پیدا نشد. کد را دوباره بررسی کنید یا در «پنل کاربری» سفارش‌هایتان را ببینید.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useSeo } from '../composables/useSeo';
import { trackOrder } from '../stores/orders';
import Timeline from '../components/Timeline.vue';

useSeo({ title: 'پیگیری سفارش', description: 'پیگیری لحظه‌ای وضعیت سفارش‌های فروشگاه خانم گل با کد سفارش یا شماره موبایل', path: '/track' });

const route = useRoute();
const q = ref('');
const found = ref(null);
const searched = ref(false);

async function doTrack() {
  searched.value = true;
  found.value = await trackOrder(q.value);
}
onMounted(() => { if (route.query.code) { q.value = String(route.query.code); doTrack(); } });
</script>
