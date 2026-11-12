<template>
  <div class="overlay" :class="{ open: ui.modal === 'lucky' }" role="dialog" aria-modal="true" aria-label="کارت شانس" @click.self="closeModal()">
    <div class="modal lucky-modal" :class="{ flipped }">
      <button type="button" class="lucky-x modal-x" aria-label="بستن کارت شانس" @click="closeModal()"><svg class="icon"><use href="#i-x" /></svg></button>
      <div class="lucky-head">
        <div class="gift-ic"><svg class="icon"><use href="#i-gift" /></svg></div>
        <h3>کارت شانس {{ shop.info.shopName.replace(/^فروشگاه\s*/, '') }}</h3>
        <p v-if="!lucky.enabled">کارت شانس فعلاً غیرفعال است.</p>
        <p v-else-if="!auth.user">کارت شانس روی حساب کاربری شما ثبت می‌شود؛ برای باز کردن آن وارد شوید یا ثبت‌نام کنید.</p>
        <p v-else-if="lucky.canSpin">روی کارت بزنید و جایزه‌تان را ببینید؛ جایزه یک کد شخصی و یک‌بارمصرف است که روی حساب شما می‌ماند.</p>
        <p v-else>شما اخیراً کارت شانس را باز کرده‌اید. نوبت بعدی: <b>{{ nextText }}</b></p>
      </div>
      <div class="lucky-stage">
        <div class="lc-inner" :class="{ locked: !canFlip }" tabindex="0" role="button" :aria-disabled="!canFlip" aria-label="باز کردن کارت شانس" @click="flip" @keydown.enter="flip">
          <div class="lc-face lc-front">
            <div class="lc-shine"></div>
            <span class="q">{{ busy ? '⏳' : canFlip ? '🎁' : '🔒' }}</span>
            <b>{{ busy ? 'در حال باز کردن…' : canFlip ? 'روی من کلیک کن!' : 'کارت شانس قفل است' }}</b>
            <span>{{ canFlip ? 'جایزه‌ات پشت این کارت مخفی است' : (auth.user ? 'تا نوبت بعدی صبر کنید' : 'برای باز کردن وارد حساب شوید') }}</span>
          </div>
          <div class="lc-face lc-back">
            <template v-if="prize">
              <span class="lc-prize-ic"><svg class="icon"><use :href="'#' + prize.icon" /></svg></span>
              <h4>{{ prize.title }}</h4>
              <span class="lc-code" dir="ltr">{{ code }}</span>
              <p>{{ prize.desc }}</p>
            </template>
          </div>
        </div>
      </div>
      <div class="lucky-foot">
        <template v-if="flipped">
          <button class="btn btn-gold btn-block" @click="copyCode">{{ copied ? 'کپی شد ✅' : 'کپی کد جایزه' }}</button>
          <button class="btn btn-light btn-block" style="margin-top:8px" @click="closeModal()">ادامه خرید</button>
        </template>
        <button v-else-if="!auth.user && lucky.enabled" class="btn btn-gold btn-block" @click="goLogin">ورود / ثبت‌نام</button>
        <RouterLink v-else-if="auth.user && !lucky.canSpin && lucky.enabled" class="btn btn-light btn-block" to="/account?tab=codes" @click="closeModal()">دیدن کدهای من</RouterLink>
        <p class="hint">جایزه به‌صورت کد شخصی در «پنل کاربری ← کدهای من» ذخیره می‌شود و هنگام ثبت سفارش (پس از ورود) قابل استفاده است.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ui, closeModal, toast, lucky, refreshLucky } from '../stores/ui';
import { auth } from '../stores/auth';
import { shop } from '../stores/shop';
import { luckySpinApi } from '../services/api';
import { jDateTime } from '../data/jalali';

const router = useRouter();
const route = useRoute();
const flipped = ref(false);
const busy = ref(false);
const prize = ref(null);
const code = ref('');
const copied = ref(false);

const canFlip = computed(() => lucky.enabled && !!auth.user && lucky.canSpin && !flipped.value && !busy.value);
const nextText = computed(() => (lucky.nextAt ? jDateTime(lucky.nextAt) : 'به‌زودی'));

async function flip() {
  if (!canFlip.value) {
    if (!auth.user && lucky.enabled) toast('برای باز کردن کارت شانس ابتدا وارد حساب کاربری شوید', 'err');
    else if (auth.user && !lucky.canSpin) toast('نوبت بعدی کارت شانس شما: ' + nextText.value, 'err');
    return;
  }
  busy.value = true;
  const r = await luckySpinApi();
  busy.value = false;
  if (!r.ok) {
    toast(r.msg || 'باز کردن کارت شانس انجام نشد', 'err');
    refreshLucky();
    return;
  }
  prize.value = r.prize; code.value = r.code;
  lucky.canSpin = false; lucky.nextAt = r.nextAt || null;
  flipped.value = true;
  setTimeout(() => toast('🎉 جایزه شما روی حسابتان ثبت شد؛ کد در «کدهای من» است', 'gold', 4200), 900);
}
function copyCode() {
  const done = () => { copied.value = true; setTimeout(() => { copied.value = false; }, 2000); };
  if (navigator.clipboard) navigator.clipboard.writeText(code.value).then(done, done); else done();
}
function goLogin() { closeModal(); router.push({ path: '/auth', query: { redirect: route.fullPath } }); }
watch(() => ui.modal, m => { if (m === 'lucky') refreshLucky(); else { flipped.value = false; prize.value = null; code.value = ''; } });
</script>

