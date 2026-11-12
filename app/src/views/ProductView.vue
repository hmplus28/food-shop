<template>
  <div v-if="p" class="section">
    <div class="container">
      <nav class="crumbs" aria-label="مسیر صفحه">
        <RouterLink to="/">خانه</RouterLink> ‹
        <RouterLink :to="{ path: '/products', query: { cat: p.cat } }">{{ catName }}</RouterLink> ‹
        <b>{{ p.name }}</b>
      </nav>
      <div class="pd-layout">
        <div class="pd-media">
          <img :src="p.img" :alt="p.name" width="600" height="600">
          <span v-if="p.disc" class="p-disc"><span class="pulse-sun">٪{{ toFa(p.disc) }}</span></span>
        </div>
        <div class="pd-info">
          <span class="p-cat">{{ catName }}</span>
          <h1 class="pd-title">{{ p.name }}</h1>
          <div class="p-meta">
            <span class="grade tag green">{{ p.grade }}</span>
            <span class="rate"><svg class="icon"><use href="#i-star" /></svg>{{ toFa(p.rate) }}</span>
            <span class="sold">{{ toFa(p.sold) }} فروش</span>
            <span class="tag" :class="p.stock > 5 ? 'green' : 'red'">{{ p.stock > 0 ? toFa(p.stock) + ' عدد موجود' : 'ناموجود' }}</span>
          </div>
          <p class="pd-desc">{{ p.desc }}</p>
          <div class="p-weights" role="radiogroup" aria-label="انتخاب وزن">
            <button v-for="(w, i) in p.weights" :key="w" type="button" class="w-chip" :class="{ on: i === wIdx }" :aria-pressed="i === wIdx" @click="wIdx = i">{{ weightLabel(w) }}</button>
          </div>
          <div class="pd-pricewrap">
            <div class="p-price">
              <span v-if="p.disc" class="p-old">{{ money(p.price * curW / 1000) }}</span>
              <span class="p-now"><b class="pv">{{ money(priceOf(p, curW)) }}</b><small>تومان</small></span>
            </div>
            <div class="qty">
              <button type="button" aria-label="کاهش" @click="qty = Math.max(1, qty - 1)">−</button>
              <span class="qv">{{ toFa(qty) }}</span>
              <button type="button" aria-label="افزایش" @click="qty = Math.min(9, qty + 1)">+</button>
            </div>
          </div>
          <div class="pd-actions">
            <button class="btn btn-brand btn-lg" :disabled="p.stock === 0" @click="addToCart(p.id, curW, qty)">
              <svg class="icon"><use href="#i-cart" /></svg> افزودن به سبد خرید
            </button>
            <button class="btn btn-light btn-lg" :class="{ 'is-fav': isFav(p.id) }" @click="toggleFav(p.id)">
              <svg class="icon"><use href="#i-heart" /></svg> {{ isFav(p.id) ? 'در علاقه‌مندی‌ها' : 'علاقه‌مندی' }}
            </button>
          </div>
          <ul class="pd-perks">
            <li><svg class="icon"><use href="#i-truck" /></svg> ارسال سریع سراسری؛ رایگان بالای ۱٬۵۰۰٬۰۰۰ تومان</li>
            <li><svg class="icon"><use href="#i-shield" /></svg> مرجوعی رایگان تا ۷ روز بدون قید و شرط</li>
            <li><svg class="icon"><use href="#i-box" /></svg> بسته‌بندی وکیوم بهداشتی با درج تاریخ</li>
          </ul>
        </div>
      </div>

      <section v-if="related.length" class="section" style="padding-bottom:0" aria-label="محصولات مشابه">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-nut" /></svg></span>
            <div><h2 class="sec-title">محصولات <i>مشابه</i></h2><span class="sec-sub">از همان دسته‌بندی {{ catName }}</span></div></span>
        </div>
        <div class="rail">
          <ProductCard v-for="r in related" :key="r.id" :p="r" />
        </div>
      </section>
    </div>
  </div>
  <div v-else class="section"><div class="container"><div class="up-empty"><svg class="icon"><use href="#i-search" /></svg><p>محصول موردنظر پیدا نشد.</p><RouterLink class="btn btn-brand btn-sm" to="/products">مشاهده محصولات</RouterLink></div></div></div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { prod, catOf, visibleProducts } from '../data/catalog';
import { toFa, money, weightLabel, priceOf } from '../data/site';
import { useSeo, SITE_URL } from '../composables/useSeo';
import { productSeo } from '../data/seoProduct';
import { isFav, toggleFav } from '../stores/fav';
import { addToCart } from '../stores/cart';
import ProductCard from '../components/ProductCard.vue';

const route = useRoute();
const p = computed(() => prod(route.params.id));
const wIdx = ref(1);
const qty = ref(1);
watch(() => route.params.id, () => { wIdx.value = 1; qty.value = 1; }, { immediate: true });
const curW = computed(() => p.value ? p.value.weights[Math.min(wIdx.value, p.value.weights.length - 1)] : 0);
const catName = computed(() => p.value ? (catOf(p.value.cat)?.name || '') : '');

const related = computed(() => p.value
  ? visibleProducts().filter(x => x.cat === p.value.cat && x.id !== p.value.id).slice(0, 6)
  : []);

watch(p, pp => { if (pp) useSeo(productSeo(pp, SITE_URL)); }, { immediate: true });
</script>

<style scoped>
.pd-layout{display:grid;grid-template-columns:minmax(300px,460px) 1fr;gap:30px;align-items:start}
.pd-media{position:relative;background:#fff;border:1px solid var(--line);border-radius:var(--r-lg);overflow:hidden;box-shadow:var(--sh-sm)}
.pd-media img{width:100%;aspect-ratio:1;object-fit:cover}
.pd-title{font-size:clamp(1.2rem,2.6vw,1.7rem);margin:6px 0 10px}
.pd-desc{color:var(--ink-2);font-size:.92rem;margin:10px 0 16px}
.pd-pricewrap{display:flex;align-items:center;justify-content:space-between;gap:14px;background:var(--brand-050);border:1px solid var(--brand-100);border-radius:var(--r-md);padding:14px 16px;margin:14px 0}
.pd-actions{display:flex;gap:10px;flex-wrap:wrap}
.is-fav{border-color:var(--gold);color:var(--gold-600)}
.pd-perks{margin-top:16px;display:grid;gap:8px}
.pd-perks li{font-size:.82rem;color:var(--ink-2);display:flex;align-items:center;gap:8px}
.pd-perks .icon{color:var(--brand)}
.crumbs{font-size:.8rem;color:var(--ink-3);margin-bottom:14px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.crumbs b{color:var(--ink)}
@media(max-width:900px){.pd-layout{grid-template-columns:1fr}}
</style>
