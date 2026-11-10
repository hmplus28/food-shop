<template>
  <div class="section">
    <div class="container">
      <nav class="crumbs" aria-label="مسیر صفحه">
        <RouterLink to="/">خانه</RouterLink> ‹ <span>فروشگاه</span>
        <template v-if="catName"> ‹ <b>{{ catName }}</b></template>
      </nav>
      <div class="sec-head">
        <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-search" /></svg></span>
          <div><h1 class="sec-title"><template v-if="catName">{{ catName }}</template><template v-else>همهٔ <i>محصولات</i></template></h1>
            <span class="sec-sub">{{ toFa(filtered.length) }} محصول {{ q ? `برای «${q}»` : 'آماده ارسال' }}</span></div></span>
      </div>
      <div class="shop-layout">
        <aside class="filters">
          <div class="f-card">
            <h4><svg class="icon"><use href="#i-nut" /></svg> دسته‌بندی</h4>
            <label v-for="c in CATS" :key="c.id" class="f-row">
              <input type="radio" name="cat" :checked="cat === c.id" @change="setFilter({ cat: c.id })">
              <svg class="icon"><use :href="'#' + c.icon" /></svg> {{ c.name }}
            </label>
            <label class="f-row"><input type="radio" name="cat" :checked="!cat" @change="setFilter({ cat: null })"> همه دسته‌ها</label>
          </div>
          <div class="f-card">
            <h4><svg class="icon"><use href="#i-scale" /></svg> بازه قیمت (تومان)</h4>
            <div class="f-price">
              <input v-model="minP" type="number" min="0" placeholder="از" aria-label="حداقل قیمت">
              <input v-model="maxP" type="number" min="0" placeholder="تا" aria-label="حداکثر قیمت">
            </div>
            <button class="btn btn-brand btn-sm btn-block" style="margin-top:8px" @click="applyPrice">اعمال قیمت</button>
          </div>
          <div class="f-card">
            <h4><svg class="icon"><use href="#i-star" /></svg> ترتیب نمایش</h4>
            <select class="fld" :value="sort" aria-label="مرتب‌سازی" @change="setFilter({ sort: $event.target.value || null })">
              <option value="">پرفروش‌ترین</option>
              <option value="cheap">ارزان‌ترین</option>
              <option value="exp">گران‌ترین</option>
              <option value="disc">بیشترین تخفیف</option>
              <option value="rate">بهترین امتیاز</option>
            </select>
          </div>
        </aside>
        <div>
          <div v-if="filtered.length" class="shop-grid">
            <ProductCard v-for="p in filtered" :key="p.id" :p="p" />
          </div>
          <div v-else class="up-empty">
            <svg class="icon"><use href="#i-search" /></svg>
            <p>محصولی با این مشخصات پیدا نشد؛ فیلترها را تغییر دهید.</p>
            <RouterLink class="btn btn-brand btn-sm" to="/products">حذف فیلترها</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { CATS, visibleProducts, catOf } from '../data/catalog';
import { toFa, priceOf, toEn } from '../data/site';
import { useSeo } from '../composables/useSeo';
import ProductCard from '../components/ProductCard.vue';

const route = useRoute();
const router = useRouter();

const cat = computed(() => route.query.cat || null);
const q = computed(() => (route.query.q || '').trim());
const sort = computed(() => route.query.sort || '');
const catName = computed(() => cat.value ? (catOf(cat.value)?.name || null) : null);

useSeo({
  title: catName.value ? `خرید ${catName.value}` : 'فروشگاه محصولات',
  description: catName.value ? `خرید انواع ${catName.value} باکیفیت با قیمت روز و ارسال سریع از فروشگاه خانم گل` : 'لیست کامل محصولات خانم گل؛ آجیل، خشکبار، زعفران و دمنوش با تضمین تازگی و مرجوعی رایگان',
  path: '/products',
});

function setFilter(patch) {
  const query = { ...route.query };
  Object.entries(patch).forEach(([k, v]) => { if (v == null || v === '') delete query[k]; else query[k] = v; });
  router.replace({ query });
}

const minP = ref(route.query.min || '');
const maxP = ref(route.query.max || '');
watch(() => route.query, nq => { minP.value = nq.min || ''; maxP.value = nq.max || ''; });
function applyPrice() {
  setFilter({
    min: minP.value ? toEn(minP.value).replace(/\D/g, '') : null,
    max: maxP.value ? toEn(maxP.value).replace(/\D/g, '') : null,
  });
}

const filtered = computed(() => {
  let list = visibleProducts();
  if (cat.value) list = list.filter(p => p.cat === cat.value);
  if (q.value) {
    const s = q.value;
    list = list.filter(p => (p.name + ' ' + p.desc + ' ' + p.grade).includes(s) || (CATS.find(c => c.id === p.cat)?.name || '').includes(s));
  }
  const min = Number(toEn(String(route.query.min || '')).replace(/\D/g, '')) || 0;
  const max = Number(toEn(String(route.query.max || '')).replace(/\D/g, '')) || 0;
  if (min) list = list.filter(p => priceOf(p, p.weights[1] ?? p.weights[0]) >= min);
  if (max) list = list.filter(p => priceOf(p, p.weights[1] ?? p.weights[0]) <= max);
  switch (sort.value) {
    case 'cheap': list = [...list].sort((a, b) => priceOf(a, a.weights[1] ?? a.weights[0]) - priceOf(b, b.weights[1] ?? b.weights[0])); break;
    case 'exp': list = [...list].sort((a, b) => priceOf(b, b.weights[1] ?? b.weights[0]) - priceOf(a, a.weights[1] ?? a.weights[0])); break;
    case 'disc': list = [...list].sort((a, b) => b.disc - a.disc); break;
    case 'rate': list = [...list].sort((a, b) => b.rate - a.rate); break;
    default: list = [...list].sort((a, b) => b.sold - a.sold);
  }
  return list;
});
</script>

<style scoped>
.shop-layout{display:grid;grid-template-columns:250px 1fr;gap:22px;align-items:start}
.filters{display:grid;gap:12px;position:sticky;top:130px}
.f-card{background:#fff;border:1px solid var(--line);border-radius:var(--r-md);padding:14px;box-shadow:var(--sh-sm)}
.f-card h4{font-size:.9rem;margin-bottom:10px;display:flex;align-items:center;gap:7px;color:var(--brand-700)}
.f-row{display:flex;align-items:center;gap:8px;font-size:.84rem;padding:5px 2px;cursor:pointer}
.f-row input{accent-color:var(--brand)}
.f-price{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.f-price input{border:1.5px solid var(--line-2);border-radius:10px;padding:8px 10px;font-size:.84rem;width:100%}
.shop-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
@media(max-width:991px){.shop-layout{grid-template-columns:1fr}.filters{position:static;grid-template-columns:repeat(3,1fr)}}
@media(max-width:767px){.filters{grid-template-columns:1fr}.shop-grid{grid-template-columns:repeat(2,1fr);gap:12px}}
.crumbs{font-size:.8rem;color:var(--ink-3);margin-bottom:14px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.crumbs b{color:var(--ink)}
</style>
