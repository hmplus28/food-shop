/* ---------- مسیریابی فروشگاه ---------- */
import { createRouter, createWebHistory } from 'vue-router';
import { auth } from '../stores/auth';

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue'), meta: { title: null } },
  { path: '/products', name: 'products', component: () => import('../views/ProductsView.vue'), meta: { title: 'فروشگاه' } },
  { path: '/product/:id', name: 'product', component: () => import('../views/ProductView.vue'), meta: { title: 'محصول' } },
  { path: '/cart', name: 'cart', component: () => import('../views/CartView.vue'), meta: { title: 'سبد خرید' } },
  { path: '/checkout', name: 'checkout', component: () => import('../views/CheckoutView.vue'), meta: { title: 'تکمیل خرید' } },
  { path: '/track', name: 'track', component: () => import('../views/TrackView.vue'), meta: { title: 'پیگیری سفارش' } },
  { path: '/auth', name: 'auth', component: () => import('../views/AuthView.vue'), meta: { title: 'ورود | ثبت‌نام' } },
  { path: '/account', name: 'account', component: () => import('../views/AccountView.vue'), meta: { title: 'پنل کاربری', requiresUser: true } },
  { path: '/admin', name: 'admin', component: () => import('../views/AdminView.vue'), meta: { title: 'پنل مدیریت' } },
  { path: '/:pathMatch(.*)*', name: 'notfound', component: () => import('../views/NotFoundView.vue'), meta: { title: 'صفحه پیدا نشد' } },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, saved) {
    if (saved) return saved;
    if (to.hash) return { el: to.hash, behavior: 'smooth', top: 130 };
    return { top: 0 };
  },
});

router.beforeEach(to => {
  if (to.meta.requiresUser && !auth.user) return { path: '/auth', query: { redirect: to.fullPath } };
  return true;
});

export default router;
