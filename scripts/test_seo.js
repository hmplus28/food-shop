// تست سئو (Playwright): پیش‌رندر بدون JS، canonical، noindex، JSON-LD. پیش‌نیاز: cd app && npm run build && npx vite preview --port 4173
// اجرا: node scripts/test_seo.js
const { chromium } = require('playwright');
const U='http://localhost:4173/food-shop/';
(async()=>{
 const b=await chromium.launch(); let bad=0; const t=(n,c,d='')=>{if(!c)bad++;console.log((c?'✓ ':'✗ ')+n+(c?'':' → '+d));};
 // no-JS view
 const nj=await b.newContext({javaScriptEnabled:false}); const q=await nj.newPage();
 for (const r of ['','products/','product/1/','track/']) {
  const resp=await q.goto(U+r); const h1=await q.locator('h1').first().innerText().catch(()=>'');
  t(`بدون JS /${r}: کد ${resp.status()} و h1`, resp.status()===200 && h1.length>3, h1);
 }
 const metas=await (async()=>{await q.goto(U+'product/1/');return q.evaluate(()=>({canon:document.querySelector('link[rel=canonical]')?.href,price:document.querySelector('meta[property="product:price:amount"]')?.content,av:document.querySelector('meta[property="product:availability"]')?.content,ld:[...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(s=>[].concat(JSON.parse(s.textContent)).map(o=>o['@type']))}))})();
 console.log('  ',JSON.stringify(metas));
 t('صفحه محصول: Product+Breadcrumb JSON-LD، قیمت و موجودی', metas.ld.includes('Product')&&metas.ld.includes('BreadcrumbList')&&+metas.price>0&&metas.av==='instock');
 // JS view
 const c=await b.newContext({viewport:{width:1280,height:900}}); await c.addInitScript(()=>{try{sessionStorage.setItem('asalat_lucky_seen','1')}catch(e){}});
 const p=await c.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(e.message));
 for (const r of ['product/1/','product/1','products/','cart','nope']) {
  await p.goto(U+r,{waitUntil:'networkidle'}); await p.waitForTimeout(300);
  const d=await p.evaluate(()=>({canon:document.querySelector('link[rel=canonical]')?.href,rob:document.querySelector('meta[name=robots]')?.content,h1:document.querySelector('#main h1, h1')?.innerText, n:document.querySelectorAll('link[rel=canonical]').length, jl:document.querySelectorAll('#seo-jsonld').length}));
  console.log('  ',r,JSON.stringify(d));
  t(`با JS ${r}: یک canonical و h1`, d.n===1 && !!d.h1);
 }
 await p.goto(U+'cart',{waitUntil:'networkidle'}); t('سبد noindex', (await p.evaluate(()=>document.querySelector('meta[name=robots]').content)).includes('noindex'));
 await p.goto(U+'product/1/',{waitUntil:'networkidle'}); t('محصول: canonical با کنونیکال پیش‌رندر برابر', (await p.evaluate(()=>document.querySelector('link[rel=canonical]').href))===metas.canon);
 t('بدون خطای JS', errs.length===0, errs.join(';'));
 await b.close(); process.exit(bad?1:0);
})();
