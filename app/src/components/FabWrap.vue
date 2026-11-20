<template>
  <div class="fab-wrap">
    <button v-if="shop.lucky.enabled" class="fab gold" aria-label="کارت شانس" @click="openModal('lucky')"><svg class="icon"><use href="#i-gift" /></svg><span v-if="luckyReady" class="dot-pulse">۱</span></button>
    <div class="fab-sup">
      <div v-if="supOpen" class="sup-pop" role="dialog" aria-label="تلفن‌های پشتیبانی">
        <b>پشتیبانی {{ shop.info.shopName.replace(/^فروشگاه\s*/, '') }}</b>
        <a v-if="shop.info.phone" :href="telLink" class="sup-row"><svg class="icon"><use href="#i-phone" /></svg><span dir="ltr">{{ shop.info.phone }}</span></a>
        <a v-if="shop.info.phone2" :href="tel2" class="sup-row"><svg class="icon"><use href="#i-phone" /></svg><span dir="ltr">{{ shop.info.phone2 }}</span></a>
        <a v-if="waLink" :href="waLink" target="_blank" rel="noopener" class="sup-row"><svg class="icon"><use href="#i-whatsapp" /></svg><span>گفتگو در واتس‌اپ</span></a>
        <small v-if="shop.info.hours">{{ shop.info.hours }}</small>
      </div>
      <button class="fab brand" aria-label="ارتباط با مشتری" :aria-expanded="supOpen" @click.stop="supOpen = !supOpen"><svg class="icon"><use href="#i-headset" /></svg></button>
    </div>
    <button v-if="showTop" class="fab" aria-label="بازگشت به بالا" @click="toTop"><svg class="icon" style="transform:rotate(-90deg)"><use href="#i-chev" /></svg></button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { openModal, lucky } from '../stores/ui';
import { shop, telLink, waLink } from '../stores/shop';
import { computed } from 'vue';
const luckyReady = computed(() => lucky.canSpin);

const supOpen = ref(false);
const tel2 = computed(() => 'tel:' + (shop.info.phone2Tel || shop.info.phone2 || '').replace(/[^\d+]/g, ''));
const closeSup = () => { supOpen.value = false; };
const showTop = ref(false);
const onScroll = () => { showTop.value = window.scrollY > 600; };
const toTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });
onMounted(() => { window.addEventListener('scroll', onScroll, { passive: true }); document.addEventListener('click', closeSup); });
onUnmounted(() => { window.removeEventListener('scroll', onScroll); document.removeEventListener('click', closeSup); });
</script>
