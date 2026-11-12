<template>
  <div class="fab-wrap">
    <button v-if="shop.lucky.enabled" class="fab gold" aria-label="کارت شانس" @click="openModal('lucky')"><svg class="icon"><use href="#i-gift" /></svg><span v-if="luckyReady" class="dot-pulse">۱</span></button>
    <a class="fab brand" :href="telLink" aria-label="ارتباط با مشتری"><svg class="icon"><use href="#i-headset" /></svg></a>
    <button v-if="showTop" class="fab" aria-label="بازگشت به بالا" @click="toTop"><svg class="icon" style="transform:rotate(-90deg)"><use href="#i-chev" /></svg></button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { openModal, lucky } from '../stores/ui';
import { shop, telLink } from '../stores/shop';
import { computed } from 'vue';
const luckyReady = computed(() => lucky.canSpin);

const showTop = ref(false);
const onScroll = () => { showTop.value = window.scrollY > 600; };
const toTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }));
onUnmounted(() => window.removeEventListener('scroll', onScroll));
</script>
