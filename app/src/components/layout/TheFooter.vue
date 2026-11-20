<template>
  <footer class="footer" aria-label="پاورقی">
    <div class="container">
      <div class="f-top">
        <div class="f-col f-about">
          <div class="f-logo"><span class="logo-mark"><svg class="icon"><use href="#i-nut" /></svg></span><b>{{ shop.info.shopName.replace(/^فروشگاه\s*/, '') }}</b></div>
          <p>{{ shop.info.footerAbout }}</p>
          <div class="socials">
            <a v-if="shop.info.instagram" :href="shop.info.instagram" target="_blank" rel="noopener" aria-label="اینستاگرام"><svg class="icon"><use href="#i-instagram" /></svg></a>
            <a v-if="shop.info.telegram" :href="shop.info.telegram" target="_blank" rel="noopener" aria-label="تلگرام"><svg class="icon"><use href="#i-telegram" /></svg></a>
            <a v-if="waLink" :href="waLink" target="_blank" rel="noopener" aria-label="واتساپ"><svg class="icon"><use href="#i-whatsapp" /></svg></a>
            <a :href="telLink" aria-label="تلفن"><svg class="icon"><use href="#i-phone" /></svg></a>
          </div>
        </div>
        <div class="f-col">
          <h4 class="f-title">دسته‌بندی‌ها</h4>
          <RouterLink v-for="c in footerCats" :key="c.id" :to="{ path: '/products', query: { cat: c.id } }">{{ c.name }}</RouterLink>
        </div>
        <div class="f-col">
          <h4 class="f-title">راهنمای خرید</h4>
          <RouterLink v-for="p in guidePages" :key="p.slug" :to="'/page/' + p.slug">{{ p.title }}</RouterLink>
          <RouterLink to="/track">پیگیری سفارش</RouterLink>
          <RouterLink to="/#consult">مشاوره خرید</RouterLink>
          <RouterLink to="/account">پنل کاربری</RouterLink>
          <RouterLink v-for="p in aboutPages.filter(x => x.slug !== 'about')" :key="p.slug" :to="'/page/' + p.slug">{{ p.title }}</RouterLink>
        </div>
        <div class="f-col">
          <h4 class="f-title">تماس با ما</h4>
          <ul class="f-contact">
            <li v-if="shop.info.address"><svg class="icon"><use href="#i-pin" /></svg> {{ shop.info.address }}</li>
            <li v-if="shop.info.phone"><svg class="icon"><use href="#i-phone" /></svg> <a :href="telLink">{{ shop.info.phone }}</a></li>
            <li v-if="shop.info.email"><svg class="icon"><use href="#i-sms" /></svg> {{ shop.info.email }}</li>
            <li v-if="shop.info.hours"><svg class="icon"><use href="#i-clock" /></svg> {{ shop.info.hours }}</li>
          </ul>
          <div class="f-badges" style="margin-top:14px">
            <!-- نماد اعتماد الکترونیکی رسمی (اینماد) — فقط تصویر رسمی با لینک تأیید، بدون متن اضافه -->
            <a class="f-badge f-badge-enamad"
               href="https://trustseal.enamad.ir/?id=8722783&Code=zZZLttcxPXlYxzPxyW5NCeA9dTSBSOMh"
               target="_blank" rel="noopener" referrerpolicy="origin"
               aria-label="نماد اعتماد الکترونیکی — اینماد">
              <img referrerpolicy="origin"
                   src="https://trustseal.enamad.ir/logo.aspx?id=8722783&Code=zZZLttcxPXlYxzPxyW5NCeA9dTSBSOMh"
                   alt="نماد اعتماد الکترونیکی (اینماد)" loading="lazy" @error="enamadFail">
            </a>
          </div>
        </div>
      </div>
      <div class="f-bottom">
        <span>© {{ jy }} فروشگاه خشکبار <b>خانم گل</b> — تمامی حقوق محفوظ است.</span>
        <a class="f-dayna" href="https://daynacode.ir" target="_blank" rel="noopener" aria-label="توسعه توسط تیم دایناکد — daynacode.ir">
          <span>توسعه توسط تیم <b>دایناکد</b></span>
          <img :src="DAYNA_LOGO" alt="دایناکد" width="84" height="28" loading="lazy">
        </a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue';
import { CATS, IMG } from '../../data/catalog';
import { jYear } from '../../data/jalali';
import { shop, telLink, waLink, guidePages, aboutPages } from '../../stores/shop';

/* سال شمسی جاری (۱۴۰۵ و بعد از آن خودکار) */
const jy = jYear();
const DAYNA_LOGO = IMG + 'dayna-logo.png';   // کپی محلی؛ در نبودش main.js به daynacode.ir برمی‌گردد
import { toast } from '../../stores/ui';

/* دسته‌های فوتر: از دادهٔ مدیریتی (پنل ادمین) — ۶ دستهٔ فعال اول؛ واکنش‌گرا به تغییرهای منو */
const footerCats = computed(() => CATS.filter(c => c && c.id && c.name).slice(0, 6));
const note = t => toast(t, 'ok', 4200);

/* اگر تصویر رسمی اینماد لود نشد (خطای شبکه)، کارت به شکل نشان متنی سالم بماند */
const enamadFail = e => { e.target.style.display = 'none'; };
</script>
