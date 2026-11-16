<template>
  <div class="drawer-veil" :class="{ open: ui.navOpen }" @click="closeNav()"></div>
  <aside class="drawer" :class="{ open: ui.navOpen }" aria-label="منوی اصلی">
    <div class="drawer-head">
      <span class="logo-mark"><svg class="icon"><use href="#i-nut" /></svg></span>
      <b>خانم گل</b>
      <button aria-label="بستن منو" @click="closeNav()"><svg class="icon"><use href="#i-x" /></svg></button>
    </div>
    <div class="drawer-body">
      <div v-for="c in CATS" :key="c.id" class="acc" :class="{ open: accOpen === c.id }">
        <button type="button" :aria-expanded="accOpen === c.id" @click="accOpen = accOpen === c.id ? null : c.id">
          <svg class="icon"><use :href="'#' + c.icon" /></svg> {{ c.name }} <svg class="icon chev"><use href="#i-chev" /></svg>
        </button>
        <div class="acc-panel">
          <div>
            <RouterLink v-for="s in c.subs" :key="s" :to="{ path: '/products', query: { cat: c.id, q: s } }" @click="closeNav()">{{ s }}</RouterLink>
          </div>
        </div>
      </div>
      <div style="height:10px"></div>
      <div style="display:grid;gap:8px">
        <RouterLink class="btn btn-brand btn-sm" to="/products" style="justify-content:center" @click="closeNav()">مشاهده همه محصولات</RouterLink>
      </div>
    </div>
    <div class="drawer-foot">
      <a :href="telLink"><svg class="icon"><use href="#i-phone" /></svg> {{ shop.info.phone }}</a>
      <!-- پیوندهای منو: از پنل ادمین (تب «منو و دسته‌ها») — پیوند داخلی یا بیرونی با آیکن -->
      <template v-for="(l, i) in menuLinks" :key="i">
        <a v-if="l.link && l.link.startsWith('http')" :href="l.link" target="_blank" rel="noopener">
          <svg class="icon"><use :href="'#' + l.icon" /></svg> {{ l.label }}</a>
        <RouterLink v-else :to="l.link || '/'" @click="closeNav()">
          <svg class="icon"><use :href="'#' + l.icon" /></svg> {{ l.label }}</RouterLink>
      </template>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue';
import { CATS } from '../../data/catalog';
import { ui, closeNav } from '../../stores/ui';
import { shop, telLink } from '../../stores/shop';

const accOpen = ref(null);

/* اگر هنوز پیوندی از سرور نرسیده، پیش‌فرض ثابت نمایش داده می‌شود (حالت دمو/لحظهٔ بارگذاری) */
const FALLBACK_LINKS = [
  { label: 'مشاوره خرید', icon: 'i-headset', link: '/#consult' },
  { label: 'پیگیری سفارش', icon: 'i-doc', link: '/track' },
];
const menuLinks = computed(() => (Array.isArray(shop.menu) && shop.menu.length ? shop.menu : FALLBACK_LINKS));
</script>
