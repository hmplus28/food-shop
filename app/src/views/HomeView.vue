<template>
  <div>
    <!-- ===== Hero ===== -->
    <section class="hero container" aria-label="معرفی فروشگاه">
      <div class="hero-frame">
        <div class="slides">
          <div class="slide">
            <div class="s-media"><img :src="IMG + '62b15d793f24.png'" alt="کاسه آجیل و خشکبار متنوع" fetchpriority="high"></div>
            <div class="s-content">
              <span class="s-tag"><svg class="icon"><use href="#i-leaf" /></svg> تازه، سالم و باکیفیت</span>
              <h1 class="s-title">طعم اصالت، کیفیت در <em>هر دانه</em></h1>
              <p class="s-text">انتخابی تازه و باکیفیت از بهترین آجیل‌ها، خشکبار و محصولات طبیعی؛ از دل طبیعت تا سفره شما.</p>
              <div class="s-ctas">
                <RouterLink class="btn btn-gold btn-lg" to="/products"><svg class="icon"><use href="#i-cart" /></svg> مشاهده محصولات</RouterLink>
                <RouterLink class="btn btn-ghost btn-lg" to="/#amazing" style="border-color:#fff;color:#fff">مشاهده پیشنهادهای ویژه</RouterLink>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== پک‌های تخفیفی کارت دورانی ===== -->
    <section id="packs" class="section packs-sec" aria-label="پک‌های تخفیفی ویژه">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-percent" /></svg></span>
            <div><h2 class="sec-title">پک‌های <i>تخفیفی</i> ویژه امروز</h2><span class="sec-sub">فرصت محدود؛ فقط ۲۴ تا ۴۸ ساعت پس از شمارش معکوس باقی است!</span></div></span>
        </div>
        <div class="packs-rail">
          <div v-for="pk in PACKS" :key="pk.pid" class="pack">
            <div class="pack-circle">
              <span class="pack-disc pulse-sun md">٪{{ toFa(Math.round((1 - pk.now / pk.old) * 100)) }}</span>
              <div class="ph"><img :src="prod(pk.pid)?.img" :alt="pk.name" loading="lazy"></div>
            </div>
            <h3>{{ pk.name }}</h3>
            <span class="pk-sub">{{ pk.sub }}</span>
            <div class="pk-price"><del>{{ money(pk.old) }}</del><b>{{ money(pk.now) }}</b><small>تومان</small></div>
            <div class="pack-timer"><svg class="icon"><use href="#i-clock" /></svg><b>{{ packCd[pk.pid] || '—' }}</b><span>فرصت باقی‌مانده</span></div>
            <button class="btn btn-brand btn-sm" @click="addToCart(pk.pid, pk.w, 1, true)">خرید سریع پک</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== دسته‌بندی‌های محبوب ===== -->
    <section id="cats" class="section" aria-label="دسته‌بندی‌های محبوب">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-nut" /></svg></span>
            <div><h2 class="sec-title">دسته‌بندی‌های <i>محبوب</i></h2><span class="sec-sub">از میان طعم‌های اصیل ایرانی انتخاب کنید</span></div></span>
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
    <section id="amazing" class="section" aria-label="پیشنهاد شگفت‌انگیز">
      <div class="container">
        <div class="amazing">
          <div class="amz-wrap">
            <div class="amz-side">
              <div class="amz-badge"><span class="pulse-sun" style="font-size:1.02rem">تا ٪۳۰</span></div>
              <h3>پیشنهاد شگفت‌انگیز</h3>
              <p>تخفیف‌های باورنکردنی روی محصولات منتخب؛ فرصت باقی‌مانده:</p>
              <div class="cd-row">
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
    <section id="best" class="section" aria-label="پرفروش‌ترین محصولات">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-fire" /></svg></span>
            <div><h2 class="sec-title">پرفروش‌ترین <i>محصولات</i></h2><span class="sec-sub">انتخاب هزاران مشتری در سراسر ایران</span></div></span>
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
    <section id="etemad" class="section trust-sec" aria-label="خرید اطمینان">
      <div class="container">
        <div class="sec-head trust-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-shield" /></svg></span>
            <div><h2 class="sec-title">خرید <i>اطمینان</i></h2><span class="sec-sub">هر روز یک کالای منتخب با قیمت ویژه؛ چون به نام ما اعتماد دارید، با خیال راحت بخرید</span></div></span>
          <div class="t-count"><svg class="icon"><use href="#i-clock" /></svg><span>تا پایان پیشنهاد امروز</span><b>{{ trustCd }}</b></div>
        </div>
        <div class="trust-wrap">
          <article class="trust-card">
            <div class="t-media">
              <img :src="trustItem.img" :alt="trustItem.name" loading="lazy">
              <span class="t-daychip">{{ trustLabel }}</span>
              <span class="t-off tag red">٪{{ toFa(trustItem.off) }} تخفیف</span>
            </div>
            <div class="t-body">
              <span class="t-kicker"><svg class="icon"><use href="#i-shield" /></svg> کالای منتخب خانم گل</span>
              <h3 class="t-title">{{ trustItem.name }}</h3>
              <p class="t-why"><b>چرا این‌جا؟</b> {{ TRUST_WHY }}</p>
              <div class="t-price"><del>{{ money(trustItem.old) }}</del><b>{{ money(trustItem.price) }}</b><small>تومان</small><span class="t-save">سود شما: {{ money(trustItem.old - trustItem.price) }} تومان</span></div>
              <div class="t-stock">موجودی امروز محدود است<div class="bar"><i></i></div></div>
              <div class="t-days">
                <span class="lbl">پیشنهاد هر روز هفته:</span>
                <button v-for="d in WEEK_ORDER" :key="d" type="button" class="t-daypill" :class="{ on: d === selDay }" @click="selDay = d">{{ DAY_NAMES[d] }}</button>
              </div>
              <div class="t-actions">
                <button class="btn btn-gold" @click="trustAdd"><svg class="icon"><use href="#i-cart" /></svg> افزودن به سبد</button>
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
    <section id="consult" class="section" aria-label="مشاوره خرید و پیگیری سفارش">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-headset" /></svg></span>
            <div><h2 class="sec-title"><i>مشاوره خرید</i> و پیگیری سفارش</h2><span class="sec-sub">کارشناسان خانم گل پاسخگوی انتخاب‌های شما هستند</span></div></span>
        </div>
        <div class="cons-grid">
          <div class="cons-card hl">
            <div class="cons-top">
              <span class="ci"><svg class="icon"><use href="#i-phone" /></svg></span>
              <div><b>تماس فوری با کارشناس</b><span>شنبه تا پنجشنبه ۹ تا ۲۱ | جمعه‌ها ۱۰ تا ۱۸</span></div>
            </div>
            <p class="cons-text">نمی‌دانید برای مهمانی، هدیه یا رژیم غذایی‌تان چه محصولی مناسب است؟ همین حالا تماس بگیرید تا رایگان راهنمایی‌تان کنیم.</p>
            <div class="cons-actions">
              <a class="btn btn-brand btn-sm" href="tel:02191092000"><svg class="icon"><use href="#i-phone" /></svg> ۰۲۱-۹۱۰۹۲۰۰۰</a>
              <a class="btn btn-light btn-sm" href="https://wa.me/989120000000" target="_blank" rel="noopener"><svg class="icon"><use href="#i-whatsapp" /></svg> واتساپ</a>
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
              <button class="btn btn-gold btn-sm" type="submit"><svg class="icon"><use href="#i-sms" /></svg> ثبت درخواست مشاوره</button>
            </form>
          </div>
          <div class="cons-card track">
            <div class="cons-top">
              <span class="ci"><svg class="icon"><use href="#i-truck" /></svg></span>
              <div><b>پیگیری سفارش</b><span>با کد سفارش یا شماره موبایل</span></div>
            </div>
            <p class="cons-text">بعد از ثبت خرید، کد پیگیری برایتان پیامک می‌شود؛ همین‌جا وضعیت لحظه‌ای سفارش را ببینید.</p>
            <form class="track-row" @submit.prevent="trackInline">
              <input v-model="trackQ" class="fld" type="text" placeholder="کد سفارش مثل AS-1024 یا شماره موبایل" aria-label="کد سفارش">
              <button class="btn btn-brand btn-sm" type="submit">پیگیری</button>
            </form>
            <Timeline v-if="inlineOrder" :order="inlineOrder" />
            <p v-else-if="inlineMsg" style="font-size:.82rem;color:var(--ink-3)">{{ inlineMsg }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== چرا خانم گل ===== -->
    <section id="why" class="section" style="padding-top:0" aria-label="مزایای فروشگاه">
      <div class="container">
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-shield" /></svg></span>
            <div><h2 class="sec-title">چرا <i>خانم گل</i>؟</h2><span class="sec-sub">چهار دلیل برای اعتماد هزاران خانواده ایرانی</span></div></span>
        </div>
        <div class="why-grid">
          <div class="why-card"><span class="wi"><svg class="icon"><use href="#i-leaf" /></svg></span><b>تضمین تازگی و کیفیت</b><p>محصولات روزانه از باغ‌ها دریافت و بو داده می‌شوند؛ اگر راضی نبودید، مرجوعی رایگان است.</p></div>
          <div class="why-card"><span class="wi"><svg class="icon"><use href="#i-box" /></svg></span><b>بسته‌بندی بهداشتی</b><p>بسته‌بندی وکیوم و استاندارد مواد غذایی با درج تاریخ تولید و انقضا روی هر بسته.</p></div>
          <div class="why-card"><span class="wi"><svg class="icon"><use href="#i-truck" /></svg></span><b>ارسال سریع سراسری</b><p>پیک فوری در تهران، پست پیشتاز و تیپاکس به تمام نقاط ایران؛ ارسال رایگان بالای ۱.۵ میلیون.</p></div>
          <div class="why-card"><span class="wi"><svg class="icon"><use href="#i-scale" /></svg></span><b>قیمت منصفانه و شفاف</b><p>خرید مستقیم از باغ‌دار بدون واسطه؛ قیمت‌ها همیشه شفاف و بدون هزینه پنهان.</p></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { useSeo } from '../composables/useSeo';
import { IMG, PACKS, TRUST, TRUST_WHY, TRUST_VPIDS, CATS, prod, visibleProducts } from '../data/catalog';
import { toFa, money, fmtHMS, DAY_NAMES, WEEK_ORDER, LS } from '../data/site';
import { addToCart } from '../stores/cart';
import { toast } from '../stores/ui';
import { findOrder, findByPhone } from '../stores/orders';
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

/* پک‌ها: پایان چرخهٔ هر پک (مانند قالب اصلی) */
function packEnd(pk) {
  const key = 'packend_' + pk.pid;
  let end = LS.get(key, 0);
  const ms = pk.hours * 3600 * 1000;
  if (!end || end - Date.now() < 1000 || end - Date.now() > ms) { end = Date.now() + ms; LS.set(key, end); }
  return end;
}
const packCd = computed(() => {
  const o = {};
  PACKS.forEach(pk => { o[pk.pid] = fmtHMS(packEnd(pk) - now.value); });
  return o;
});

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
const bestList = visibleProducts().filter(p => p.sec.includes('best')).sort((a, b) => b.sold - a.sold).slice(0, 8);
const amzList = visibleProducts().filter(p => p.sec.includes('amz')).sort((a, b) => b.disc - a.disc).slice(0, 6);

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

/* ---------- خرید اطمینان ---------- */
const selDay = ref(new Date().getDay());
const trustItem = computed(() => TRUST.find(t => t.day === selDay.value) || TRUST[0]);
const trustLabel = computed(() => selDay.value === new Date().getDay() ? ('پیشنهاد امروز — ' + DAY_NAMES[selDay.value]) : ('پیش‌نمایش ' + DAY_NAMES[selDay.value]));
function trustAdd() {
  const vpid = TRUST_VPIDS[selDay.value] ?? TRUST_VPIDS[TRUST[0].day];
  addToCart(vpid, 1, 1, true);
  toast(`«${trustItem.value.name}» به سبد اضافه شد؛ نماد اعتماد خانم گل در راه است 🛡️`, 'gold');
}

/* ---------- فرم مشاوره + پیگیری داخل صفحه ---------- */
const cons = reactive({ name: '', phone: '', topic: '' });
function consult() {
  const ph = cons.phone.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/\D/g, '');
  if (!/^09\d{9}$/.test(ph)) return toast('شماره موبایل معتبر وارد کنید', 'err');
  toast('درخواست مشاوره ثبت شد؛ کارشناس خانم گل تا ۳۰ دقیقه دیگر با شما تماس می‌گیرد 📞', 'ok', 5200);
  cons.name = ''; cons.phone = ''; cons.topic = '';
}
const trackQ = ref('');
const inlineOrder = ref(null);
const inlineMsg = ref('');
function trackInline() {
  const q = trackQ.value;
  inlineOrder.value = null; inlineMsg.value = '';
  const byPhone = findByPhone(q);
  if (byPhone.length) { inlineOrder.value = byPhone[0]; return; }
  const o = findOrder(q);
  if (o) { inlineOrder.value = o; return; }
  if (q.trim()) inlineMsg.value = 'سفارشی یافت نشد؛ از صفحه «پیگیری سفارش» با کد صحیح امتحان کنید.';
  else toast('کد سفارش یا شماره موبایل را وارد کنید', 'err');
}
</script>
