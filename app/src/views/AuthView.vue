<template>
  <div class="section">
    <div class="container" style="max-width:460px">
      <div class="auth-card">
        <div class="f-logo" style="justify-content:center;margin-bottom:6px"><span class="logo-mark"><svg class="icon"><use href="#i-nut" /></svg></span><b>خانم گل</b></div>
        <p style="font-size:.82rem;color:var(--ink-3);text-align:center;margin-bottom:16px">برای دسترسی به پنل کاربری، سفارش‌ها و کدهای تخفیف وارد شوید.</p>
        <div class="auth-tabs">
          <button type="button" :class="{ on: tab === 'sms' }" @click="tab = 'sms'">کد پیامکی</button>
          <button type="button" :class="{ on: tab === 'login' }" @click="tab = 'login'">ورود</button>
          <button type="button" :class="{ on: tab === 'reg' }" @click="tab = 'reg'">ثبت‌نام</button>
        </div>

        <!-- ورود با کد پیامکی (بک‌اند + پنل پیامک) -->
        <form v-if="tab === 'sms'" class="auth-form" @submit.prevent="otpStep === 0 ? doOtpRequest() : doOtpVerify()">
          <template v-if="otpStep === 0">
            <div class="fld w">
              <label>شماره موبایل</label>
              <input v-model="phone" type="tel" inputmode="tel" placeholder="۰۹۱۲۳۴۵۶۷۸۹" :disabled="otpSending">
            </div>
            <button class="btn btn-brand btn-block" type="submit" :disabled="otpSending">
              {{ otpSending ? 'در حال ارسال پیامک… ⏳' : 'دریافت کد ورود پیامکی' }}
            </button>
            <p class="hint" style="font-size:.72rem;color:var(--ink-3);text-align:center;margin:0">اگر حساب نداشته باشید، همان لحظه با همین شماره برایتان ساخته می‌شود.</p>
          </template>
          <template v-else>
            <div class="otp-note"><svg class="icon"><use href="#i-sms" /></svg> کد ۵ رقمی به شماره <b>{{ toFa(toEn(phone).replace(/\D/g,'')) }}</b> پیامک شد.</div>
            <div class="fld w">
              <label>کد پیامک‌شده</label>
              <input ref="otpInput" v-model="otpCode" type="text" inputmode="numeric" maxlength="6" placeholder="- - - - -" dir="ltr" style="text-align:center;letter-spacing:.5em;font-weight:800" :disabled="otpSending">
            </div>
            <div v-if="devCode" class="otp-dev">حالت توسعه (بدون پنل پیامک) — کد شما: <b>{{ toFa(devCode) }}</b></div>
            <button class="btn btn-brand btn-block" type="submit" :disabled="otpSending">
              {{ otpSending ? 'در حال بررسی… ⏳' : 'ورود به پنل' }}
            </button>
            <button class="btn btn-light btn-sm btn-block" type="button" :disabled="otpCooldown > 0" @click="doOtpRequest">
              {{ otpCooldown > 0 ? `ارسال مجدد تا ${toFa(otpCooldown)} ثانیه دیگر` : 'ارسال مجدد کد' }}
            </button>
            <button class="btn btn-light btn-sm btn-block" type="button" @click="backToPhone">تغییر شماره</button>
          </template>
        </form>

        <form v-else-if="tab === 'login'" class="auth-form" @submit.prevent="doLogin">
          <div class="fld w"><label>شماره موبایل</label><input v-model="phone" type="tel" inputmode="tel" placeholder="۰۹۱۲۳۴۵۶۷۸۹"></div>
          <div class="fld w"><label>رمز عبور</label><input v-model="pass" type="password" placeholder="••••••"></div>
          <button class="btn btn-brand btn-block" type="submit">ورود به پنل</button>
        </form>
        <form v-else class="auth-form" @submit.prevent="doReg">
          <div class="fld w"><label>نام و نام خانوادگی</label><input v-model="name" type="text" placeholder="مثلاً سارا محمدی"></div>
          <div class="fld w"><label>شماره موبایل</label><input v-model="phone" type="tel" inputmode="tel" placeholder="۰۹۱۲۳۴۵۶۷۸۹"></div>
          <div class="fld w"><label>رمز عبور</label><input v-model="pass" type="password" placeholder="حداقل ۴ کاراکتر"></div>
          <button class="btn btn-gold btn-block" type="submit">ساخت حساب کاربری</button>
        </form>
        <p class="hint" style="font-size:.74rem;color:var(--ink-3);margin-top:12px;text-align:center">اگر اتصال بک‌اند فعال باشد حساب روی سرور ساخته می‌شود؛ در غیر این صورت اطلاعات فقط در مرورگر خودتان ذخیره می‌شود.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useSeo } from '../composables/useSeo';
import { login, register, otpRequest, otpVerify } from '../stores/auth';
import { toast } from '../stores/ui';
import { toFa, toEn } from '../data/site';

useSeo({ title: 'ورود | ثبت‌نام', description: 'ورود یا ثبت‌نام در فروشگاه اینترنتی خانم گل برای دسترسی به پنل کاربری', path: '/auth' });

const router = useRouter();
const route = useRoute();
const tab = ref('sms');
const name = ref(''), phone = ref(''), pass = ref('');

/* حالت ورود با کد پیامکی */
const otpStep = ref(0);
const otpCode = ref('');
const otpSending = ref(false);
const devCode = ref('');
const otpCooldown = ref(0);
let cooldownTimer = null;
const otpInput = ref(null);

function startCooldown(sec) {
  otpCooldown.value = Math.max(0, Number(sec) || 0);
  clearInterval(cooldownTimer);
  cooldownTimer = setInterval(() => {
    if (otpCooldown.value <= 0) return clearInterval(cooldownTimer);
    otpCooldown.value--;
  }, 1000);
}
onUnmounted(() => clearInterval(cooldownTimer));

const doOtpRequest = async () => {
  otpSending.value = true;
  const r = await otpRequest(phone.value);
  otpSending.value = false;
  if (!r.ok) return toast(r.msg || 'ارسال کد انجام نشد', 'err');
  devCode.value = r.devCode || '';
  otpStep.value = 1;
  startCooldown(r.cooldown || 90);
  toast('کد ورود پیامک شد 📩', 'ok');
  setTimeout(() => otpInput.value && otpInput.value.focus(), 60);
};
const doOtpVerify = async () => {
  otpSending.value = true;
  const r = await otpVerify(phone.value, otpCode.value);
  otpSending.value = false;
  if (!r.ok) return toast(r.msg || 'کد اشتباه است', 'err');
  toast(r.created ? 'حساب شما ساخته شد؛ خوش آمدید! 🌰' : 'خوش آمدید! 🌰', 'gold');
  router.push(String(route.query.redirect || '/account'));
};
function backToPhone() { otpStep.value = 0; otpCode.value = ''; devCode.value = ''; }

function done(res) {
  if (!res.ok) return toast(res.msg, 'err');
  toast('خوش آمدید! 🌰', 'gold');
  router.push(String(route.query.redirect || '/account'));
}
const doLogin = async () => done(await login(phone.value, pass.value));
const doReg = async () => done(await register(name.value, phone.value, pass.value));
</script>

<style scoped>
.auth-card{background:#fff;border:1px solid var(--line);border-radius:var(--r-lg);padding:26px;box-shadow:var(--sh-md)}
.auth-tabs{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;background:var(--bg-warm);padding:5px;border-radius:14px;margin-bottom:16px}
.auth-tabs button{padding:10px;border-radius:10px;font-weight:700;font-size:.88rem;color:var(--ink-2)}
.auth-tabs button.on{background:#fff;color:var(--brand-700);box-shadow:var(--sh-sm)}
.auth-form{display:grid;gap:12px}
.otp-note{display:flex;align-items:center;gap:8px;font-size:.8rem;color:var(--ink-2);background:var(--brand-050);border:1px solid var(--brand-100);border-radius:12px;padding:10px 12px}
.otp-dev{font-size:.74rem;color:var(--gold-600);background:var(--gold-050);border:1px dashed var(--gold-100);border-radius:12px;padding:9px 12px;text-align:center}
</style>
