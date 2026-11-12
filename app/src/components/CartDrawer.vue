<template>
  <div class="drawer-veil" :class="{ open: ui.cartOpen }" @click="closeCart()"></div>
  <aside class="cart-drawer" :class="{ open: ui.cartOpen }" aria-label="سبد خرید">
    <div class="cd-head">
      <b><svg class="icon"><use href="#i-cart" /></svg> سبد خرید <span class="cnt">{{ toFa(cartCount) }}</span></b>
      <button aria-label="بستن سبد" @click="closeCart()"><svg class="icon"><use href="#i-x" /></svg></button>
    </div>
    <div v-if="freeShipOn" class="ship-progress">
      <p v-if="shipRemain > 0">تا <b>ارسال رایگان</b> {{ money(shipRemain) }} تومان باقی مانده 🚚</p>
      <p v-else><b>🎉 تبریک!</b> هزینه ارسال شما رایگان شد.</p>
      <div class="sp-bar"><i :style="{ width: Math.min(100, cartSub / freeFrom * 100) + '%' }"></i></div>
    </div>
    <div class="cd-items">
      <div v-if="!cart.items.length" class="cart-empty">
        <svg class="icon"><use href="#i-cart" /></svg>
        <p>سبد خرید شما خالی است!</p>
        <RouterLink class="btn btn-brand btn-sm" to="/products" @click="closeCart()">مشاهده محصولات</RouterLink>
      </div>
      <div v-for="(c, i) in cart.items" :key="c.pid + '-' + c.w" class="cart-item">
        <div class="ci-media"><img :src="prod(c.pid)?.img" :alt="prod(c.pid)?.name"></div>
        <div class="ci-info">
          <div class="ci-name">{{ prod(c.pid)?.name }}</div>
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
    <div class="cd-foot">
      <div v-if="auth.user || !apiState.enabled" class="coupon-row">
        <input v-model="couponInput" class="fld" type="text" placeholder="کد تخفیف…" aria-label="کد تخفیف">
        <button class="btn btn-brand btn-sm" @click="applyCoupon(couponInput); couponInput = ''">اعمال</button>
      </div>
      <p v-else class="coupon-hint">برای استفاده از کد تخفیف <RouterLink to="/auth" @click="closeCart()"><b>وارد حساب کاربری</b></RouterLink> شوید.</p>
      <div class="totals">
        <div class="t-row"><span>جمع کالاها</span><b>{{ money(cartSub) }} تومان</b></div>
        <div class="t-row"><span>تخفیف کدها</span><b class="off">{{ couponVal.off > 0 ? '−' + money(couponVal.off) + ' تومان' : '۰ تومان' }}</b></div>
        <div class="t-row"><span>هزینه ارسال</span><b v-if="cartSub === 0">—</b><b v-else-if="shipCost === 0"><span class="free">رایگان 🎉</span></b><b v-else>{{ money(shipCost) }} تومان</b></div>
        <div class="t-row grand"><span>مبلغ قابل پرداخت</span><b>{{ money(grandTotal) }} تومان</b></div>
      </div>
      <div class="returns-note"><svg class="icon"><use href="#i-shield" /></svg> {{ shop.info.returnsNote }}<template v-if="freeShipOn">؛ هزینه ارسال برای سفارش‌های بالای {{ money(freeFrom) }} تومان رایگان است.</template></div>
      <button class="btn btn-brand btn-lg btn-block" :disabled="cartCount === 0" :style="cartCount === 0 ? 'opacity:.5' : ''"
        @click="closeCart(); router.push('/checkout')">تکمیل خرید و پرداخت</button>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { toFa, money, weightLabel, priceOf } from '../data/site';
import { freeFrom, freeShipOn, shop } from '../stores/shop';
import { auth } from '../stores/auth';
import { apiState } from '../services/api';
import { prod } from '../data/catalog';
import { ui, closeCart } from '../stores/ui';
import { cart, cartCount, cartSub, couponVal, shipRemain, shipCost, grandTotal, lineQty, applyCoupon } from '../stores/cart';

const router = useRouter();
const couponInput = ref('');
</script>
