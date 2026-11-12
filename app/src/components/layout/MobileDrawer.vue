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
      <RouterLink to="/#consult"><svg class="icon"><use href="#i-headset" /></svg> مشاوره خرید</RouterLink>
      <RouterLink to="/track"><svg class="icon"><use href="#i-doc" /></svg> پیگیری سفارش</RouterLink>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';
import { CATS } from '../../data/catalog';
import { ui, closeNav } from '../../stores/ui';
import { shop, telLink } from '../../stores/shop';

const accOpen = ref(null);
</script>
