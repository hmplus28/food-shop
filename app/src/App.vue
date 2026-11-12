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
  <SiteStudio />
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
import SiteStudio from './components/SiteStudio.vue';
import { ui, closeAll, openModal, loadLook, refreshLucky, lucky } from './stores/ui';
import { loadShop } from './stores/shop';
import { auth, refreshSession } from './stores/auth';
import { syncCatalog } from './services/api';
import { pruneCart } from './stores/cart';

const route = useRoute();

/* قفل اسکرول بدنه هنگام باز بودن کشو/مودال */
const lock = computed(() => String(ui.cartOpen) + String(ui.navOpen) + String(ui.modal));
watch(lock, v => { document.body.style.overflow = (v !== 'falsefalsenull') ? 'hidden' : ''; });

/* با هر جابه‌جایی مسیر، کشوها و مودال‌ها بسته شوند */
watch(() => route.fullPath, () => closeAll());

/* راه‌اندازی: ظاهر/محتوا/نشست از سرور؛ کارت شانس فقط برای کاربر واردشده‌ای که می‌تواند بچرخاند خودکار باز می‌شود */
onMounted(async () => {
  loadLook();          // تم/رنگ سراسری سایت از سرور
  await refreshSession();    // نقش واقعی کاربر (سوپریوزر) از سرور
  Promise.all([loadShop(), syncCatalog()]).then(pruneCart);   // محتوا + کاتالوگ (شامل پک/اعتماد)؛ سپس پاک‌سازی سبد از کالاهای حذف‌شده
  await refreshLucky();
  setTimeout(() => {
    if (lucky.enabled && lucky.loggedIn && lucky.canSpin && !sessionStorage.getItem('asalat_lucky_seen')) {
      sessionStorage.setItem('asalat_lucky_seen', '1');
      openModal('lucky');
    }
  }, 1400);
});
/* ورود/خروج کاربر → وضعیت کارت شانس تازه شود */
watch(() => auth.user && auth.user.phone, () => refreshLucky());
</script>
