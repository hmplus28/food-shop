<template>
  <div class="fab-wrap">
    <button class="fab gold" aria-label="کارت شانس" @click="openModal('lucky')"><svg class="icon"><use href="#i-gift" /></svg><span class="dot-pulse">۱</span></button>
    <a class="fab brand" href="tel:02191092000" aria-label="ارتباط با مشتری"><svg class="icon"><use href="#i-headset" /></svg></a>
    <button v-if="showTop" class="fab" aria-label="بازگشت به بالا" @click="toTop"><svg class="icon" style="transform:rotate(-90deg)"><use href="#i-chev" /></svg></button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { openModal } from '../stores/ui';

const showTop = ref(false);
const onScroll = () => { showTop.value = window.scrollY > 600; };
const toTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }));
onUnmounted(() => window.removeEventListener('scroll', onScroll));
</script>
