/* ============ دانه‌سرا — App (Vanilla JS) ============ */
'use strict';

/* ---------- Helpers ---------- */
const $  = (s, c = document) => c.querySelector(s);
const $$ = (s, c = document) => [...c.querySelectorAll(s)];
const faNum = n => Number(n).toLocaleString('fa-IR', { maximumFractionDigits: 1 });
const faInt = n => Number(n).toLocaleString('fa-IR');
const fmtPrice = n => faInt(n) + ' تومان';
const esc = s => String(s).replace(/[&<>"]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]));
const starSVG = cls => `<svg class="${cls}"><use href="#i-star"/></svg>`;
const LS = {
  get: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
  set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }
};
const FALLBACK = 'data:image/svg+xml;utf8,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#F2E9D8"/><ellipse cx="50" cy="46" rx="14" ry="20" fill="#C9A227" opacity=".55"/><text x="50" y="86" font-size="9" text-anchor="middle" fill="#8D7B66" font-family="sans-serif">دانه‌سرا</text></svg>`);
function safeImg(img) { img.addEventListener('error', () => { img.src = FALLBACK; }, { once: true }); }

/* ---------- Data ---------- */
const FREE_SHIP = 1500000;
const CAT_NAMES = {}; CATEGORIES.forEach(c => CAT_NAMES[c.key] = c.name);
const P_BY_ID = {}; PRODUCTS.forEach(p => P_BY_ID[p.id] = p);
const weightLabel = w => w >= 1000 ? faNum(w / 1000) + ' کیلوگرم' : faNum(w) + ' گرم';
const finalPrice = (p, g) => Math.round(p.price * (g / 1000) * (1 - p.off / 100) / 1000) * 1000;
const oldPrice = (p, g) => p.off ? Math.round(p.price * (g / 1000) / 1000) * 1000 : 0;
const basePrice = p => finalPrice(p, p.weights[0]);

/* ---------- State ---------- */
let cart = LS.get('ds_cart', {});      // { "id-g": qty }
let wish = LS.get('ds_wish', []);      // [id]
const shopState = { cat: 'all', sort: 'pop', maxP: Infinity, query: '', shown: 8 };

/* ---------- Toast ---------- */
function toast(msg, type = 'success', html = '') {
  const zone = $('#toastZone');
  const icons = { success: '#i-check', cart: '#i-cart', love: '#i-heart' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="t-ico"><svg><use href="${icons[type] || '#i-check'}"/></svg></span><div>${msg}${html}</div>`;
  zone.appendChild(el);
  setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 320); }, 3000);
  if (zone.children.length > 3) zone.firstElementChild.remove();
}

/* ---------- Product card ---------- */
function starsHTML(rate) {
  const full = Math.round(rate);
  let out = '';
  for (let i = 1; i <= 5; i++) out += starSVG(i <= full ? '' : 'off');
  return `<span class="stars" aria-hidden="true">${out}</span>`;
}
function cardHTML(p) {
  const g = p.weights[0];
  const tags = [];
  if (p.off) tags.push(`<span class="p-tag off num">٪${faNum(p.off)}-</span>`);
  if (p.tags?.includes('premium')) tags.push('<span class="p-tag premium">ممتاز</span>');
  if (p.tags?.includes('hot')) tags.push('<span class="p-tag hot">پرفروش</span>');
  if (p.tags?.includes('new')) tags.push('<span class="p-tag new">تازه‌بوستی</span>');
  const chips = p.weights.map((w, i) =>
    `<button class="w-chip num${i === 0 ? ' active' : ''}" data-w="${w}" aria-label="وزن ${weightLabel(w)}">${weightLabel(w)}</button>`).join('');
  const inWish = wish.includes(p.id);
  return `
  <article class="p-card" data-id="${p.id}">
    <div class="p-media">
      <img src="${p.img}" alt="${esc(p.name)}" width="520" height="520" loading="lazy">
      <div class="p-tags">${tags.join('')}</div>
      <button class="p-wish${inWish ? ' active' : ''}" data-wish="${p.id}" aria-label="افزودن به علاقه‌مندی‌ها" title="علاقه‌مندی">
        <svg viewBox="0 0 24 24"><use href="#i-heart"/></svg>
      </button>
    </div>
    <div class="p-body">
      <span class="p-cat">${CAT_NAMES[p.cat]}${p.grade ? ' · ' + esc(p.grade) : ''}</span>
      <h3 class="p-name">${esc(p.name)}</h3>
      <div class="p-rate">${starsHTML(p.rate)}<b class="num">${faNum(p.rate)}</b><span class="num">(${faInt(p.rateCount)})</span></div>
      <div class="p-weights" role="group" aria-label="انتخاب وزن">${chips}</div>
      <div class="p-price">
        <span>
          <span class="pp-old num">${p.off ? fmtPrice(oldPrice(p, g)) : ''}</span>
          <span class="pp-new num">${faInt(finalPrice(p, g))}<small>تومان</small></span>
        </span>
      </div>
      <div class="p-buy">
        <div class="qty">
          <button data-a="inc" aria-label="افزایش تعداد"><svg><use href="#i-plus"/></svg></button>
          <input class="num" value="۱" inputmode="numeric" aria-label="تعداد" readonly>
          <button data-a="dec" aria-label="کاهش تعداد"><svg><use href="#i-minus"/></svg></button>
        </div>
        <button class="add-btn" data-add="${p.id}"><svg><use href="#i-cart"/></svg><span>افزودن به سبد</span></button>
      </div>
    </div>
  </article>`;
}

function bindCardEvents(root) {
  root.addEventListener('click', e => {
    const card = e.target.closest('.p-card'); if (!card) return;
    const p = P_BY_ID[+card.dataset.id];
    const chip = e.target.closest('.w-chip');
    if (chip) {
      $$('.w-chip', card).forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const g = +chip.dataset.w;
      const oldEl = $('.pp-old', card), newEl = $('.pp-new', card);
      oldEl.textContent = p.off ? fmtPrice(oldPrice(p, g)) : '';
      newEl.innerHTML = faInt(finalPrice(p, g)) + '<small>تومان</small>';
      return;
    }
    const qtyBtn = e.target.closest('.qty button');
    if (qtyBtn) {
      const input = $('.qty input', card);
      let v = Math.max(1, +faToEn(input.value) || 1);
      v = qtyBtn.dataset.a === 'inc' ? Math.min(99, v + 1) : Math.max(1, v - 1);
      input.value = faInt(v);
      return;
    }
    const addBtn = e.target.closest('.add-btn');
    if (addBtn) {
      const g = +$('.w-chip.active', card).dataset.w;
      const q = Math.min(99, Math.max(1, +faToEn($('.qty input', card).value) || 1));
      addToCart(p.id, g, q);
      addBtn.classList.add('added');
      $('.add-btn span', card).textContent = 'به سبد اضافه شد';
      setTimeout(() => { addBtn.classList.remove('added'); $('.add-btn span', card).textContent = 'افزودن به سبد'; }, 1400);
      return;
    }
    const wishBtn = e.target.closest('.p-wish');
    if (wishBtn) toggleWish(+wishBtn.dataset.wish, wishBtn);
  });
}
const faToEn = s => String(s).replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));

/* ---------- Cart ---------- */
function addToCart(id, g, q = 1) {
  const key = `${id}-${g}`;
  const have = Math.max(0, Math.round(+cart[key] || 0));
  q = Math.max(1, Math.round(+q || 1));
  const p = P_BY_ID[id];
  const stock = p.stock || 99;
  if (have + q > stock) { toast('موجودی کافی نیست؛ حداکثر ' + faInt(stock) + ' عدد از این کالا موجود است.', 'cart'); return; }
  cart[key] = have + q;
  LS.set('ds_cart', cart);
  renderCart();
  const name = p.name;
  toast(`<b>${esc(name)}</b><br>به سبد خرید اضافه شد (${weightLabel(g)})`, 'cart');
  const badge = $('#cartBadge');
  badge.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.5)' }, { transform: 'scale(1)' }], { duration: 400 });
}
function setQty(key, q) {
  q = Math.round(+q || 0);
  if (q <= 0) delete cart[key]; else cart[key] = Math.min(99, q);
  LS.set('ds_cart', cart); renderCart();
}
function removeItem(key, el) {
  el.classList.add('removing');
  setTimeout(() => { delete cart[key]; LS.set('ds_cart', cart); renderCart(); }, 280);
}
function cartEntries() {
  return Object.entries(cart).map(([k, raw]) => {
    const q = Math.max(1, Math.min(99, Math.round(+raw || 1)));
    const [id, g] = k.split('-').map(Number);
    const p = P_BY_ID[id];
    return { key: k, p, g, q, price: finalPrice(p, g), old: oldPrice(p, g) };
  }).filter(e => e.p);
}
function renderCart() {
  const entries = cartEntries();
  const count = entries.reduce((s, e) => s + e.q, 0);
  const sub = entries.reduce((s, e) => s + e.price * e.q, 0);
  const save = entries.reduce((s, e) => s + (e.old ? (e.old - e.price) * e.q : 0), 0);
  $('#cartBadge').textContent = faInt(count);
  $('#cartAmount').textContent = faInt(sub) + ' تومان';
  $('#cdCount').textContent = faInt(count) + ' کالا';
  $('#cartSub').textContent = fmtPrice(sub);
  $('#cartSave').textContent = '− ' + fmtPrice(save);
  $('#cartTotal').textContent = fmtPrice(Math.max(sub, 0));
  // free shipping progress
  const pct = Math.min(100, sub / FREE_SHIP * 100);
  $('#shipFill').style.width = pct + '%';
  $('#shipText').innerHTML = sub >= FREE_SHIP
    ? '<b>تبریک!</b> ارسال سفارش شما رایگان شد.'
    : `تا ارسال رایگان فقط <b>${fmtPrice(FREE_SHIP - sub)}</b> مانده است.`;
  $('#shipBox').style.display = entries.length ? '' : 'none';
  $('#cartFoot').style.display = entries.length ? '' : 'none';
  const box = $('#cartItems');
  if (!entries.length) {
    box.innerHTML = `<div class="cd-empty">
      <svg><use href="#i-cart"/></svg>
      <b>سبد خرید شما خالی است!</b>
      <p>از پیشنهادهای ویژه و پرفروش‌ترین‌ها شروع کنید؛ تازه‌بوستی امروز را از دست ندهید.</p>
      <button class="btn btn-primary btn-sm" id="goShop">مشاهده محصولات</button></div>`;
    $('#goShop')?.addEventListener('click', () => { closeCart(); document.getElementById('shop').scrollIntoView({ behavior: 'smooth' }); });
    return;
  }
  box.innerHTML = entries.map(e => `
    <div class="ci-card" data-key="${e.key}">
      <img class="ci-img" src="${e.p.img}" alt="${esc(e.p.name)}" width="74" height="74">
      <div class="ci-info">
        <span class="ci-name">${esc(e.p.name)}</span>
        <span class="ci-meta num">وزن: ${weightLabel(e.g)} × ${faInt(e.q)}</span>
        <div class="ci-bottom">
          <div class="ci-qty">
            <button data-a="inc" aria-label="افزایش"><svg><use href="#i-plus"/></svg></button>
            <span class="num">${faInt(e.q)}</span>
            <button data-a="dec" aria-label="کاهش"><svg><use href="#i-minus"/></svg></button>
          </div>
          <span class="ci-price num">${faInt(e.price * e.q)}<small> تومان</small></span>
        </div>
      </div>
      <button class="ci-del" aria-label="حذف از سبد"><svg><use href="#i-trash"/></svg></button>
    </div>`).join('');
  $$('.ci-card', box).forEach(card => {
    const key = card.dataset.key;
    const e = entries.find(x => x.key === key);
    card.addEventListener('click', ev => {
      const b = ev.target.closest('button'); if (!b) return;
      if (b.classList.contains('ci-del')) { removeItem(key, card); toast('کالا از سبد حذف شد.', 'cart'); return; }
      const q = b.dataset.a === 'inc' ? e.q + 1 : e.q - 1;
      setQty(key, q);
    });
  });
}
/* drawer */
const cartDrawer = $('#cartDrawer'), cartBackdrop = $('#cartBackdrop');
function openCart() { cartDrawer.classList.add('open'); cartBackdrop.classList.add('show'); cartDrawer.setAttribute('aria-hidden', 'false'); document.body.style.overflow = 'hidden'; }
function closeCart() { cartDrawer.classList.remove('open'); cartBackdrop.classList.remove('show'); cartDrawer.setAttribute('aria-hidden', 'true'); document.body.style.overflow = ''; }
$('#cartBtn').addEventListener('click', openCart);
$('#cartClose').addEventListener('click', closeCart);
cartBackdrop.addEventListener('click', closeCart);
$('#checkoutBtn').addEventListener('click', () => toast('این یک قالب نمایشی است؛ صفحه پرداخت در نسخه نهایی متصل می‌شود.', 'success'));
document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeCart(); closeDrawer(); } });

/* ---------- Wishlist ---------- */
function toggleWish(id, btn) {
  const i = wish.indexOf(id);
  const on = i === -1;
  if (on) wish.push(id); else wish.splice(i, 1);
  LS.set('ds_wish', wish);
  $('#wishBadge').textContent = faInt(wish.length);
  if (btn) btn.classList.toggle('active', on);
  const p = P_BY_ID[id];
  toast(on ? `<b>${esc(p.name)}</b><br>به علاقه‌مندی‌ها اضافه شد` : 'از علاقه‌مندی‌ها حذف شد', 'love');
}
$('#wishBtn').addEventListener('click', () => toast(wish.length
  ? `<b>${faInt(wish.length)} کالا</b> در فهرست علاقه‌مندی‌ها دارید.`
  : 'فهرست علاقه‌مندی‌های شما خالی است؛ با آیکون قلب محصولات را ذخیره کنید.', 'love'));

/* ---------- Render sections ---------- */
function renderCatsGrid() {
  const POP = [
    { key: 'nuts', img: 'nuts_2', label: 'آجیل و مغزها' },
    { key: 'pistachio', img: 'pistachio_3', label: 'پسته' },
    { key: 'almond', img: 'almond_1', label: 'بادام' },
    { key: 'walnut', img: 'walnut-kernel_1', label: 'گردو' },
    { key: 'driedfruit', img: 'apricot_0', label: 'میوه خشک' },
    { key: 'date', img: 'date-medjool_2', label: 'خرما و کشمش' },
    { key: 'seeds', img: 'pumpkin-seeds_0', label: 'تخمه و دانه‌ها' },
    { key: 'gift', img: 'gift-lux_1', label: 'پک‌های هدیه' },
  ];
  $('#catsGrid').innerHTML = POP.map((c, i) => {
    const n = PRODUCTS.filter(p => p.cat === c.key || (c.key === 'date' && p.cat === 'raisin')).length;
    return `<a class="cat-card rv rv-d${i % 4}" href="#shop" data-cat="${c.key}">
      <img src="${IMG[c.img]}" alt="${c.label}" width="200" height="200" loading="lazy">
      <b>${c.label}</b><small class="num">${faInt(n)} محصول</small></a>`;
  }).join('');
  $('#catsGrid').addEventListener('click', e => {
    const a = e.target.closest('.cat-card'); if (!a) return;
    e.preventDefault();
    setShopCat(a.dataset.cat);
  });
}

/* desktop nav + mega */
function renderNav() {
  const li = CATEGORIES.map((c, i) => {
    if (i === 0) {
      const prods = PRODUCTS.filter(p => ['nuts', 'pistachio', 'almond', 'walnut', 'hazelnut'].includes(p.cat)).slice(0, 4);
      return `<li class="cat-nav-item has-mega">
        <a href="#shop" data-cat="${c.key}"><svg><use href="#i-cart"/></svg>${c.name}</a>
        <div class="mega" role="menu">
          <div class="mega-col">
            <h4>مغزها و آجیل</h4>
            <ul>
              <li><a href="#shop" data-cat="pistachio">پسته و مغز پسته</a></li>
              <li><a href="#shop" data-cat="almond">بادام درختی و هندی</a></li>
              <li><a href="#shop" data-cat="walnut">گردو و مغز گردو</a></li>
              <li><a href="#shop" data-cat="hazelnut">فندق خام و بو داده</a></li>
              <li><a href="#shop" data-cat="nuts">آجیل مخلوط و بو داده</a></li>
            </ul>
          </div>
          <div class="mega-col">
            <h4>خشکبار سنتی</h4>
            <ul>
              <li><a href="#shop" data-cat="raisin">کشمش، مویز و قیسی</a></li>
              <li><a href="#shop" data-cat="date">خرما و رطب تازه</a></li>
              <li><a href="#shop" data-cat="fig">انجیر، توت و برنجک</a></li>
              <li><a href="#shop" data-cat="driedfruit">برگه‌ها و چیپس میوه</a></li>
              <li><a href="#shop" data-cat="seeds">تخمه و مغز تخمه</a></li>
              <li><a href="#shop" data-cat="saffron">زعفران و ادویه</a></li>
            </ul>
          </div>
          <div class="mega-side">
            <h5>آجیل شب یلدا، آماده‌ی جشن!</h5>
            <p>میکس ممتاز چهار مغز با بسته‌بندی هدیه؛ سفارش‌های یلدا از اول آذر ثبت می‌شود.</p>
            <a class="mega-cta" href="#shop" data-cat="gift">مشاهده پک‌ها<svg><use href="#i-arrl"/></svg></a>
            <img src="${IMG['pistachio-b_1']}" alt="آجیل ممتاز" loading="lazy">
          </div>
        </div>
      </li>`;
    }
    const items = PRODUCTS.filter(p => p.cat === c.key).slice(0, 3);
    const drop = items.map(p => `<a href="#shop" data-cat="${c.key}"><svg><use href="#i-leaf"/></svg>${esc(p.name)}</a>`).join('');
    return `<li class="cat-nav-item">
      <a href="#shop" data-cat="${c.key}">${c.name}</a>
      <div class="dropdown">${drop}<a href="#shop" data-cat="${c.key}" style="color:var(--gold-deep);font-weight:800">مشاهده همه ${c.name}</a></div>
    </li>`;
  }).join('');
  $('#catNavList').innerHTML = li;
  $('#catNavList').addEventListener('click', e => {
    const a = e.target.closest('a[data-cat]'); if (!a) return;
    e.preventDefault(); setShopCat(a.dataset.cat);
  });
}

/* mobile accordion */
function renderMobileMenu() {
  $('#mMenuCats').innerHTML = `
    <button class="m-acc-btn" aria-expanded="false"><svg><use href="#i-menu"/></svg>دسته‌بندی محصولات<svg class="chev"><use href="#i-chev"/></svg></button>
    <div class="m-acc-panel">
      ${CATEGORIES.map(c => `<a href="#shop" data-cat="${c.key}">${c.name}</a>`).join('')}
    </div>`;
  const acc = $('#mMenuCats');
  acc.querySelector('.m-acc-btn').addEventListener('click', function () {
    const panel = acc.querySelector('.m-acc-panel');
    const open = this.parentElement.classList.toggle('open');
    this.setAttribute('aria-expanded', open);
    panel.style.maxHeight = open ? panel.scrollHeight + 'px' : '0';
  });
  $('#mMenuCats').addEventListener('click', e => {
    const a = e.target.closest('a[data-cat]'); if (!a) return;
    e.preventDefault(); closeDrawer(); setShopCat(a.dataset.cat);
  });
}

const mDrawer = $('#mDrawer'), drawerBackdrop = $('#drawerBackdrop');
function openDrawer() { mDrawer.classList.add('open'); drawerBackdrop.classList.add('show'); mDrawer.setAttribute('aria-hidden', 'false'); document.body.style.overflow = 'hidden'; }
function closeDrawer() { mDrawer.classList.remove('open'); drawerBackdrop.classList.remove('show'); mDrawer.setAttribute('aria-hidden', 'true'); document.body.style.overflow = ''; }
$('#hambBtn').addEventListener('click', openDrawer);
$('#mDrawerClose').addEventListener('click', closeDrawer);
drawerBackdrop.addEventListener('click', closeDrawer);
