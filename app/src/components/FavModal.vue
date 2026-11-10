<template>
  <div class="overlay" :class="{ open: ui.modal === 'fav' }" role="dialog" aria-modal="true" aria-label="علاقه‌مندی‌ها" @click.self="closeModal()">
    <div class="modal" style="width:min(560px,100%)">
      <div class="modal-head"><b><svg class="icon"><use href="#i-heart" /></svg> علاقه‌مندی‌های من</b><button class="modal-x" aria-label="بستن" @click="closeModal()"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body">
        <div v-if="!fav.ids.length" class="up-empty">
          <svg class="icon"><use href="#i-heart" /></svg>
          <p>هنوز محصولی به علاقه‌مندی‌ها اضافه نکرده‌اید. روی ❤️ کارت هر محصول بزنید.</p>
        </div>
        <div v-for="p in list" :key="p.id" class="fav-row">
          <img :src="p.img" :alt="p.name" loading="lazy">
          <div><b>{{ p.name }}</b><span>{{ money(priceOf(p, p.weights[1])) }} تومان</span></div>
          <div class="fav-acts">
            <button class="btn btn-brand btn-sm" @click="addToCart(p.id, p.weights[1], 1)">افزودن</button>
            <button class="btn btn-light btn-sm" @click="toggleFav(p.id)">حذف</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { prod } from '../data/catalog';
import { money, priceOf } from '../data/site';
import { ui, closeModal } from '../stores/ui';
import { fav, toggleFav } from '../stores/fav';
import { addToCart } from '../stores/cart';

const list = computed(() => fav.ids.map(id => prod(id)).filter(Boolean));
</script>
