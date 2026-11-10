<template>
  <div class="section">
    <div class="container" style="max-width:820px">
      <div class="up-frame page-frame">
        <div class="up-head">
          <div class="row1">
            <span class="up-av">{{ (auth.user?.name || 'م').trim()[0] }}</span>
            <div>
              <div class="up-name">{{ auth.user?.name || 'مهمان گرامی' }}</div>
              <div class="up-phone">{{ auth.user?.phone ? toFa(auth.user.phone) : 'برای فعال‌سازی پنل، یک خرید ثبت کنید' }}</div>
            </div>
            <div class="up-tier"><b>{{ tier.i }} {{ tier.n }}</b><span>سطح عضویت</span></div>
          </div>
          <div v-if="!buyer" class="up-welcome">
            <svg class="icon"><use href="#i-gift" /></svg>
            <p>به پنل اختصاصی <b>خانم گل</b> خوش آمدید! اولین خرید بالای ۵۰۰٬۰۰۰ تومان = کد تخفیف ۱۰٪ (WELCOME10)</p>
          </div>
          <div v-else class="up-welcome">
            <svg class="icon"><use href="#i-gift" /></svg>
            <p><b>{{ (auth.user?.name || '').split(' ')[0] }} عزیز، خوش برگشتی!</b> امتیازها و سفارش‌هایت این‌جاست 🌰</p>
          </div>
        </div>
        <div class="up-stats">
          <div class="up-stat"><b>{{ toFa(myOrders.length) }}</b><span>سفارش موفق</span></div>
          <div class="up-stat"><b>{{ toFa(pts) }}</b><span>امتیاز باشگاه</span></div>
          <div class="up-stat"><b>{{ toFa(activeCodes) }}</b><span>کد تخفیف فعال</span></div>
        </div>
        <div class="up-body page-body">
          <!-- خانه -->
          <div v-if="tab === 'home'">
            <template v-if="buyer">
              <div class="up-sec-title"><svg class="icon"><use href="#i-box" /></svg> آخرین سفارش شما</div>
              <OrderCard v-if="myOrders[0]" :o="myOrders[0]" />
              <div class="up-sec-title"><svg class="icon"><use href="#i-sms" /></svg> پیامک‌های خانم گل</div>
              <div v-for="o in myOrders.slice(0, 2)" :key="o.code" class="msg-card">
                <span class="msg-ic"><svg class="icon"><use href="#i-sms" /></svg></span>
                <div><b>تأیید سفارش {{ o.code }}</b><p>مشتری گرامی، سفارش {{ money(o.total) }} تومانی شما ثبت شد. پیگیری: بخش «پیگیری سفارش». — خانم گل</p><time>{{ faDate(o.ts) }}</time></div>
              </div>
            </template>
            <div v-else class="up-empty">
              <svg class="icon"><use href="#i-box" /></svg>
              <p>هنوز سفارشی ثبت نکرده‌اید!<br>اولین خرید شما بالای ۵۰۰٬۰۰۰ تومان، <b>۱۰٪ تخفیف</b> دارد.</p>
              <RouterLink class="btn btn-brand btn-sm" to="/products">شروع خرید با تخفیف اولین خرید</RouterLink>
            </div>
            <div class="up-sec-title"><svg class="icon"><use href="#i-refresh" /></svg> دسترسی سریع</div>
            <div class="up-actions">
              <RouterLink class="up-act" to="/track"><svg class="icon"><use href="#i-truck" /></svg> پیگیری سفارش</RouterLink>
              <a class="up-act" href="tel:02191092000"><svg class="icon"><use href="#i-headset" /></svg> پشتیبانی تلفنی</a>
              <RouterLink class="up-act" to="/#consult"><svg class="icon"><use href="#i-user" /></svg> مشاوره خرید</RouterLink>
              <button class="up-act" @click="openModal('lucky')"><svg class="icon"><use href="#i-gift" /></svg> کارت شانس امروز</button>
            </div>
          </div>

          <!-- سفارش‌ها -->
          <div v-else-if="tab === 'orders'">
            <template v-if="myOrders.length">
              <OrderCard v-for="o in myOrders" :key="o.code" :o="o" />
            </template>
            <div v-else class="up-empty"><svg class="icon"><use href="#i-doc" /></svg><p>لیست سفارش‌ها پس از اولین خرید فعال می‌شود.</p></div>
          </div>

          <!-- علاقه‌مندی‌ها -->
          <div v-else-if="tab === 'favs'">
            <template v-if="favList.length">
              <div v-for="p in favList" :key="p.id" class="fav-row">
                <img :src="p.img" :alt="p.name">
                <div><b>{{ p.name }}</b><span>{{ money(priceOf(p, p.weights[1])) }} تومان</span></div>
                <div class="fav-acts"><button class="btn btn-brand btn-sm" @click="addToCart(p.id, p.weights[1], 1, true)">خرید</button></div>
              </div>
            </template>
            <div v-else class="up-empty"><svg class="icon"><use href="#i-heart" /></svg><p>لیست علاقه‌مندی‌های شما خالی است.</p></div>
          </div>

          <!-- کدهای من -->
          <div v-else-if="tab === 'codes'">
            <div class="code-card">
              <div><span class="cc-c">WELCOME10</span><b>۱۰٪ تخفیف اولین خرید</b><span>حداقل سفارش: ۵۰۰٬۰۰۰ تومان {{ isFirstOrder ? '' : '— استفاده شده' }}</span></div>
            </div>
            <template v-if="wonCodes().length">
              <div v-for="c in wonCodes()" :key="c.code" class="code-card" :class="{ used: c.used }">
                <div><span class="cc-c">{{ c.code }}</span><b>{{ c.label }}</b><span>{{ c.used ? 'استفاده شده' : 'فعال — هنگام پرداخت اعمال کنید' }} | {{ faDate(c.ts) }}</span></div>
                <button v-if="!c.used" class="btn btn-gold btn-sm use" @click="copy(c.code)">کپی/اعمال</button>
              </div>
            </template>
            <div v-else class="up-empty">
              <svg class="icon"><use href="#i-gift" /></svg>
              <p>کارت شانس را باز کنید؛ کدهای تخفیف این‌جا ذخیره می‌شوند.</p>
              <button class="btn btn-gold btn-sm" @click="openModal('lucky')">باز کردن کارت شانس 🎁</button>
            </div>
          </div>

          <!-- حساب -->
          <div v-else>
            <div class="up-sec-title"><svg class="icon"><use href="#i-user" /></svg> اطلاعات من</div>
            <div class="fld w profile-fld"><label>نام و نام خانوادگی</label><input v-model="pf.name" type="text" placeholder="نام شما"></div>
            <div class="fld w profile-fld"><label>شماره موبایل</label><input v-model="pf.phone" type="tel" inputmode="tel" placeholder="۰۹۱۲…"></div>
            <button class="btn btn-brand btn-sm btn-block" @click="saveProfile">ذخیره اطلاعات</button>
            <div class="up-sec-title" style="margin-top:20px"><svg class="icon"><use href="#i-wallet" /></svg> سطح عضویت</div>
            <div class="co-summary" style="font-size:.82rem">
              مجموع خرید شما: <b>{{ money(spentTotal()) }} تومان</b> — سطح فعلی: <b>{{ tier.i }} {{ tier.n }}</b><br>
              <small style="color:var(--ink-3)">🥉 برنزی: شروع | 🥈 نقره‌ای: بالای ۵ میلیون | 🥇 طلایی: بالای ۱۵ میلیون (ارسال همیشه رایگان)</small>
            </div>
            <button class="btn btn-light btn-sm btn-block" style="margin-top:14px;border-color:#f7cdc9;color:var(--red)" @click="exit">خروج از حساب</button>
          </div>
        </div>
        <nav class="up-tabbar" aria-label="تب‌های پنل">
          <button v-for="t in tabs" :key="t.id" class="up-tab" :class="{ on: tab === t.id }" @click="tab = t.id">
            <svg class="icon"><use :href="'#' + t.ic" /></svg> {{ t.label }}
          </button>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { toFa, money, priceOf, faDate, LS } from '../data/site';
import { prod, visibleProducts } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import { auth, updateProfile, logout } from '../stores/auth';
import { fav } from '../stores/fav';
import { addToCart } from '../stores/cart';
import { orders, spentTotal, tierOf, syncMineOrders } from '../stores/orders';
import { openModal, toast } from '../stores/ui';
import OrderCard from '../components/OrderCard.vue';

useSeo({ title: 'پنل کاربری', description: 'پنل کاربری فروشگاه خانم گل؛ سفارش‌ها، علاقه‌مندی‌ها و کدهای تخفیف شما', path: '/account' });

const router = useRouter();
const tab = ref('home');
const tabs = [
  { id: 'home', label: 'خانه', ic: 'i-nut' },
  { id: 'orders', label: 'سفارش‌ها', ic: 'i-box' },
  { id: 'favs', label: 'علاقه‌مندی', ic: 'i-heart' },
  { id: 'codes', label: 'کدهای من', ic: 'i-percent' },
  { id: 'account', label: 'حساب', ic: 'i-user' },
];
const pf = reactive({ name: auth.user?.name || '', phone: auth.user?.phone || '' });

const wonCodes = () => LS.get('codes', []);
const myOrders = computed(() => orders.filter(o => !auth.user?.phone || o.addr.phone === auth.user.phone));

onMounted(() => { if (auth.user) syncMineOrders(); });
const buyer = computed(() => myOrders.value.length > 0);
const tier = computed(() => tierOf(spentTotal()));
const pts = computed(() => Math.floor(spentTotal() / 100000));
const activeCodes = computed(() => wonCodes().filter(c => !c.used).length);
const favList = computed(() => fav.ids.map(id => prod(id)).filter(Boolean));
const isFirstOrder = computed(() => orders.length === 0);

function copy(code) {
  navigator.clipboard?.writeText(code).catch(() => {});
  toast(`کد ${code} کپی شد؛ هنگام پرداخت وارد کنید`, 'gold');
}
function saveProfile() {
  const res = updateProfile(pf.name, pf.phone);
  if (!res.ok) return toast(res.msg, 'err');
  toast('اطلاعات شما ذخیره شد ✅');
}
function exit() {
  logout();
  toast('از حساب خارج شدید', 'ok');
  router.push('/auth');
}
</script>

<style scoped>
.page-frame{position:static;height:auto;max-height:none;display:flex;flex-direction:column;box-shadow:var(--sh-md)}
.page-body{padding:18px;display:grid;gap:12px;overflow:visible}
</style>
