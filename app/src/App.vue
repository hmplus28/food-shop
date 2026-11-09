<template>
  <IconSprite />
  <TheTopbar />
  <TheHeader />
  <MobileDrawer />
  <main id="main">
    <router-view />
  </main>
  <TheFooter />
  <CartDrawer />
  <LuckyModal />
  <FavModal />
  <Toasts />
  <FabWrap />
  <MobileCartBar />
  <BrandTuner />
</template>

<script setup>
import { watch, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import IconSprite from './components/IconSprite.vue';
import TheTopbar from './components/layout/TheTopbar.vue';
import TheHeader from './components/layout/TheHeader.vue';
import MobileDrawer from './components/layout/MobileDrawer.vue';
import TheFooter from './components/layout/TheFooter.vue';
import CartDrawer from './components/CartDrawer.vue';
import LuckyModal from './components/LuckyModal.vue';
import FavModal from './components/FavModal.vue';
import Toasts from './components/Toasts.vue';
import FabWrap from './components/FabWrap.vue';
import MobileCartBar from './components/MobileCartBar.vue';
import BrandTuner from './components/BrandTuner.vue';
import { ui, closeAll, openModal } from './stores/ui';
import { syncCatalog } from './services/api';

const route = useRoute();

/* قفل اسکرول بدنه هنگام باز بودن کشو/مودال */
const lock = computed(() => String(ui.cartOpen) + String(ui.navOpen) + String(ui.modal));
watch(lock, v => { document.body.style.overflow = (v !== 'falsefalsenull') ? 'hidden' : ''; });

/* با هر جابه‌جایی مسیر، کشوها و مودال‌ها بسته شوند */
watch(() => route.fullPath, () => closeAll());

/* کارت شانس: هر بار ورود به سایت (هر سشن جدید) + همگام‌سازی بی‌صدای محصولات با بک‌اند */
onMounted(() => {
  syncCatalog();   // اگر بک‌اند فعال/در دسترس نباشد، بی‌صدا به دادهٔ محلی برمی‌گردد
  setTimeout(() => {
    if (!sessionStorage.getItem('asalat_lucky_seen')) {
      sessionStorage.setItem('asalat_lucky_seen', '1');
      openModal('lucky');
    }
  }, 1600);
});
</script>
