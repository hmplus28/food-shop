<template>
  <div class="topbar">
    <div class="container">
      <div class="tb-comm">
        <svg class="icon"><use href="#i-headset" /></svg>
        <span>ارتباط با مشتری:</span>
        <a class="phone" :href="telLink" dir="ltr">{{ shop.info.phone }}</a>
        <span v-if="shop.info.topbarMsg" class="tb-tail">— {{ shop.info.topbarMsg }}</span>
      </div>
      <nav class="tb-links" aria-label="دسترسی سریع">
        <RouterLink to="/track"><svg class="icon"><use href="#i-doc" /></svg><span class="lbl">پیگیری سفارش</span></RouterLink>
        <i class="tb-sep"></i>
        <RouterLink to="/#consult"><svg class="icon"><use href="#i-headset" /></svg><span class="lbl">مشاوره خرید</span></RouterLink>
        <template v-if="shop.lucky.enabled">
          <i class="tb-sep"></i>
          <button type="button" @click="openModal('lucky')"><svg class="icon"><use href="#i-gift" /></svg><span class="lbl">کارت شانس</span></button>
        </template>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { openModal } from '../../stores/ui';
import { shop, telLink } from '../../stores/shop';
</script>
