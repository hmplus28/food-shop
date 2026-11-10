<template>
  <article class="p-card">
    <div class="p-media">
      <img :src="p.img" :alt="p.name" loading="lazy" width="400" height="400">
      <div class="p-tags">
        <span v-for="t in p.tags" :key="t" class="tag" :class="t === 'ممتاز' ? 'gold' : t === 'تخفیف‌دار' ? 'red' : 'green'">{{ t }}</span>
        <span v-if="!p.tags.length" class="tag green">{{ p.grade }}</span>
      </div>
      <button type="button" class="p-fav" :class="{ on: isFav(p.id) }" :aria-label="isFav(p.id) ? 'حذف از علاقه‌مندی‌ها' : 'افزودن به علاقه‌مندی‌ها'" @click="toggleFav(p.id)">
        <svg class="icon"><use href="#i-heart" /></svg>
      </button>
      <span v-if="p.disc" class="p-disc"><span class="pulse-sun">٪{{ toFa(p.disc) }}</span></span>
    </div>
    <div class="p-body">
      <span class="p-cat">{{ catName }}</span>
      <h3 class="p-name"><RouterLink :to="'/product/' + p.id">{{ p.name }}</RouterLink></h3>
      <div class="p-meta">
        <span class="grade tag green">{{ p.grade }}</span>
        <span class="rate"><svg class="icon"><use href="#i-star" /></svg>{{ toFa(p.rate) }}</span>
        <span class="sold">{{ toFa(p.sold) }} فروش</span>
      </div>
      <div class="p-weights" role="radiogroup" aria-label="انتخاب وزن">
        <button v-for="(w, i) in p.weights" :key="w" type="button" class="w-chip" :class="{ on: i === wIdx }" :aria-pressed="i === wIdx" @click="wIdx = i">{{ weightLabel(w) }}</button>
      </div>
      <p style="font-size:.72rem;color:var(--ink-3);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{{ p.desc }}</p>
      <div class="p-pricewrap">
        <div class="p-price">
          <span v-if="p.disc" class="p-old">{{ money(p.price * curW / 1000) }}</span>
          <span class="p-now"><b class="pv">{{ money(priceOf(p, curW)) }}</b><small>تومان</small></span>
        </div>
        <div class="p-actions">
          <div class="qty">
            <button type="button" aria-label="کاهش" @click="qty = Math.max(1, qty - 1)">−</button>
            <span class="qv">{{ toFa(qty) }}</span>
            <button type="button" aria-label="افزایش" @click="qty = Math.min(9, qty + 1)">+</button>
          </div>
        </div>
      </div>
      <button type="button" class="p-add" @click="addToCart(p.id, curW, qty)"><svg class="icon"><use href="#i-cart" /></svg> افزودن به سبد</button>
    </div>
  </article>
</template>

<script setup>
import { ref, computed } from 'vue';
import { toFa, weightLabel, priceOf, money } from '../data/site';
import { catOf } from '../data/catalog';
import { isFav, toggleFav } from '../stores/fav';
import { addToCart } from '../stores/cart';

const props = defineProps({ p: { type: Object, required: true } });
const wIdx = ref(Math.min(1, props.p.weights.length - 1));
const qty = ref(1);
const curW = computed(() => props.p.weights[wIdx.value]);
const catName = computed(() => catOf(props.p.cat)?.name || '');
</script>
