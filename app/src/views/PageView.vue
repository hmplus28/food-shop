<template>
  <div class="section">
    <div class="container" style="max-width:820px">
      <nav class="crumbs" aria-label="مسیر صفحه"><RouterLink to="/">خانه</RouterLink> ‹ <span>{{ page ? page.title : 'راهنما' }}</span></nav>
      <div v-if="loading" class="up-empty"><p>در حال بارگذاری…</p></div>
      <div v-else-if="!page" class="up-empty">
        <svg class="icon"><use href="#i-search" /></svg>
        <p>این صفحه پیدا نشد.</p>
        <RouterLink class="btn btn-brand btn-sm" to="/">بازگشت به خانه</RouterLink>
      </div>
      <article v-else class="page-card">
        <h1 class="page-title">{{ page.title }}</h1>

        <!-- متن -->
        <div v-if="html" class="rich" v-html="html"></div>

        <!-- سوالات متداول -->
        <div v-if="page.kind === 'faq'" class="faq">
          <details v-for="(it, i) in page.items" :key="i" class="faq-item">
            <summary>{{ it.q }}</summary>
            <p>{{ it.a }}</p>
          </details>
        </div>

        <!-- جدول زندهٔ هزینه‌های ارسال -->
        <div v-if="page.kind === 'shipping'" class="ship-table">
          <table class="tbl" style="min-width:0">
            <thead><tr><th>روش ارسال</th><th>زمان تحویل</th><th>هزینه</th></tr></thead>
            <tbody>
              <tr v-for="m in shipMethods" :key="m.type"><td><b>{{ m.label }}</b><small style="display:block;color:var(--ink-3)">{{ m.hint }}</small></td><td>{{ m.days }}</td><td>{{ m.cost ? money(m.cost) + ' تومان' : 'رایگان' }}</td></tr>
            </tbody>
          </table>
          <p v-if="freeShipOn" class="ship-free">🎉 سفارش‌های بالای <b>{{ money(freeFrom) }} تومان</b> بدون هزینهٔ ارسال برای شما ارسال می‌شوند.</p>
        </div>

        <!-- تماس -->
        <div v-if="page.kind === 'contact'" class="contact-grid">
          <a v-if="shop.info.phone" :href="telLink" class="c-card"><svg class="icon"><use href="#i-phone" /></svg><b>تلفن</b><span dir="ltr">{{ shop.info.phone }}</span></a>
          <a v-if="waLink" :href="waLink" target="_blank" rel="noopener" class="c-card"><svg class="icon"><use href="#i-whatsapp" /></svg><b>واتس‌اپ</b><span>گفتگوی مستقیم</span></a>
          <div v-if="shop.info.email" class="c-card"><svg class="icon"><use href="#i-sms" /></svg><b>ایمیل</b><span dir="ltr">{{ shop.info.email }}</span></div>
          <div v-if="shop.info.address" class="c-card"><svg class="icon"><use href="#i-pin" /></svg><b>نشانی</b><span>{{ shop.info.address }}</span></div>
          <div v-if="shop.info.hours" class="c-card"><svg class="icon"><use href="#i-clock" /></svg><b>ساعت پاسخگویی</b><span>{{ shop.info.hours }}</span></div>
          <a v-if="shop.info.instagram" :href="shop.info.instagram" target="_blank" rel="noopener" class="c-card"><svg class="icon"><use href="#i-instagram" /></svg><b>اینستاگرام</b><span>صفحهٔ ما</span></a>
          <a v-if="shop.info.telegram" :href="shop.info.telegram" target="_blank" rel="noopener" class="c-card"><svg class="icon"><use href="#i-telegram" /></svg><b>تلگرام</b><span>کانال ما</span></a>
        </div>
        <RouterLink v-if="page.kind === 'contact'" class="btn btn-gold btn-sm" to="/#consult" style="margin-top:14px">درخواست مشاورهٔ تلفنی</RouterLink>
      </article>

      <nav v-if="page" class="page-links" aria-label="سایر راهنماها">
        <RouterLink v-for="p in shop.pages.filter(x => x.slug !== page.slug)" :key="p.slug" :to="'/page/' + p.slug">{{ p.title }}</RouterLink>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { money } from '../data/site';
import { useSeo } from '../composables/useSeo';
import { pageApi } from '../services/api';
import { renderRichText } from '../utils/richtext';
import { shop, shipMethods, freeFrom, freeShipOn, telLink, waLink } from '../stores/shop';

const route = useRoute();
const page = ref(null);
const loading = ref(true);
const html = computed(() => (page.value ? renderRichText(page.value.body) : ''));

async function load(slug) {
  loading.value = true;
  const r = await pageApi(slug);
  page.value = r.ok ? r.page : null;
  loading.value = false;
  if (page.value) {
    const desc = (page.value.body || page.value.title).replace(/[#*\-\d.]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 155);
    useSeo({
      title: page.value.title, description: desc || page.value.title, path: '/page/' + slug,
      jsonld: page.value.kind === 'faq' && page.value.items.length ? {
        '@context': 'https://schema.org', '@type': 'FAQPage',
        mainEntity: page.value.items.map(it => ({ '@type': 'Question', name: it.q, acceptedAnswer: { '@type': 'Answer', text: it.a } })),
      } : undefined,
    });
  } else {
    useSeo({ title: 'صفحه پیدا نشد', description: 'صفحه موردنظر یافت نشد', path: '/404' });
  }
}
watch(() => route.params.slug, s => { if (s) load(String(s)); }, { immediate: true });
</script>

<style scoped>
.page-card{background:#fff;border:1px solid var(--line);border-radius:var(--r-lg);padding:26px;box-shadow:var(--sh-sm)}
.page-title{font-size:clamp(1.3rem,3vw,1.8rem);margin-bottom:14px;color:var(--brand-700)}
.rich :deep(h2){font-size:1.1rem;margin:20px 0 8px;color:var(--ink)}
.rich :deep(h3){font-size:1rem;margin:16px 0 6px}
.rich :deep(p){margin:8px 0;line-height:2;color:var(--ink-2)}
.rich :deep(ul),.rich :deep(ol){margin:8px 0;padding-inline-start:22px;line-height:2;color:var(--ink-2)}
.rich :deep(li){margin:4px 0}
.faq{display:grid;gap:10px;margin-top:14px}
.faq-item{border:1px solid var(--line);border-radius:14px;padding:0 14px;background:var(--bg-warm)}
.faq-item summary{cursor:pointer;font-weight:700;padding:13px 0;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:10px}
.faq-item summary::after{content:"‹";font-size:1.2rem;color:var(--ink-3);transform:rotate(0deg);transition:transform .2s ease}
.faq-item[open] summary::after{transform:rotate(-90deg)}
.faq-item p{margin:0 0 14px;line-height:2;color:var(--ink-2);font-size:.9rem}
.ship-table{margin-top:14px;overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;font-size:.88rem}
.tbl th{background:var(--bg-warm);padding:10px;text-align:start;color:var(--ink-2);font-size:.8rem}
.tbl td{padding:10px;border-top:1px solid var(--line)}
.ship-free{margin-top:12px;background:var(--brand-050);border:1px solid var(--brand-100);border-radius:12px;padding:10px 14px;font-size:.86rem}
.contact-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:14px}
.c-card{display:grid;gap:4px;justify-items:start;background:var(--bg-warm);border:1px solid var(--line);border-radius:14px;padding:14px;color:inherit;text-decoration:none}
.c-card .icon{width:22px;height:22px;color:var(--brand-700)}
.c-card span{font-size:.84rem;color:var(--ink-2)}
a.c-card:hover{border-color:var(--brand)}
.page-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.page-links a{font-size:.8rem;padding:6px 13px;border-radius:999px;background:#fff;border:1px solid var(--line);color:var(--ink-2)}
.page-links a:hover{border-color:var(--brand);color:var(--brand-700)}
</style>
