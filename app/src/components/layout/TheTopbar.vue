<template>
  <div class="topbar">
    <div class="container">
      <div class="tb-comm">
        <svg class="icon"><use href="#i-headset" /></svg>
        <span>ارتباط با مشتری:</span>
        <a class="phone" href="tel:02191092000" dir="ltr">۰۲۱-۹۱۰۹۲۰۰۰</a>
        <span class="tb-tail">— پاسخگویی شبانه‌روزی، همیشه در کنار شما</span>
      </div>
      <nav class="tb-links" aria-label="دسترسی سریع">
        <RouterLink to="/track"><svg class="icon"><use href="#i-doc" /></svg><span class="lbl">پیگیری سفارش</span></RouterLink>
        <i class="tb-sep"></i>
        <RouterLink to="/#consult"><svg class="icon"><use href="#i-headset" /></svg><span class="lbl">مشاوره خرید</span></RouterLink>
        <i class="tb-sep"></i>
        <button type="button" @click="openModal('lucky')"><svg class="icon"><use href="#i-gift" /></svg><span class="lbl">کارت شانس</span></button>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { openModal } from '../../stores/ui';
</script>
