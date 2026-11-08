<template>
  <div class="m-cart-bar" :class="{ show: visible }">
    <span class="ci"><svg class="icon"><use href="#i-cart" /></svg><span class="dot-pulse cart-count">{{ toFa(cartCount) }}</span></span>
    <div><b>{{ money(cartSub) }} تومان</b><span>{{ cartQtyLabel }}</span></div>
    <RouterLink class="btn btn-brand btn-sm" to="/cart">مشاهده سبد</RouterLink>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { toFa, money } from '../data/site';
import { cartCount, cartSub, cartQtyLabel } from '../stores/cart';
import { ui } from '../stores/ui';

const route = useRoute();
const visible = computed(() =>
  cartCount.value > 0 && !ui.cartOpen && !['cart', 'checkout'].includes(route.name));
</script>
