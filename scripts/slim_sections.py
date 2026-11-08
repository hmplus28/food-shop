#!/usr/bin/env python3
"""Remove 4 sections (#gifts, #story, #new, #shop) + rewire all references.
Every replacement is asserted to match exactly the expected number of times."""
import re, sys

PATH = "/home/z/my-project/download/فروشگاه-خانم-گل.html"
s = open(PATH, encoding="utf-8").read()
orig_len = len(s)
fails = []

def rep(pattern, repl, n_expected=1, flags=re.DOTALL, label=""):
    global s
    new, n = re.subn(pattern, repl, s, flags=flags)
    if n != n_expected:
        fails.append(f"[{label}] expected {n_expected}, matched {n}")
        return
    s = new
    print(f"  ok: {label} ({n})")

# ---------- HTML ----------
rep(r'\n[ \t]*<a href="#story" data-scroll="#story"><svg class="icon"><use href="#i-leaf"/></svg> داستان خانم گل</a>',
    '', 1, 0, "topbar story link")
rep(r'href="#shop" data-scroll="#shop"><svg class="icon"><use href="#i-cart"/></svg> مشاهده محصولات',
    'href="#best" data-scroll="#best"><svg class="icon"><use href="#i-cart"/></svg> مشاهده محصولات',
    1, 0, "hero slide1 CTA")
rep(r'\n[ \t]*<div class="slide">\s*<div class="s-media"><img src="[^"]*9773f286dee5[^"]*".*?\n[ \t]*</div>(?=\n[ \t]*</div>\n[ \t]*<button class="hero-arrow next")',
    '', 1, re.DOTALL, "hero gift slide")
rep(r'\n[ \t]*<button class="hero-arrow next" id="heroNext".*?</button>', '', 1, re.DOTALL, "hero arrow next")
rep(r'\n[ \t]*<button class="hero-arrow prev" id="heroPrev".*?</button>', '', 1, re.DOTALL, "hero arrow prev")
rep(r'\n[ \t]*<div class="hero-dots" id="heroDots"></div>', '', 1, 0, "hero dots")
rep(r'href="#shop" data-scroll="#shop">همه محصولات', 'href="#best" data-scroll="#best">همه محصولات', 1, 0, "cats see-all")
rep(r'href="#shop" data-scroll="#shop">مشاهده همه', 'href="#best" data-scroll="#best">مشاهده همه', 1, 0, "amz see-all")
rep(r'<!-- ===== تازه‌ها و ممتازها ===== -->.*?<!-- ===== خرید اطمینان ===== -->',
    '<!-- ===== خرید اطمینان ===== -->', 1, re.DOTALL, "sections #new/#shop/#gifts")
rep(r'\n<!-- ===== داستان ما ===== -->\n<section class="section story-sec".*?</section>\n',
    '\n', 1, re.DOTALL, "section #story")

# ---------- footer quick links ----------
for cat, name in [("ajil","آجیل و مغزها"),("pistachio","پسته"),("date","خرما و رطب"),
                  ("saffron","زعفران و ادویه"),("tea","دمنوش و محصولات طبیعی")]:
    rep(rf'<a href="#shop" data-cat="{cat}">{name}</a>',
        f'<a href="#best" data-scroll="#best">{name}</a>', 1, 0, f"footer {cat}")
rep(r'<a href="#gifts" data-scroll="#gifts">آجیل و پک‌های هدیه</a>',
    '<a href="#best" data-scroll="#best">آجیل و پک‌های هدیه</a>', 1, 0, "footer giftbox")

# ---------- JS templates ----------
rep(r'href="#shop" data-scroll="#shop" data-cat="\$\{c\.id\}"><svg class="icon"><use href="#\$\{c\.icon\}"/></svg> \$\{c\.name\}',
    'href="#best" data-scroll="#best"><svg class="icon"><use href="#${c.icon}"/></svg> ${c.name}', 1, 0, "mega main link")
rep(r'<a href="#shop" data-scroll="#shop" data-cat="\$\{c\.id\}" data-search="\$\{s\}">\$\{s\}</a>',
    '<a href="#best" data-scroll="#best">${s}</a>', 2, 0, "mega+drawer sub links")
rep(r'<a href="#shop" data-scroll="#shop" data-cat="\$\{c\.id\}" data-search="\$\{p\.name\}">\$\{p\.name\}</a>',
    '<a href="#best" data-scroll="#best">${p.name}</a>', 1, 0, "mega popular links")
rep(r'<a href="#gifts" data-scroll="#gifts">پک‌های هدیه</a>', '', 1, 0, "mega gifts link")
rep(r'<a class="mega-feat" href="#shop" data-scroll="#shop" data-cat="\$\{c\.id\}">',
    '<a class="mega-feat" href="#best" data-scroll="#best">', 1, 0, "mega feat")
rep(r'<a class="btn btn-brand btn-sm" href="#shop" data-scroll="#shop" style="justify-content:center">مشاهده همه محصولات</a>',
    '<a class="btn btn-brand btn-sm" href="#best" data-scroll="#best" style="justify-content:center">مشاهده همه محصولات</a>',
    1, 0, "drawer CTA")
rep(r'<a class="cat-card" href="#shop" data-scroll="#shop" data-cat="\$\{c\.id\}">',
    '<a class="cat-card" href="#best" data-scroll="#best">', 1, 0, "cat-card")
rep(r'<button class="btn btn-brand btn-sm" data-open="shop-goto">مشاهده محصولات</button>',
    '<a class="btn btn-brand btn-sm" href="#best" data-scroll="#best">مشاهده محصولات</a>', 1, 0, "cart empty CTA")
rep(r'\n[ \t]*\$\$\(\'\[data-open="shop-goto"\]\', box\)\.forEach[^\n]*\n', '\n', 1, 0, "shop-goto binding")

# ---------- search: results add-to-cart, goSearch simplified ----------
rep(r'\? res\.map\(p=>`<a class="sr-item" href="#shop" data-scroll="#shop" data-cat="\$\{p\.cat\}" data-search="\$\{p\.name\}"><img src="\$\{p\.img\}" alt=""><div><div class="n">\$\{p\.name\}</div><div class="p">\$\{money\(priceOf\(p,p\.weights\[1\]\)\)\} تومان</div></div></a>`\)\.join\(\'\'\)',
    '? res.map(p=>`<button class="sr-item" data-sradd="${p.id}"><img src="${p.img}" alt=""><div><div class="n">${p.name}</div><div class="p">${money(priceOf(p,p.weights[1]??p.weights[0]))} تومان</div></div></button>`).join(\'\')',
    1, 0, "search result items")
rep(r"    dd\.classList\.add\('open'\);",
    """      dd.classList.add('open');
    $$('[data-sradd]', dd).forEach(b=>b.addEventListener('click',()=>{
      const p = prod(+b.dataset.sradd);
      addToCart(p.id, p.weights[1]??p.weights[0], 1, true);
      dd.classList.remove('open');
      toast(`«${p.name}» به سبد اضافه شد 🛒`,'ok');
    }));""", 1, 0, "search result binding")
rep(r'function goSearch\(q\)\{\n  \$\$\(\'\.search-dd\'\)\.forEach\(d=>d\.classList\.remove\(\'open\'\)\);\n  scrollToShop\(\);\n  \$\(\'#searchInput\'\)\.value = q; \$\(\'#searchInputM\'\)\.value = q;\n  shopFilter\.q = q\.trim\(\);\n  applyShop\(\);\n\}',
    "function goSearch(q){\n  $$('.search-dd').forEach(d=>d.classList.remove('open'));\n  $('#best').scrollIntoView({behavior:'smooth'});\n}",
    1, 0, "goSearch")

# ---------- remove shop JS ----------
rep(r'\n/\* ---------- فیلتر و مرتب‌سازی فروشگاه ---------- \*/\nconst shopFilter.*?function scrollToShop\(\)\{ \$\(\'#shop\'\)\.scrollIntoView\(\{behavior:\'smooth\'\}\); \}\n',
    '\n', 1, re.DOTALL, "shopFilter/applyShop/scrollToShop")
rep(r'   پک هدیه، خرید اطمینان، چیپس دسته‌ها', '   خرید اطمینان و چیپس دسته‌ها', 1, 0, "section comment")
rep(r'const GIFTS = \[.*?\n\}\n(?=\nconst DAY_NAMES)', '', 1, re.DOTALL, "GIFTS/renderGifts")
rep(r'    if\(sc\.dataset\.cat\)\{ setShopCat\(sc\.dataset\.cat\); \}\n    if\(sc\.dataset\.search\)\{[^\n]*\n', '', 1, 0, "global cat/search branches")
rep(r"  const st = e\.target\.closest\('\[data-setcat\]'\);\n  if\(st\)\{ setShopCat\(st\.dataset\.setcat\); scrollToShop\(\); return; \}\n",
    '', 1, 0, "data-setcat branch")
rep(r'function setShopCat\(id\)\{.*?\n\}\n(?=document\.addEventListener)', '', 1, re.DOTALL, "setShopCat")
rep(r'\nfunction bindShopControls\(\)\{.*?\n\}\n', '\n', 1, re.DOTALL, "bindShopControls")
rep(r"  renderRail\('newRail',[^\n]*\n", '', 1, 0, "init newRail")
rep(r'  renderGifts\(\);\n', '', 1, 0, "init renderGifts")
rep(r'  bindShopControls\(\);\n  applyShop\(\);\n', '', 1, 0, "init shop calls")
rep(r'  heroInit\(\);\n', '', 1, 0, "init heroInit")
rep(r'\n/\* =+\n   اسلایدر هیرو\n=+ \*/\nlet heroIdx = 0, heroTimer = null;\nconst heroN = 3;.*?function heroRestart\(\)\{ clearInterval\(heroTimer\); heroTimer = setInterval\(\(\)=>heroGo\(heroIdx\+1\), 6000\); \}\n',
    '\n', 1, re.DOTALL, "hero JS block")

if fails:
    print("\nFAILED — file NOT modified:")
    [print(" ", f) for f in fails]
    sys.exit(1)

open(PATH, "w", encoding="utf-8").write(s)
print(f"\nAll replacements OK. size {orig_len} -> {len(s)} bytes (-{orig_len-len(s)})")
