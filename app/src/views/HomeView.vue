<template>
  <div class="home-flow">
    <!-- ===== Hero ===== -->
    <section v-if="banners.length" class="hero container" aria-label="معرفی فروشگاه">
      <div class="hero-frame" @mouseenter="heroPaused = true" @mouseleave="heroPaused = false">
        <div class="slides" :style="{ transform: 'translateX(' + (slideIdx * 100) + '%)' }">
          <div v-for="(b, i) in banners" :key="b.id + '-' + i" class="slide" :aria-hidden="i !== slideIdx">
            <div v-if="b.image" class="s-media"><img :src="imgSrc(b.image)" :alt="b.title" :fetchpriority="i === 0 ? 'high' : 'low'"></div>
            <div class="s-content">
              <span v-if="b.tag" class="s-tag"><svg class="icon"><use href="#i-leaf" /></svg> {{ b.tag }}</span>
              <component :is="i === 0 ? 'h1' : 'h2'" class="s-title">{{ b.title }} <em v-if="b.titleEm">{{ b.titleEm }}</em></component>
              <p v-if="b.text" class="s-text">{{ b.text }}</p>
              <div class="s-ctas">
                <HeroLink v-if="b.cta1 && b.cta1.label" class="btn btn-gold btn-lg" :to="b.cta1.link">{{ b.cta1.label }}</HeroLink>
                <HeroLink v-if="b.cta2 && b.cta2.label" class="btn btn-ghost btn-lg" :to="b.cta2.link" style="border-color:#fff;color:#fff">{{ b.cta2.label }}</HeroLink>
              </div>
            </div>
          </div>
        </div>
        <div v-if="banners.length > 1" class="hero-dots" role="tablist" aria-label="اسلایدها">
          <button v-for="(b, i) in banners" :key="i" type="button" class="hd" :class="{ on: i === slideIdx }" :aria-label="'اسلاید ' + (i + 1)" @click="slideIdx = i"></button>
        </div>
      </div>
    </section>

    <!-- ===== پک‌های تخفیفی کارت دورانی ===== -->
    <section v-if="on('packs') && packs.length" id="packs" class="section packs-sec" :style="{ order: ord('packs') }" aria-label="پک‌های تخفیفی ویژه">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-percent" /></svg></span>
            <div><h2 class="sec-title">{{ hc.packs.title }} <i v-if="hc.packs.titleEm">{{ hc.packs.titleEm }}</i> {{ hc.packs.titleTail }}</h2><span class="sec-sub">{{ hc.packs.sub }}</span></div></span>
        </div>
        <div class="packs-rail">
          <div v-for="pk in packs" :key="pk.id" class="pack">
            <div class="pack-circle">
              <span v-if="pk.old > pk.now" class="pack-disc pulse-sun md">٪{{ toFa(Math.round((1 - pk.now / pk.old) * 100)) }}</span>
              <div class="ph"><img :src="imgSrc(pk.image) || prod(pk.pid)?.img" :alt="pk.name" loading="lazy"></div>
            </div>
            <h3>{{ pk.name }}</h3>
            <span class="pk-sub">{{ pk.sub }}</span>
            <div class="pk-price"><del v-if="pk.old > pk.now">{{ money(pk.old) }}</del><b>{{ money(pk.now) }}</b><small>تومان</small></div>
            <div class="pack-timer"><svg class="icon"><use href="#i-clock" /></svg><b>{{ packCd[pk.id] || '—' }}</b><span>فرصت باقی‌مانده</span></div>
            <button class="btn btn-brand btn-sm" :disabled="pk.stock <= 0" @click="addToCart(pk.pid, pk.w || 1, 1, true)">{{ pk.stock <= 0 ? 'ناموجود' : 'خرید سریع پک' }}</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== دسته‌بندی‌های محبوب ===== -->
    <section v-if="on('cats')" id="cats" class="section" :style="{ order: ord('cats') }" aria-label="دسته‌بندی‌های محبوب">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-nut" /></svg></span>
            <div><h2 class="sec-title">{{ hc.cats.title }} <i v-if="hc.cats.titleEm">{{ hc.cats.titleEm }}</i> {{ hc.cats.titleTail }}</h2><span class="sec-sub">{{ hc.cats.sub }}</span></div></span>
          <div class="sec-actions"><RouterLink class="link-more" to="/products">همه محصولات <svg class="icon"><use href="#i-chev" /></svg></RouterLink></div>
        </div>
        <div class="cats-grid">
          <RouterLink v-for="c in catPicks" :key="c.id" class="cat-card" :to="{ path: '/products', query: { cat: c.id } }">
            <img :src="c.feat.img" :alt="c.name" loading="lazy">
            <div class="cat-info"><b>{{ c.name }}</b><span>{{ toFa(c.subs.length) }} زیرشاخه</span>
              <span class="go"><svg class="icon"><use href="#i-chev" /></svg></span></div>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- ===== پیشنهاد شگفت‌انگیز ===== -->
    <section v-if="on('amazing') && amzList.length" id="amazing" class="section" :style="{ order: ord('amazing') }" aria-label="پیشنهاد شگفت‌انگیز">
      <div class="container">
        <div class="amazing">
          <div class="amz-wrap">
            <div class="amz-side">
              <div v-if="hc.amazing.badge" class="amz-badge"><span class="pulse-sun" style="font-size:1.02rem">{{ hc.amazing.badge }}</span></div>
              <h3>{{ hc.amazing.title }}</h3>
              <p>{{ hc.amazing.text }}</p>
              <div v-if="hc.amazing.countdown" class="cd-row">
                <div class="cd-box"><b>{{ amzCd.h }}</b><span>ساعت</span></div>
                <div class="cd-box"><b>{{ amzCd.m }}</b><span>دقیقه</span></div>
                <div class="cd-box"><b>{{ amzCd.s }}</b><span>ثانیه</span></div>
              </div>
              <RouterLink class="btn btn-gold btn-sm" to="/products">مشاهده همه</RouterLink>
            </div>
            <div class="amz-rail">
              <ProductCard v-for="p in amzList" :key="p.id" :p="p" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== پرفروش‌ترین‌ها ===== -->
    <section v-if="on('best') && bestList.length" id="best" class="section" :style="{ order: ord('best') }" aria-label="پرفروش‌ترین محصولات">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-fire" /></svg></span>
            <div><h2 class="sec-title">{{ hc.best.title }} <i v-if="hc.best.titleEm">{{ hc.best.titleEm }}</i> {{ hc.best.titleTail }}</h2><span class="sec-sub">{{ hc.best.sub }}</span></div></span>
          <div class="sec-actions">
            <button class="rail-arrow" aria-label="قبلی" @click="railGo(bestRail, -1)"><svg class="icon"><use href="#i-chev" /></svg></button>
            <button class="rail-arrow" aria-label="بعدی" @click="railGo(bestRail, 1)"><svg class="icon" style="transform:rotate(180deg)"><use href="#i-chev" /></svg></button>
          </div>
        </div>
        <div ref="bestRail" class="rail">
          <ProductCard v-for="p in bestList" :key="p.id" :p="p" />
        </div>
      </div>
    </section>

    <!-- ===== خرید اطمینان ===== -->
    <section v-if="on('trust') && trustItem" id="etemad" class="section trust-sec" :style="{ order: ord('trust') }" aria-label="خرید اطمینان">
      <div class="container">
        <div class="sec-head trust-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-shield" /></svg></span>
            <div><h2 class="sec-title">{{ hc.trust.title }} <i v-if="hc.trust.titleEm">{{ hc.trust.titleEm }}</i> {{ hc.trust.titleTail }}</h2><span class="sec-sub">{{ hc.trust.sub }}</span></div></span>
          <div class="t-count"><svg class="icon"><use href="#i-clock" /></svg><span>تا پایان پیشنهاد امروز</span><b>{{ trustCd }}</b></div>
        </div>
        <div class="trust-wrap">
          <article class="trust-card">
            <div class="t-media">
              <img :src="imgSrc(trustItem.image)" :alt="trustItem.name" loading="lazy">
              <span class="t-daychip">{{ trustLabel }}</span>
              <span v-if="trustOff" class="t-off tag red">٪{{ toFa(trustOff) }} تخفیف</span>
            </div>
            <div class="t-body">
              <span class="t-kicker"><svg class="icon"><use href="#i-shield" /></svg> {{ hc.trust.kicker }}</span>
              <h3 class="t-title">{{ trustItem.name }}</h3>
              <p v-if="hc.trust.why" class="t-why"><b>چرا این‌جا؟</b> {{ hc.trust.why }}</p>
              <div class="t-price"><del v-if="trustItem.old > trustItem.price">{{ money(trustItem.old) }}</del><b>{{ money(trustItem.price) }}</b><small>تومان</small><span v-if="trustItem.old > trustItem.price" class="t-save">سود شما: {{ money(trustItem.old - trustItem.price) }} تومان</span></div>
              <div class="t-stock">{{ trustItem.stock > 0 ? (trustItem.stock <= 10 ? 'موجودی امروز محدود است (' + toFa(trustItem.stock) + ' عدد)' : 'موجود') : 'ناموجود' }}<div class="bar"><i :style="{ width: Math.min(100, trustItem.stock * 10) + '%' }"></i></div></div>
              <div class="t-days">
                <span class="lbl">پیشنهاد هر روز هفته:</span>
                <button v-for="d in trustDays" :key="d" type="button" class="t-daypill" :class="{ on: d === selDay }" @click="selDay = d">{{ DAY_NAMES[d] }}</button>
              </div>
              <div class="t-actions">
                <button class="btn btn-gold" :disabled="trustItem.stock <= 0" @click="trustAdd"><svg class="icon"><use href="#i-cart" /></svg> افزودن به سبد</button>
                <RouterLink class="btn btn-ghostd" to="/track">سفارش‌های قبلی‌تان را پیگیری کنید</RouterLink>
              </div>
            </div>
          </article>
          <aside class="trust-side">
            <div class="ts-card">
              <h4><span class="pulse-sun sm">✓</span> زیر یک سقف با شما</h4>
              <div class="ts-item"><span class="ti"><svg class="icon"><use href="#i-shield" /></svg></span><div><b>کیفیت‌سنجی تیم خانم گل</b><span>هر کالا پیش از عرضه توسط تیم ما بررسی و تأیید می‌شود.</span></div></div>
              <div class="ts-item"><span class="ti"><svg class="icon"><use href="#i-percent" /></svg></span><div><b>تضمین بازگشت ۷ روزه</b><span>راضی نبودید؟ بدون سؤال و با کد تخفیف هدیه پس بگیرید.</span></div></div>
              <div class="ts-item"><span class="ti"><svg class="icon"><use href="#i-truck" /></svg></span><div><b>ارسال سریع و ضربه‌گیر</b><span>بسته‌بندی چندلایه و رهگیری لحظه‌ای مرسوله.</span></div></div>
              <div class="ts-item"><span class="ti"><svg class="icon"><use href="#i-wallet" /></svg></span><div><b>پرداخت مطمئن</b><span>درگاه بانکی معتبر یا پرداخت در محل، به انتخاب شما.</span></div></div>
            </div>
          </aside>
        </div>
      </div>
    </section>

    <!-- ===== مشاوره خرید + پیگیری سفارش ===== -->
    <section v-if="on('consult')" id="consult" class="section" :style="{ order: ord('consult') }" aria-label="مشاوره خرید و پیگیری سفارش">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-headset" /></svg></span>
            <div><h2 class="sec-title"><i v-if="hc.consult.title">{{ hc.consult.title }}</i> {{ hc.consult.titleTail }}</h2><span class="sec-sub">{{ hc.consult.sub }}</span></div></span>
        </div>
        <div class="cons-grid">
          <div class="cons-card hl">
            <div class="cons-top">
              <span class="ci"><svg class="icon"><use href="#i-phone" /></svg></span>
              <div><b>تماس فوری با کارشناس</b><span>{{ shop.info.hours }}</span></div>
            </div>
            <p class="cons-text">{{ shop.info.consultText }}</p>
            <div class="cons-actions">
              <a class="btn btn-brand btn-sm" :href="telLink"><svg class="icon"><use href="#i-phone" /></svg> {{ shop.info.phone }}</a>
              <a v-if="waLink" class="btn btn-light btn-sm" :href="waLink" target="_blank" rel="noopener"><svg class="icon"><use href="#i-whatsapp" /></svg> واتساپ</a>
            </div>
          </div>
          <div class="cons-card">
            <div class="cons-top">
              <span class="ci"><svg class="icon"><use href="#i-doc" /></svg></span>
              <div><b>درخواست مشاوره تلفنی</b><span>کارشناس ما در اولین فرصت با شما تماس می‌گیرد</span></div>
            </div>
            <form class="cons-form" @submit.prevent="consult">
              <div class="fld w"><input v-model="cons.name" type="text" placeholder="نام و نام خانوادگی" required></div>
              <div class="fld w"><input v-model="cons.phone" type="tel" inputmode="tel" placeholder="شماره موبایل (۰۹…)" required></div>
              <div class="fld w">
                <select v-model="cons.topic" aria-label="موضوع مشاوره">
                  <option value="">موضوع مشاوره…</option>
                  <option>انتخاب آجیل برای مهمانی</option>
                  <option>پک هدیه سازمانی و شرکتی</option>
                  <option>مشاوره رژیم سلامت</option>
                  <option>خرید عمده و همکاری</option>
                </select>
              </div>
              <button class="btn btn-gold btn-sm" type="submit" :disabled="consBusy"><svg class="icon"><use href="#i-sms" /></svg> {{ consBusy ? 'در حال ثبت…' : 'ثبت درخواست مشاوره' }}</button>
            </form>
          </div>
          <div class="cons-card track">
            <div class="cons-top">
              <span class="ci"><svg class="icon"><use href="#i-truck" /></svg></span>
              <div><b>پیگیری سفارش</b><span>با کد سفارشی که پیامک شده</span></div>
            </div>
            <p class="cons-text">بعد از ثبت خرید، کد پیگیری برایتان پیامک می‌شود؛ همین‌جا وضعیت لحظه‌ای سفارش را ببینید.</p>
            <form class="track-row" @submit.prevent="trackInline">
              <input v-model="trackQ" class="fld" type="text" placeholder="کد سفارش مثل KG-12345" aria-label="کد سفارش">
              <button class="btn btn-brand btn-sm" type="submit">پیگیری</button>
            </form>
            <Timeline v-if="inlineOrder" :order="inlineOrder" />
            <p v-else-if="inlineMsg" style="font-size:.82rem;color:var(--ink-3)">{{ inlineMsg }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== چرا خانم گل ===== -->
    <section v-if="on('why') && hc.why.items.length" id="why" class="section" :style="{ paddingTop: 0, order: ord('why') }" aria-label="مزایای فروشگاه">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-shield" /></svg></span>
            <div><h2 class="sec-title">{{ hc.why.title }} <i v-if="hc.why.titleEm">{{ hc.why.titleEm }}</i>{{ hc.why.titleTail }}</h2><span class="sec-sub">{{ hc.why.sub }}</span></div></span>
        </div>
        <div class="why-grid">
          <div v-for="(w, i) in hc.why.items" :key="i" class="why-card"><span class="wi"><svg class="icon"><use :href="'#' + w.icon" /></svg></span><b>{{ w.title }}</b><p>{{ w.text }}</p></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { useSeo } from '../composables/useSeo';
import { IMG, CATS, prod, visibleProducts } from '../data/catalog';
import { toFa, money, fmtHMS, DAY_NAMES, WEEK_ORDER, LS } from '../data/site';
import { addToCart } from '../stores/cart';
import { toast } from '../stores/ui';
import { trackOrder } from '../stores/orders';
import { consultApi } from '../services/api';
import { shop, telLink, waLink } from '../stores/shop';
import { imgSrc } from '../services/api';
import HeroLink from '../components/HeroLink.vue';
import ProductCard from '../components/ProductCard.vue';
import Timeline from '../components/Timeline.vue';

useSeo({
  title: null,
  description: 'خرید آنلاین بهترین آجیل، پسته، بادام، گردو، خرما و زعفران با تضمین تازگی، ارسال سریع سراسری و مرجوعی رایگان از فروشگاه خانم گل',
  path: '/',
});

const catPicks = ['ajil', 'pistachio', 'date', 'dryfruit', 'saffron', 'tea', 'giftbox', 'mulberryfig']
  .map(id => CATS.find(c => c.id === id)).filter(Boolean);

/* ---------- شمارش معکوس‌ها ---------- */
const now = ref(Date.now());
let timer = null;
onMounted(() => { timer = setInterval(() => { now.value = Date.now(); }, 1000); });
onUnmounted(() => clearInterval(timer));

/* پک‌ها: پایان شمارش معکوس از سرور می‌آید (برای همهٔ بازدیدکنندگان یکسان است) */
const packs = computed(() => shop.packs.filter(p => p.endsAt > now.value - 1000 || p.endsAt === null));
const packCd = computed(() => {
  const o = {};
  shop.packs.forEach(pk => { o[pk.id] = fmtHMS(Math.max(0, pk.endsAt - now.value)); });
  return o;
});

/* تنظیم بخش‌ها (عنوان، روشن/خاموش، ترتیب) از پنل مدیر */
const hc = computed(() => shop.home);
const on = key => shop.home[key] && shop.home[key].on !== false;
const ord = key => shop.home.order.indexOf(key) + 1;

/* بنر اصلی: اسلایدر خودکار */
const banners = computed(() => shop.banners);
const slideIdx = ref(0);
const heroPaused = ref(false);
let heroTimer = null;
onMounted(() => { heroTimer = setInterval(() => { if (!heroPaused.value && banners.value.length > 1) slideIdx.value = (slideIdx.value + 1) % banners.value.length; }, 6500); });
onUnmounted(() => clearInterval(heroTimer));

/* شگفت‌انگیز: تا نیمه‌شب */
const amzCd = computed(() => {
  const end = new Date(now.value); end.setHours(24, 0, 0, 0);
  const s = Math.max(0, Math.floor((end - now.value) / 1000));
  return {
    h: toFa(String(Math.floor(s / 3600)).padStart(2, '0')),
    m: toFa(String(Math.floor(s % 3600 / 60)).padStart(2, '0')),
    s: toFa(String(s % 60).padStart(2, '0')),
  };
});

/* خرید اطمینان: تا نیمه‌شب */
const trustCd = computed(() => {
  const end = new Date(now.value); end.setHours(24, 0, 0, 0);
  return fmtHMS(end - now.value);
});

/* ---------- لیست‌ها ---------- */
const bestList = computed(() => visibleProducts().filter(p => p.sec.includes('best')).sort((a, b) => b.sold - a.sold).slice(0, shop.home.best.limit || 8));
const amzList = computed(() => visibleProducts().filter(p => p.sec.includes('amz')).sort((a, b) => b.disc - a.disc).slice(0, shop.home.amazing.limit || 6));

/* ریل افقی سازگار با RTL */
const bestRail = ref(null);
const RTL_NEG = (() => {
  try {
    const d = document.createElement('div');
    d.style.cssText = 'position:absolute;top:-9999px;inset-inline-start:-9999px;direction:rtl;width:100px;overflow:scroll';
    d.innerHTML = '<div style="display:inline-block;width:300px;height:1px"></div>';
    document.body.appendChild(d);
    d.scrollLeft = -50;
    const neg = d.scrollLeft === -50;
    d.remove();
    return neg;
  } catch (e) { return true; }
})();
function railGo(rail, dir) {
  if (!rail) return;
  const max = rail.scrollWidth - rail.clientWidth;
  if (max <= 4) return;
  const step = Math.max(240, rail.clientWidth * .8) * dir;
  rail.scrollBy({ left: RTL_NEG ? -step : step, behavior: 'smooth' });
}

/* ---------- خرید اطمینان (کالاهای هر روز هفته از پنل مدیر) ---------- */
const selDay = ref(new Date().getDay());
const trustDays = computed(() => WEEK_ORDER.filter(d => shop.trust.some(t => t.day === d)));
const trustItem = computed(() => shop.trust.find(t => t.day === selDay.value) || shop.trust.find(t => t.day === trustDays.value[0]) || null);
const trustOff = computed(() => (trustItem.value && trustItem.value.old > trustItem.value.price ? Math.round((1 - trustItem.value.price / trustItem.value.old) * 100) : 0));
const trustLabel = computed(() => selDay.value === new Date().getDay() ? ('پیشنهاد امروز — ' + DAY_NAMES[selDay.value]) : ('پیش‌نمایش ' + DAY_NAMES[selDay.value]));
function trustAdd() {
  if (!trustItem.value) return;
  addToCart(trustItem.value.pid, 1, 1, true);
  toast(`«${trustItem.value.name}» به سبد اضافه شد؛ نماد اعتماد خانم گل در راه است 🛡️`, 'gold');
}

/* ---------- فرم مشاوره + پیگیری داخل صفحه ---------- */
const cons = reactive({ name: '', phone: '', topic: '' });
const consBusy = ref(false);
async function consult() {
  const ph = cons.phone.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/\D/g, '');
  if (!/^09\d{9}$/.test(ph)) return toast('شماره موبایل معتبر وارد کنید', 'err');
  consBusy.value = true;
  const r = await consultApi({ name: cons.name, phone: ph, topic: cons.topic });
  consBusy.value = false;
  if (!r.ok) return toast(r.msg || 'ثبت درخواست انجام نشد؛ دوباره تلاش کنید', 'err');
  toast('درخواست مشاوره ثبت شد؛ کارشناس خانم گل با شما تماس می‌گیرد 📞', 'ok', 5200);
  cons.name = ''; cons.phone = ''; cons.topic = '';
}
const trackQ = ref('');
const inlineOrder = ref(null);
const inlineMsg = ref('');
async function trackInline() {
  inlineOrder.value = null; inlineMsg.value = '';
  if (!trackQ.value.trim()) return toast('کد سفارش را وارد کنید', 'err');
  const o = await trackOrder(trackQ.value);
  if (o) inlineOrder.value = o; else inlineMsg.value = 'سفارشی با این کد پیدا نشد؛ از صفحه «پیگیری سفارش» دوباره امتحان کنید.';
}
</script>
