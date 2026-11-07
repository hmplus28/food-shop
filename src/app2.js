
/* ---------- Shop: filters / sort / search ---------- */
function setShopCat(key) {
  shopState.cat = key; shopState.shown = 8;
  renderChips(); renderShop();
  document.getElementById('shop').scrollIntoView({ behavior: 'smooth' });
}
function renderChips() {
  const chips = [{ key: 'all', name: 'همه محصولات' }, ...CATEGORIES.map(c => ({ key: c.key, name: c.name }))];
  let html = chips.map(c =>
    `<button class="f-chip${shopState.cat === c.key ? ' active' : ''}" data-fcat="${c.key}">${c.name}</button>`).join('');
  if (shopState.query) {
    html += `<button class="f-chip active" id="clearQuery">حذف جستجو: «${esc(shopState.query)}» ✕</button>`;
  }
  $('#catChips').innerHTML = html;
  $('#catChips').onclick = e => {
    const b = e.target.closest('.f-chip'); if (!b) return;
    if (b.id === 'clearQuery') { shopState.query = ''; $('#searchInput').value = ''; $('#searchInputM').value = ''; shopState.shown = 8; renderChips(); renderShop(); return; }
    shopState.cat = b.dataset.fcat; shopState.shown = 8; renderChips(); renderShop();
  };
}
function filteredProducts() {
  let list = PRODUCTS.filter(p => {
    if (shopState.cat !== 'all' && p.cat !== shopState.cat) return false;
    if (basePrice(p) > shopState.maxP) return false;
    if (shopState.query) {
      const q = shopState.query.trim();
      const hay = p.name + ' ' + CAT_NAMES[p.cat] + ' ' + (p.grade || '') + ' ' + (p.desc || '');
      if (!hay.includes(q)) return false;
    }
    return true;
  });
  const s = shopState.sort;
  list.sort((a, b) =>
    s === 'cheap' ? basePrice(a) - basePrice(b) :
    s === 'exp' ? basePrice(b) - basePrice(a) :
    s === 'off' ? b.off - a.off :
    s === 'rate' ? b.rate - a.rate :
    (b.sold || 0) - (a.sold || 0));
  return list;
}
function renderShop() {
  const list = filteredProducts();
  const shown = list.slice(0, shopState.shown);
  const grid = $('#productsGrid');
  grid.innerHTML = shown.length
    ? shown.map(cardHTML).join('')
    : `<div class="no-result"><svg><use href="#i-search"/></svg><b>محصولی یافت نشد!</b>عبارت جستجو یا فیلترها را تغییر دهید.</div>`;
  $('#shopResult').innerHTML = list.length
    ? `نمایش <b class="num">${faInt(shown.length)}</b> از <b class="num">${faInt(list.length)}</b> محصول${shopState.query ? ` برای جستجوی «${esc(shopState.query)}»` : ''}`
    : '';
  $('#showMoreWrap').style.display = list.length > shopState.shown ? '' : 'none';
  $$('img', grid).forEach(safeImg);
}
$('#showMoreBtn').addEventListener('click', () => {
  shopState.shown += 8; renderShop();
});
$('#sortSel').addEventListener('change', e => { shopState.sort = e.target.value; renderShop(); });

/* price range slider */
const PRICE_MAX = 6000000;
const priceRange = $('#priceRange'), priceOut = $('#priceOut');
priceRange.addEventListener('input', () => {
  const v = +priceRange.value;
  shopState.maxP = v >= 100 ? Infinity : Math.max(50000, Math.round(PRICE_MAX * v / 100 / 10000) * 10000);
  priceOut.textContent = v >= 100 ? 'نامحدود' : 'تا ' + faInt(shopState.maxP);
  shopState.shown = 8;
  renderShop();
});

/* ---------- Search + suggestions ---------- */
function sugHTML(list) {
  if (!list.length) return `<p class="sug-empty">محصولی مطابق جستجوی شما پیدا نشد؛ عبارت دیگری را امتحان کنید.</p>`;
  return `<p class="sug-head">پیشنهاد محصولات</p>` + list.map(p =>
    `<button class="sug-item" data-sug="${p.id}">
      <img src="${p.img}" alt="" width="46" height="46">
      <span><span class="si-name">${esc(p.name)}</span><span class="si-price num">${fmtPrice(basePrice(p))}</span></span>
      <svg class="si-arrow"><use href="#i-arrl"/></svg>
    </button>`).join('');
}
function wireSearch(inputId, panelId, boxId, hasBtn) {
  const input = $(inputId), panel = $(panelId), box = $(boxId);
  const close = () => box.classList.remove('open-sug');
  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (q.length < 2) { close(); return; }
    const list = PRODUCTS.filter(p => (p.name + ' ' + CAT_NAMES[p.cat]).includes(q)).slice(0, 6);
    panel.innerHTML = sugHTML(list);
    box.classList.add('open-sug');
  });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); submitSearch(input.value); close(); }
    if (e.key === 'Escape') close();
  });
  if (hasBtn) $(hasBtn).addEventListener('click', () => { submitSearch(input.value); close(); });
  panel.addEventListener('click', e => {
    const b = e.target.closest('.sug-item'); if (!b) return;
    input.value = P_BY_ID[+b.dataset.sug].name.split(' ').slice(0, 2).join(' ');
    submitSearch(input.value); close();
  });
  document.addEventListener('click', e => { if (!box.contains(e.target)) close(); });
}
function submitSearch(q) {
  q = (q || '').trim();
  if (!q) { toast('عبارتی برای جستجو وارد کنید.', 'success'); return; }
  shopState.query = q; shopState.cat = 'all'; shopState.shown = 8;
  renderChips(); renderShop();
  document.getElementById('shop').scrollIntoView({ behavior: 'smooth' });
}
wireSearch('#searchInput', '#sugPanelD', '#searchBoxD', '#searchBtnD');
wireSearch('#searchInputM', '#sugPanelM', '#searchBoxM', '#searchBtnM');

/* ---------- Hero slider ---------- */
(function hero() {
  const slides = $$('.hero-slide');
  const dotsBox = $('#heroDots');
  let cur = 0, timer;
  slides.forEach((_, i) => {
    const b = document.createElement('button');
    b.setAttribute('aria-label', 'اسلاید ' + faInt(i + 1));
    if (!i) b.classList.add('active');
    b.addEventListener('click', () => go(i, true));
    dotsBox.appendChild(b);
  });
  const dots = $$('button', dotsBox);
  function go(i, manual) {
    slides[cur].classList.remove('active'); dots[cur].classList.remove('active');
    cur = (i + slides.length) % slides.length;
    slides[cur].classList.add('active'); dots[cur].classList.add('active');
    if (manual) restart();
  }
  function restart() { clearInterval(timer); timer = setInterval(() => go(cur + 1), 6500); }
  $('#heroNext').addEventListener('click', () => go(cur + 1, true));
  $('#heroPrev').addEventListener('click', () => go(cur - 1, true));
  // RTL: 'next' scrolls content leftwards
  void 0;
  const zone = $('#heroSlider');
  zone.addEventListener('mouseenter', () => clearInterval(timer));
  zone.addEventListener('mouseleave', restart);
  let sx = null;
  zone.addEventListener('touchstart', e => sx = e.touches[0].clientX, { passive: true });
  zone.addEventListener('touchend', e => {
    if (sx === null) return;
    const dx = e.changedTouches[0].clientX - sx;
    if (Math.abs(dx) > 46) go(cur + (dx > 0 ? 1 : -1), true);
    sx = null;
  }, { passive: true });
  restart();
})();

/* ---------- Countdown ---------- */
(function countdown() {
  let deadline = LS.get('ds_deadline', 0);
  if (!deadline || deadline < Date.now()) {
    deadline = Date.now() + (2 * 24 * 3600 + 11 * 3600 + 23 * 60) * 1000;
    LS.set('ds_deadline', deadline);
  }
  const two = n => faInt(n).padStart(2, '۰');
  function tick() {
    let d = Math.max(0, deadline - Date.now()) / 1000;
    const days = Math.floor(d / 86400); d %= 86400;
    const h = Math.floor(d / 3600); d %= 3600;
    const m = Math.floor(d / 60), s = Math.floor(d % 60);
    $('#cdDays').textContent = two(days);
    $('#cdHrs').textContent = two(h);
    $('#cdMin').textContent = two(m);
    $('#cdSec').textContent = two(s);
  }
  tick(); setInterval(tick, 1000);
})();

/* ---------- Scroll rows ---------- */
$$('.row-arrow').forEach(btn => {
  btn.addEventListener('click', () => {
    const row = document.getElementById(btn.dataset.row);
    const step = row.clientWidth * .8;
    row.scrollBy({ left: btn.classList.contains('next') ? -step : step, behavior: 'smooth' });
  });
});

/* ---------- Topbar messages ---------- */
(function topMsgs() {
  const msgs = $$('.topbar-msg'); let i = 0;
  setInterval(() => {
    msgs[i].classList.remove('active');
    i = (i + 1) % msgs.length;
    msgs[i].classList.add('active');
  }, 4200);
})();

/* ---------- Reveal on scroll + count-up ---------- */
const io = new IntersectionObserver(entries => {
  entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
}, { threshold: .12 });
$$('.rv').forEach(el => io.observe(el));

const statIO = new IntersectionObserver(entries => {
  entries.forEach(en => {
    if (!en.isIntersecting) return;
    const el = en.target, target = +el.dataset.count, t0 = performance.now();
    (function step(t) {
      const k = Math.min(1, (t - t0) / 1400);
      el.textContent = faInt(Math.round(target * (1 - Math.pow(1 - k, 3))));
      if (k < 1) requestAnimationFrame(step);
    })(t0);
    statIO.unobserve(el);
  });
}, { threshold: .6 });
$$('[data-count]').forEach(el => statIO.observe(el));

/* ---------- Header / to-top on scroll ---------- */
const header = $('#siteHeader'), toTop = $('#toTop');
window.addEventListener('scroll', () => {
  header.classList.toggle('scrolled', scrollY > 8);
  toTop.classList.toggle('show', scrollY > 900);
}, { passive: true });
toTop.addEventListener('click', () => scrollTo({ top: 0, behavior: 'smooth' }));

/* ---------- Newsletter ---------- */
$('#nlForm').addEventListener('submit', e => {
  e.preventDefault();
  const v = $('#nlInput').value.trim();
  const isMail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  const isPhone = /^09\d{9}$/.test(faToEn(v));
  if (!isMail && !isPhone) { toast('لطفاً یک <b>ایمیل معتبر</b> یا <b>شماره موبایل</b> (۰۹...) وارد کنید.', 'success'); return; }
  toast('<b>عضویت شما ثبت شد!</b><br>کد تخفیف ۱۰٪ اولین خرید برایتان ارسال می‌شود.');
  $('#nlInput').value = '';
});

/* ---------- Misc ---------- */
$('#loginBtn').addEventListener('click', e => { e.preventDefault(); toast('این بخش در قالب نمایشی غیرفعال است.', 'success'); });
$('#bulkBtn').addEventListener('click', e => { e.preventDefault(); toast('<b>درخواست شما ثبت شد.</b><br>کارشناس فروش عمده تا ۲۴ ساعت آینده تماس می‌گیرد.'); });
$$('.gift-card').forEach(a => a.addEventListener('click', e => {
  e.preventDefault();
  const id = +a.dataset.gift, p = P_BY_ID[id];
  if (!p) return;
  shopState.query = p.name.split(' ')[0]; shopState.cat = 'all'; shopState.shown = 24;
  renderChips(); renderShop();
  document.getElementById('shop').scrollIntoView({ behavior: 'smooth' });
  setTimeout(() => { const c = $(`.p-card[data-id="${id}"]`); if (c) c.classList.add('flash'); }, 700);
}));

/* ---------- Init ---------- */
renderNav();
renderMobileMenu();
renderCatsGrid();
$('#offersRow').innerHTML = PRODUCTS.filter(p => p.off > 0).map(cardHTML).join('');
$('#bestGrid').innerHTML = [1, 2, 4, 5, 7, 8, 10, 12].map(id => cardHTML(P_BY_ID[id])).join('');
$('#freshRow').innerHTML = [27, 25, 26, 19, 21, 23, 22, 29, 30, 31].map(id => cardHTML(P_BY_ID[id])).join('');
renderChips();
renderShop();
$('#testiGrid').innerHTML = TESTIMONIALS.map((t, i) => `
  <div class="t-card rv rv-d${i % 3}">
    <span class="t-quote">”</span>
    <div class="t-stars">${starsHTML(t.rate)}</div>
    <p class="t-text">${t.text}</p>
    <div class="t-user">
      <span class="t-ava" style="background:${t.color}">${t.name.split(' ')[0][0]}${t.name.split(' ')[1]?.[0] || ''}</span>
      <span><b>${t.name}</b><small>${t.city} — عضویت: ${t.since}</small></span>
      <span class="t-buy">خرید: ${t.product}</span>
    </div>
  </div>`).join('');
$$('.rv:not(.in)').forEach(el => io.observe(el));
$$('img').forEach(safeImg);
$('#wishBadge').textContent = faInt(wish.length);
renderCart();
bindCardEvents(document);
