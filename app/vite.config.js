import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// مسیر پایه برای GitHub Pages (ریپو: hmplus28/food-shop)
// اگر روی دامنه یا مسیر دیگری منتشر شد فقط همین مقدار را عوض کنید.
export default defineConfig(({ mode }) => {
  // VITE_API_ENABLED از متغیر شل یا فایل .env (loadEnv هر دو را می‌خواند)
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const apiOn = String(env.VITE_API_ENABLED || '').trim().toLowerCase() === 'true';
  return {
    base: process.env.VITE_BASE || '/food-shop/',
    plugins: [vue()],
    build: {
      outDir: 'dist',
      assetsInlineLimit: 0
    },
    define: {
      // کلید ایستا برای حذف کامل کاتالوگ نمونه (محصولات فیک) از باندلِ بیلد تولید؛
      // در بیلد دمو (GitHub Pages / تست‌های UI) true می‌ماند و کاتالوگ نمونه داخل باندل است.
      __KG_API_ON__: JSON.stringify(apiOn),
    },
  };
})
