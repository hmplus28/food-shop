<template>
  <div class="section">
    <div class="container" style="max-width:900px">
      <nav class="crumbs" aria-label="مسیر صفحه"><RouterLink to="/">خانه</RouterLink> ‹ <span>سبد خرید</span></nav>
      <div class="sec-head">
        <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-cart" /></svg></span>
          <div><h1 class="sec-title">سبد <i>خرید</i></h1><span class="sec-sub">{{ cartQtyLabel }}</span></div></span>
      </div>
      <div v-if="cart.items.length" class="cart-page">
        <div class="cart-list">
          <div v-for="(c, i) in cart.items" :key="c.pid + '-' + c.w" class="cart-item">
            <div class="ci-media"><img :src="prod(c.pid)?.img" :alt="prod(c.pid)?.name"></div>
            <div class="ci-info">
              <RouterLink class="ci-name" :to="'/product/' + c.pid">{{ prod(c.pid)?.name }}</RouterLink>
              <span class="ci-w">{{ weightLabel(c.w) }}</span>
              <div class="ci-row">
                <div class="ci-qty">
                  <button aria-label="کاهش" @click="lineQty(i, -1)">−</button>
                  <span>{{ toFa(c.qty) }}</span>
                  <button aria-label="افزایش" @click="lineQty(i, 1)">+</button>
                </div>
                <span class="ci-price">{{ money(priceOf(prod(c.pid), c.w) * c.qty) }} <small>تومان</small></span>
                <button class="ci-del" aria-label="حذف" @click="lineQty(i, 0)"><svg class="icon"><use href="#i-trash" /></svg></button>
              </div>
            </div>
          </div>
        </div>
        <aside class="cart-summary">
          <div v-if="auth.user || !apiState.enabled" class="coupon-row">
            <input v-model="couponInput" class="fld" type="text" placeholder="کد تخفیف…" aria-label="کد تخفیف">
            <button class="btn btn-brand btn-sm" @click="applyCoupon(couponInput); couponInput = ''">اعمال</button>
          </div>
          <p v-else class="coupon-login">برای استفاده از کد تخفیف <RouterLink :to="{ path: '/auth', query: { redirect: '/cart' } }"><b>وارد حساب کاربری</b></RouterLink> شوید.</p>
          <div class="totals">
            <div class="t-row"><span>جمع کالاها</span><b>{{ money(cartSub) }} تومان</b></div>
            <div class="t-row"><span>تخفیف کدها</span><b class="off">{{ couponVal.off > 0 ? '−' + money(couponVal.off) + ' تومان' : '۰ تومان' }}</b></div>
            <div class="t-row"><span>هزینه ارسال</span><b v-if="shipCost === 0"><span class="free">رایگان 🎉</span></b><b v-else>{{ money(shipCost) }} تومان</b></div>
            <div class="t-row grand"><span>مبلغ قابل پرداخت</span><b>{{ money(grandTotal) }} تومان</b></div>
          </div>
          <RouterLink class="btn btn-brand btn-lg btn-block" to="/checkout">ادامه و تکمیل خرید</RouterLink>
          <div class="returns-note"><svg class="icon"><use href="#i-shield" /></svg> {{ shop.info.returnsNote }}.</div>
        </aside>
      </div>
      <div v-else class="up-empty">
        <svg class="icon"><use href="#i-cart" /></svg>
        <p>سبد خرید شما خالی است!</p>
        <RouterLink class="btn btn-brand btn-sm" to="/products">مشاهده محصولات</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { toFa, money, weightLabel, priceOf } from '../data/site';
import { prod } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import { shop } from '../stores/shop';
import { auth } from '../stores/auth';
import { apiState } from '../services/api';
import { cart, cartSub, couponVal, shipCost, grandTotal, lineQty, applyCoupon, cartQtyLabel } from '../stores/cart';

useSeo({ title: 'سبد خرید', description: 'سبد خرید فروشگاه خانم گل؛ جمع نهایی سفارش، کد تخفیف و هزینه ارسال', path: '/cart' });
const couponInput = ref('');
</script>

<style scoped>
.cart-page{display:grid;grid-template-columns:1fr 340px;gap:22px;align-items:start}
.coupon-login{font-size:.8rem;color:var(--ink-3);background:var(--bg-warm);border:1px dashed var(--line);border-radius:12px;padding:10px 12px}
.cart-list{display:grid;gap:12px}
.cart-summary{background:#fff;border:1px solid var(--line);border-radius:var(--r-md);padding:16px;box-shadow:var(--sh-sm);display:grid;gap:12px;position:sticky;top:130px}
@media(max-width:800px){.cart-page{grid-template-columns:1fr}.cart-summary{position:static}}
</style>
