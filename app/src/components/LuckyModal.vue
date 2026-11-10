<template>
  <div class="overlay" :class="{ open: ui.modal === 'lucky' }" role="dialog" aria-modal="true" aria-label="کارت شانس" @click.self="closeModal()">
    <div class="modal lucky-modal" :class="{ flipped }">
      <div class="lucky-head">
        <div class="gift-ic"><svg class="icon"><use href="#i-gift" /></svg></div>
        <h3>کارت شانس خانم گل</h3>
        <p>هر بار که وارد سایت می‌شوید، یک کارت شانس پشت سر شماست! روی کارت بزنید و جایزه‌تان را ببینید.</p>
      </div>
      <div class="lucky-stage">
        <div class="lc-inner" tabindex="0" role="button" aria-label="باز کردن کارت شانس" @click="flip" @keydown.enter="flip">
          <div class="lc-face lc-front">
            <div class="lc-shine"></div>
            <span class="q">🎁</span>
            <b>روی من کلیک کن!</b>
            <span>جایزه‌ات پشت این کارت مخفی است</span>
          </div>
          <div class="lc-face lc-back">
            <template v-if="prize">
              <span class="lc-prize-ic"><svg class="icon"><use :href="'#' + prize.ic" /></svg></span>
              <h4>{{ prize.t }}</h4>
              <span class="lc-code">{{ prize.c }}</span>
              <p>{{ prize.d }}</p>
            </template>
          </div>
        </div>
      </div>
      <div class="lucky-foot">
        <button v-if="flipped" class="btn btn-gold btn-block" @click="use">عالی بود! ثبت جایزه و ادامه خرید</button>
        <p class="hint">جایزه به‌صورت خودکار در پنل کاربری شما ذخیره می‌شود و هنگام پرداخت قابل استفاده است.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { PRIZES } from '../data/catalog';
import { ui, closeModal, toast } from '../stores/ui';
import { addWonCode } from '../stores/cart';

const flipped = ref(false);
const prize = ref(null);

function pickPrize() {
  const tot = PRIZES.reduce((s, p) => s + p.w, 0);
  let r = Math.random() * tot;
  for (const p of PRIZES) { if ((r -= p.w) <= 0) return p; }
  return PRIZES[1];
}
function flip() {
  if (flipped.value) return;
  flipped.value = true;
  prize.value = pickPrize();
  setTimeout(() => toast('🎉 جایزه شما ثبت شد! کد در پنل کاربری ذخیره شد', 'gold', 4200), 900);
}
function use() {
  if (prize.value) addWonCode(prize.value.c, prize.value.t);
  closeModal();
  toast('جایزه در «پنل کاربری ← کدهای من» ذخیره شد 🎁', 'gold');
}
watch(() => ui.modal, m => { if (m !== 'lucky') { flipped.value = false; prize.value = null; } });
</script>
