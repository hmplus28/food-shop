<template>
  <footer class="footer" aria-label="پاورقی">
    <div class="container">
      <div class="f-top">
        <div class="f-col f-about">
          <div class="f-logo"><span class="logo-mark"><svg class="icon"><use href="#i-nut" /></svg></span><b>خانم گل</b></div>
          <p>خانم گل، فروشگاه اینترنتی خشکبار و محصولات طبیعی؛ بیش از سه دهه است که تازه‌ترین آجیل، خشکبار، زعفران و دمنوش‌ها را مستقیم از باغ‌داران ایرانی تهیه و با بسته‌بندی بهداشتی به سراسر ایران می‌رساند.</p>
          <div class="socials">
            <a href="#" aria-label="اینستاگرام"><svg class="icon"><use href="#i-instagram" /></svg></a>
            <a href="#" aria-label="تلگرام"><svg class="icon"><use href="#i-telegram" /></svg></a>
            <a href="#" aria-label="واتساپ"><svg class="icon"><use href="#i-whatsapp" /></svg></a>
            <a href="tel:02191092000" aria-label="تلفن"><svg class="icon"><use href="#i-phone" /></svg></a>
          </div>
        </div>
        <div class="f-col">
          <h4 class="f-title">دسته‌بندی‌ها</h4>
          <RouterLink v-for="c in footerCats" :key="c.id" :to="{ path: '/products', query: { cat: c.id } }">{{ c.name }}</RouterLink>
        </div>
        <div class="f-col">
          <h4 class="f-title">راهنمای خرید</h4>
          <a href="#" @click.prevent="note('راهنمای خرید به‌زودی تکمیل می‌شود.')">نحوه ثبت سفارش</a>
          <a href="#" @click.prevent="note('شیوه‌های ارسال: پیک فوری، پست پیشتاز و تیپاکس.')">شیوه‌های ارسال و هزینه‌ها</a>
          <a href="#" @click.prevent="note('مرجوعی رایگان تا ۷ روز؛ بدون قید و شرط!')">شرایط مرجوعی کالا</a>
          <a href="#" @click.prevent="note('سوالات متداول به‌زودی تکمیل می‌شود.')">سوالات متداول</a>
          <RouterLink to="/track">پیگیری سفارش</RouterLink>
          <RouterLink to="/#consult">مشاوره خرید</RouterLink>
          <RouterLink to="/account">پنل کاربری</RouterLink>
        </div>
        <div class="f-col">
          <h4 class="f-title">تماس با ما</h4>
          <ul class="f-contact">
            <li><svg class="icon"><use href="#i-pin" /></svg> تهران، خیابان ولی‌عصر، مجتمع تجاری خانم گل، طبقه ۲</li>
            <li><svg class="icon"><use href="#i-phone" /></svg> ۰۲۱-۹۱۰۹۲۰۰۰ (۷ خط)</li>
            <li><svg class="icon"><use href="#i-sms" /></svg> info@asalat-shop.ir</li>
            <li><svg class="icon"><use href="#i-clock" /></svg> شنبه تا پنجشنبه ۹ تا ۲۱</li>
          </ul>
          <div class="f-badges" style="margin-top:14px">
            <span class="f-badge"><svg class="icon"><use href="#i-shield" /></svg> نماد اعتماد الکترونیکی</span>
            <span class="f-badge"><svg class="icon"><use href="#i-check" /></svg> ساماندهی رسانه‌های دیجیتال</span>
            <span class="f-badge"><svg class="icon"><use href="#i-lock" /></svg> درگاه پرداخت امن</span>
          </div>
        </div>
      </div>
      <div class="f-bottom">
        <span>© ۱۴۰۴ فروشگاه خشکبار <b>خانم گل</b> — تمامی حقوق محفوظ است.</span>
        <span>طراحی‌شده با <b>♥</b> برای طعم‌های اصیل ایران</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { CATS } from '../../data/catalog';
import { toast } from '../../stores/ui';

const footerCats = ['ajil', 'pistachio', 'date', 'saffron', 'tea', 'giftbox'].map(id => CATS.find(c => c.id === id));
const note = t => toast(t, 'ok', 4200);
</script>
