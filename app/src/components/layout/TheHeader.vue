<template>
  <header class="site-header">
    <div class="container">
      <div class="hd-inner">
        <button class="burger" aria-label="باز کردن منو" @click="openNav()"><svg class="icon"><use href="#i-menu" /></svg></button>
        <RouterLink class="logo" to="/" aria-label="فروشگاه خانم گل">
          <span class="logo-mark"><svg class="icon"><use href="#i-nut" /></svg></span>
          <span class="logo-text"><b>خانم گل</b><small>خشکبار و محصولات طبیعی</small></span>
        </RouterLink>
        <div class="search-wrap">
          <div class="search-box">
            <svg class="icon"><use href="#i-search" /></svg>
            <input v-model="q" class="search-input" type="search" placeholder="جستجو در بیش از ۳۰ محصول؛ مثلاً پسته اکبری…"
              aria-label="جستجوی محصولات" @keydown.enter.prevent="goSearch" @input="searchDD = true">
            <button class="search-btn" @click="goSearch">جستجو</button>
          </div>
          <div class="search-dd" :class="{ open: searchDD && q.trim() }" role="listbox">
            <template v-if="results.length">
              <button v-for="p in results" :key="p.id" class="sr-item" @click="quickAdd(p)">
                <img :src="p.img" alt="">
                <div><div class="n">{{ p.name }}</div><div class="p">{{ money(priceOf(p, p.weights[1] ?? p.weights[0])) }} تومان</div></div>
              </button>
            </template>
            <div v-else class="sr-empty">محصولی برای «{{ q }}» پیدا نشد</div>
          </div>
        </div>
        <div class="hd-actions">
          <button class="icon-btn" aria-label="علاقه‌مندی‌ها" @click="openModal('fav')">
            <svg class="icon"><use href="#i-heart" /></svg>
            <span class="dot-pulse fav-count" :class="{ hidden: favCount === 0 }">{{ toFa(favCount) }}</span>
          </button>
          <RouterLink class="login-btn" :to="auth.user ? '/account' : '/auth'">
            <svg class="icon"><use href="#i-user" /></svg> {{ auth.user ? 'پنل کاربری' : 'ورود | ثبت‌نام' }}
          </RouterLink>
          <button class="icon-btn cart-btn" aria-label="سبد خرید" @click="openCart()">
            <svg class="icon"><use href="#i-cart" /></svg>
            <span class="dot-pulse cart-count" :class="{ hidden: cartCount === 0 }">{{ toFa(cartCount) }}</span>
          </button>
        </div>
      </div>
      <div class="m-search">
        <div class="search-box">
          <svg class="icon"><use href="#i-search" /></svg>
          <input v-model="qM" class="search-input" type="search" placeholder="جستجوی محصول…" aria-label="جستجوی محصولات"
            @keydown.enter.prevent="goSearchM" @input="searchDDM = true">
          <button class="search-btn" aria-label="جستجو" @click="goSearchM"><svg class="icon"><use href="#i-search" /></svg></button>
        </div>
        <div class="search-dd" :class="{ open: searchDDM && qM.trim() }" role="listbox">
          <template v-if="resultsM.length">
            <button v-for="p in resultsM" :key="p.id" class="sr-item" @click="quickAdd(p)">
              <img :src="p.img" alt="">
              <div><div class="n">{{ p.name }}</div><div class="p">{{ money(priceOf(p, p.weights[1] ?? p.weights[0])) }} تومان</div></div>
            </button>
          </template>
          <div v-else class="sr-empty">محصولی برای «{{ qM }}» پیدا نشد</div>
        </div>
      </div>
    </div>
    <!-- منوی دسته‌بندی دسکتاپ -->
    <nav class="main-nav" aria-label="دسته‌بندی محصولات">
      <div class="container">
        <ul class="nav-list">
          <li v-for="c in CATS" :key="c.id" class="nav-item" :class="{ hot: c.hot }">
            <RouterLink :to="{ path: '/products', query: { cat: c.id } }"><svg class="icon"><use :href="'#' + c.icon" /></svg> {{ c.name }}</RouterLink>
            <div class="mega" role="menu">
              <div class="container mega-inner">
                <div class="mega-cats">
                  <h5>زیرشاخه‌های {{ c.name }}</h5>
                  <RouterLink v-for="s in c.subs" :key="s" :to="{ path: '/products', query: { cat: c.id, q: s } }">{{ s }}</RouterLink>
                </div>
                <div class="mega-cols">
                  <div class="mega-links">
                    <h5>محبوب‌ها</h5>
                    <RouterLink v-for="p in popular(c.id)" :key="p.id" :to="'/product/' + p.id">{{ p.name }}</RouterLink>
                  </div>
                  <div class="mega-links">
                    <h5>پیشنهاد خانم گل</h5>
                    <RouterLink to="/#packs">پک‌های تخفیفی امروز</RouterLink>
                    <RouterLink to="/#etemad">خرید اطمینان روز</RouterLink>
                    <RouterLink to="/#amazing">شگفت‌انگیزها</RouterLink>
                  </div>
                </div>
                <RouterLink class="mega-feat" :to="{ path: '/products', query: { cat: c.id } }">
                  <img :src="c.feat.img" :alt="c.feat.t" loading="lazy">
                  <b>{{ c.feat.t }}</b><span>{{ c.feat.s }}</span>
                </RouterLink>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { CATS, visibleProducts } from '../../data/catalog';
import { priceOf, money, toFa } from '../../data/site';
import { ui, openNav, openCart, openModal, toast } from '../../stores/ui';
import { cartCount } from '../../stores/cart';
import { favCount } from '../../stores/fav';
import { auth } from '../../stores/auth';
import { addToCart } from '../../stores/cart';

const router = useRouter();
const q = ref(''), qM = ref('');
const searchDD = ref(false), searchDDM = ref(false);

const searchProducts = s => {
  s = s.trim();
  if (!s) return [];
  return visibleProducts().filter(p => (p.name + ' ' + p.desc + ' ' + p.grade + ' ' + (CATS.find(c => c.id === p.cat)?.name || '')).includes(s)).slice(0, 6);
};
const results = computed(() => searchProducts(q.value));
const resultsM = computed(() => searchProducts(qM.value));
const popular = cat => visibleProducts().filter(p => p.cat === cat).slice(0, 4);

function goSearch() { searchDD.value = false; router.push({ path: '/products', query: q.value.trim() ? { q: q.value.trim() } : {} }); q.value = ''; }
function goSearchM() { searchDDM.value = false; router.push({ path: '/products', query: qM.value.trim() ? { q: qM.value.trim() } : {} }); qM.value = ''; }
function quickAdd(p) { addToCart(p.id, p.weights[1] ?? p.weights[0], 1, true); searchDD.value = false; searchDDM.value = false; toast(`«${p.name}» به سبد اضافه شد 🛒`, 'ok'); }

document.addEventListener('click', e => {
  if (!e.target.closest('.search-wrap') && !e.target.closest('.m-search')) { searchDD.value = false; searchDDM.value = false; }
});
</script>
