<template>
  <div class="section">
    <div class="container" style="text-align:center;padding:40px 0">
      <div class="nf-code">۴۰۴</div>
      <h1 style="font-size:1.3rem;margin:10px 0">صفحه‌ای که دنبالش بودید پیدا نشد!</h1>
      <p style="color:var(--ink-3);font-size:.9rem;margin-bottom:20px">ممکن است آدرس تغییر کرده باشد؛ از این‌جا ادامه دهید:</p>
      <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
        <RouterLink class="btn btn-brand" to="/">صفحه اصلی</RouterLink>
        <RouterLink class="btn btn-gold" to="/products">مشاهده محصولات</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useSeo } from '../composables/useSeo';
useSeo({ title: 'صفحه پیدا نشد', description: 'صفحه موردنظر در فروشگاه خانم گل یافت نشد', path: '/404' });
</script>

<style scoped>
.nf-code{font-family:var(--f-display);font-size:5rem;color:var(--brand-100);line-height:1}
</style>
