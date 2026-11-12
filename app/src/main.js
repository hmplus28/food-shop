import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
/* فونت‌ها روی خود هاست (بدون Google Fonts) تا با اینترنت ملی/قطع اینترنت جهانی هم بالا بیایند */
import '@fontsource-variable/vazirmatn/wght.css';
import '@fontsource/lalezar/arabic-400.css';
import '@fontsource/lalezar/latin-400.css';
import '@fontsource/amiri/arabic-400.css';
import '@fontsource/amiri/latin-400.css';
import './assets/main.css';
import { IMG_CDN } from './services/api';

/* تصاویر از /img/ همین سایت می‌آیند؛ اگر فایلی هنوز دانلود نشده بود (scripts/fetch_assets.py)،
   یک‌بار به منبع اصلی برمی‌گردیم تا تصویر خراب نشان داده نشود. */
const LOCAL = (import.meta.env.BASE_URL || '/') + 'img/';
const REMOTE_ONLY = { 'dayna-logo.png': 'https://daynacode.ir/assets/dayna-logo.png' };
document.addEventListener('error', e => {
  const t = e.target;
  if (!t || t.tagName !== 'IMG' || t.dataset.fb) return;
  const src = t.getAttribute('src') || '';
  if (!src.startsWith(LOCAL) || src.length === LOCAL.length) return;
  const name = src.slice(LOCAL.length);
  t.dataset.fb = '1';
  t.src = REMOTE_ONLY[name] || (IMG_CDN + name);
}, true);

createApp(App).use(router).mount('#app');
