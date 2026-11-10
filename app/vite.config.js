import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// مسیر پایه برای GitHub Pages (ریپو: hmplus28/food-shop)
// اگر روی دامنه یا مسیر دیگری منتشر شد فقط همین مقدار را عوض کنید.
export default defineConfig({
  base: process.env.VITE_BASE || '/food-shop/',
  plugins: [vue()],
  build: {
    outDir: 'dist',
    assetsInlineLimit: 0
  }
})
