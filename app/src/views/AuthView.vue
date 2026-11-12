<template>
  <div class="section">
    <div class="container" style="max-width:460px">
      <div class="auth-card">
        <div class="f-logo" style="justify-content:center;margin-bottom:6px"><span class="logo-mark"><svg class="icon"><use href="#i-nut" /></svg></span><b>خانم گل</b></div>
        <p style="font-size:.82rem;color:var(--ink-3);text-align:center;margin-bottom:16px">برای دسترسی به پنل کاربری، سفارش‌ها و کدهای تخفیف وارد شوید.</p>
        <div class="auth-tabs">
          <button type="button" :class="{ on: tab === 'login' }" @click="tab = 'login'">ورود</button>
          <button type="button" :class="{ on: tab === 'reg' }" @click="tab = 'reg'">ثبت‌نام</button>
        </div>

        <form v-if="tab === 'login'" class="auth-form" @submit.prevent="doLogin">
          <div class="fld w"><label>شماره موبایل</label><input v-model="phone" type="tel" inputmode="tel" autocomplete="username" placeholder="۰۹۱۲۳۴۵۶۷۸۹"></div>
          <div class="fld w"><label>رمز عبور</label><input v-model="pass" type="password" autocomplete="current-password" placeholder="••••••"></div>
          <button class="btn btn-brand btn-block" type="submit" :disabled="busy">{{ busy ? 'در حال ورود…' : 'ورود' }}</button>
        </form>
        <form v-else class="auth-form" @submit.prevent="doReg">
          <div class="fld w"><label>نام و نام خانوادگی</label><input v-model="name" type="text" autocomplete="name" placeholder="مثلاً سارا محمدی"></div>
          <div class="fld w"><label>شماره موبایل</label><input v-model="phone" type="tel" inputmode="tel" autocomplete="username" placeholder="۰۹۱۲۳۴۵۶۷۸۹"></div>
          <div class="fld w"><label>رمز عبور</label><input v-model="pass" type="password" autocomplete="new-password" placeholder="حداقل ۴ کاراکتر"></div>
          <button class="btn btn-gold btn-block" type="submit" :disabled="busy">{{ busy ? 'در حال ثبت…' : 'ساخت حساب کاربری' }}</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useSeo } from '../composables/useSeo';
import { login, register } from '../stores/auth';
import { toast } from '../stores/ui';

useSeo({ title: 'ورود | ثبت‌نام', description: 'ورود یا ثبت‌نام در فروشگاه اینترنتی خانم گل برای دسترسی به پنل کاربری', path: '/auth' });

const router = useRouter();
const route = useRoute();
const tab = ref('login');
const name = ref(''), phone = ref(''), pass = ref('');
const busy = ref(false);

async function done(p) {
  busy.value = true;
  const res = await p;
  busy.value = false;
  if (!res.ok) return toast(res.msg, 'err');
  toast('خوش آمدید! 🌰', 'gold');
  router.push(String(route.query.redirect || '/account'));
}
const doLogin = () => done(login(phone.value, pass.value));
const doReg = () => done(register(name.value, phone.value, pass.value));
</script>

<style scoped>
.auth-card{background:#fff;border:1px solid var(--line);border-radius:var(--r-lg);padding:26px;box-shadow:var(--sh-md)}
.auth-tabs{display:grid;grid-template-columns:1fr 1fr;gap:8px;background:var(--bg-warm);padding:5px;border-radius:14px;margin-bottom:16px}
.auth-tabs button{padding:10px;border-radius:10px;font-weight:700;font-size:.88rem;color:var(--ink-2)}
.auth-tabs button.on{background:#fff;color:var(--brand-700);box-shadow:var(--sh-sm)}
.auth-form{display:grid;gap:12px}
</style>
