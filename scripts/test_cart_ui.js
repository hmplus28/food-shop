// تست رفتاری سبد خرید (Playwright). پیش‌نیاز: cd app && npm run build && npx vite preview --port 4173
// اجرا: node scripts/test_cart_ui.js
const { chromium } = require('playwright');
const U='http://localhost:4173/food-shop/';
let ok=0,bad=0;
const t=(n,c,d='')=>{ (c?ok++:bad++); console.log((c?'✓ ':'✗ ')+n+(c?'':'  → '+d)); };
const fa=s=>s.replace(/[۰-۹]/g,d=>'۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٬,\s]/g,'');
(async()=>{
 const b=await chromium.launch();
 const ctx=await b.newContext({viewport:{width:1280,height:900}});
 await ctx.addInitScript(()=>{try{sessionStorage.setItem('asalat_lucky_seen','1')}catch(e){}});
 const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 const ls=()=>p.evaluate(()=>JSON.parse(localStorage.getItem('asalat_cart')||'[]'));
 const go=async(path)=>{await p.goto(U+path,{waitUntil:'networkidle'});await p.waitForTimeout(250);};
 const toast=async()=>p.evaluate(()=>[...document.querySelectorAll('[class*=toast]')].map(e=>e.textContent).join('|'));
 const num=async(sel)=>fa(await p.locator(sel).first().innerText());
 await go('cart');
 t('سبد خالی: پیام خالی', await p.locator('#main .up-empty').count()===1);
 t('سبد خالی: نوار موبایل نمایش داده نمی‌شود', !(await p.locator('.m-cart-bar.show').count()));
 // add from product list
 await go('products');
 await p.locator('.p-add').first().click();
 let items=await ls(); t('افزودن از لیست → ۱ ردیف qty=1', items.length===1&&items[0].qty===1, JSON.stringify(items));
 await p.locator('.p-add').first().click();
 items=await ls(); t('افزودن دوباره همان وزن → qty=2 بدون ردیف جدید', items.length===1&&items[0].qty===2, JSON.stringify(items));
 // different weight, same product
 await p.locator('.p-weights').first().locator('.w-chip').first().click();
 await p.locator('.p-add').first().click();
 items=await ls(); t('وزن متفاوت همان محصول → ردیف جدا', items.length===2&&items[0].pid===items[1].pid&&items[0].w!==items[1].w, JSON.stringify(items));
 // cart page
 await go('cart');
 t('صفحه سبد: ۲ ردیف', await p.locator('#main .cart-item').count()===2);
 const price0=await num('#main .cart-item .ci-price');
 const sub0=await num('#main .totals .t-row:nth-child(1) b');
 const sum=(await p.locator('#main .cart-item .ci-price').allInnerTexts()).reduce((s,x)=>s+parseInt(fa(x).replace('تومان','')),0);
 t('جمع کالاها = مجموع ردیف‌ها', sub0.startsWith(String(sum)), sub0+' vs '+sum);
 // qty +/-
 const before=(await ls())[0].qty;
 await p.locator('#main .cart-item').first().locator('.ci-qty button').nth(1).click();
 t('دکمه + افزایش می‌دهد', (await ls())[0].qty===before+1);
 await p.locator('#main .cart-item').first().locator('.ci-qty button').nth(0).click();
 t('دکمه − کاهش می‌دهد', (await ls())[0].qty===before);
 // cap at 20
 for(let i=0;i<25;i++) await p.locator('#main .cart-item').first().locator('.ci-qty button').nth(1).click();
 t('سقف تعداد ۲۰', (await ls())[0].qty===20, String((await ls())[0].qty));
 // minus to zero removes line
 await go('cart');
 await p.evaluate(()=>localStorage.setItem('asalat_cart',JSON.stringify([{pid:1,w:500,qty:1}]))); await go('cart');
 await p.locator('#main .cart-item .ci-qty button').nth(0).click();
 t('کاهش از ۱ → ردیف حذف و سبد خالی', (await ls()).length===0 && await p.locator('#main .up-empty').count()===1);
 // delete button
 await p.evaluate(()=>localStorage.setItem('asalat_cart',JSON.stringify([{pid:1,w:500,qty:3},{pid:2,w:250,qty:1}]))); await go('cart');
 await p.locator('#main .cart-item .ci-del').first().click();
 t('دکمه حذف فقط همان ردیف را برمی‌دارد', (await ls()).length===1 && (await ls())[0].pid===2);
 // persistence across reload
 await p.reload({waitUntil:'networkidle'});
 t('سبد بعد از رفرش حفظ می‌شود', (await ls()).length===1 && await p.locator('#main .cart-item').count()===1);
 // totals / shipping: small cart
 let tot=await p.locator('#main .totals').innerText();
 t('سبد کوچک: هزینه ارسال ۸۹٬۰۰۰ اعمال می‌شود', /۸۹٬۰۰۰/.test(tot), tot);
 // coupons
 const subv=parseInt((await num('#main .totals .t-row:nth-child(1) b')).replace('تومان',''));
 console.log('  (جمع فعلی',subv,')');
 const apply=async(c)=>{await p.fill('#main .coupon-row input',c);await p.click('#main .coupon-row button');await p.waitForTimeout(200);};
 await apply('INVALID');
 t('کد نامعتبر: تخفیف صفر', /۰ تومان/.test(await p.locator('#main .t-row').nth(1).innerText()));
 await apply('luck5');
 let off=parseInt(fa(await p.locator('#main .t-row').nth(1).innerText()).replace(/\D/g,''));
 t('LUCK5 (حروف کوچک) ۵٪ تخفیف', Math.abs(off-Math.round(subv*0.05))<=1, off+' vs '+Math.round(subv*.05));
 await apply('SHIP0');
 t('SHIP0 ارسال را رایگان می‌کند', /رایگان/.test(await p.locator('#main .t-row').nth(2).innerText()));
 await apply('CASH50');
 if(subv<300000) t('CASH50 زیر حداقل رد می‌شود', !/۵۰٬۰۰۰/.test(await p.locator('#main .t-row').nth(1).innerText()));
 // grand total consistency
 tot=await p.locator('#main .totals').innerText();
 const g=parseInt(fa(await p.locator('#main .grand b').innerText()).replace(/\D/g,''));
 const o=parseInt(fa(await p.locator('#main .t-row').nth(1).innerText()).replace(/\D/g,''));
 const sp=/رایگان/.test(await p.locator('#main .t-row').nth(2).innerText())?0:89000;
 t('مبلغ قابل پرداخت = جمع − تخفیف + ارسال', g===subv-o+sp, `${g} vs ${subv-o+sp}`);
 // free shipping threshold + progress in drawer
 await p.evaluate(()=>localStorage.setItem('asalat_cart',JSON.stringify([{pid:1,w:1000,qty:20}]))); await go('cart');
 const big=parseInt(fa(await p.locator('#main .t-row').nth(0).innerText()).replace(/\D/g,''));
 console.log('  (سبد بزرگ',big,')');
 if(big>=1500000) t('بالای ۱٫۵م: ارسال رایگان', /رایگان/.test(await p.locator('#main .t-row').nth(2).innerText()));
 // drawer
 await go('');
 await p.evaluate(()=>localStorage.setItem('asalat_cart',JSON.stringify([{pid:1,w:500,qty:1}]))); await p.reload({waitUntil:'networkidle'});
 t('نوار موبایل/شناور شمارنده قابل مشاهده در DOM', await p.locator('.m-cart-bar').count()===1);
 await p.locator('[aria-label*="سبد"]:visible').first().click().catch(()=>{});
 await p.waitForTimeout(400);
 t('کشوی سبد باز می‌شود', await p.locator('.cart-drawer.open').count()===1);
 if(await p.locator('.cart-drawer.open').count()){
  t('کشو: ردیف و دکمه تکمیل خرید فعال', await p.locator('.cart-drawer .cart-item').count()===1 && !(await p.locator('.cd-foot .btn-lg').isDisabled()));
  await p.locator('.cd-foot .btn-lg').click(); await p.waitForTimeout(400);
  t('تکمیل خرید → /checkout', p.url().includes('checkout'), p.url());
 }
 // corrupt/stale data
 await p.evaluate(()=>localStorage.setItem('asalat_cart',JSON.stringify([{pid:99999,w:500,qty:2},{pid:1,w:500,qty:1}])));
 const e0=errs.length; await go('cart');
 t('محصول ناموجود در localStorage: بدون خطای JS', errs.length===e0, errs.slice(e0).join(';'));
 t('محصول ناموجود: ردیف خراب نمایش داده نمی‌شود', await p.locator('#main .cart-item').count()===1, 'rows='+await p.locator('#main .cart-item').count());
 await p.evaluate(()=>localStorage.setItem('asalat_cart','{bad json')); const e1=errs.length; await go('cart');
 t('JSON خراب در localStorage: بدون کرش', errs.length===e1 && await p.locator('#main .up-empty').count()===1);
 await p.evaluate(()=>localStorage.setItem('asalat_cart','"x"')); const e2=errs.length; await go('cart');
 t('مقدار غیرآرایه: بدون کرش', errs.length===e2, errs.slice(e2).join(';'));
 // checkout with empty cart
 await p.evaluate(()=>localStorage.removeItem('asalat_cart')); await go('checkout');
 console.log('  (checkout خالی →', p.url().replace(U,''), ')');
 console.log(`\nنتیجه: ${ok} موفق، ${bad} ناموفق | خطاهای JS: ${[...new Set(errs)].join(' ; ')||'ندارد'}`);
 await b.close();
})();
