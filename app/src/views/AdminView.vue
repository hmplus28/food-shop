<template>
  <div class="section">
    <div class="container">
      <!-- ورود مدیر -->
      <div v-if="!auth.isAdmin" class="admin-login">
        <div class="auth-card">
          <h1 style="font-size:1.1rem;display:flex;align-items:center;gap:8px"><svg class="icon"><use href="#i-lock" /></svg> ورود مدیر فروشگاه</h1>
          <p style="font-size:.8rem;color:var(--ink-3);margin:6px 0 16px">این بخش برای مدیریت محصولات و سفارش‌هاست. (نسخه نمایشی: admin / admin1234)</p>
          <form class="auth-form" @submit.prevent="doAdmin">
            <div class="fld w"><label>نام کاربری</label><input v-model="au" type="text" autocomplete="username"></div>
            <div class="fld w"><label>رمز عبور</label><input v-model="ap" type="password" autocomplete="current-password"></div>
            <button class="btn btn-brand btn-block" type="submit">ورود به پنل مدیریت</button>
          </form>
        </div>
      </div>

      <!-- پنل مدیریت -->
      <template v-else>
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-box" /></svg></span>
            <div><h1 class="sec-title">پنل <i>مدیریت</i> خانم گل</h1><span class="sec-sub">مدیریت محصولات، سفارش‌ها و وضعیت ارسال</span></div></span>
          <div class="sec-actions"><button class="btn btn-light btn-sm" @click="adminLogout(); toast('از پنل مدیر خارج شدید', 'ok')"><svg class="icon"><use href="#i-x" /></svg> خروج</button></div>
        </div>

        <div class="admin-stats">
          <div class="up-stat"><b>{{ toFa(products.length) }}</b><span>محصول</span></div>
          <div class="up-stat"><b>{{ toFa(orders.length) }}</b><span>سفارش</span></div>
          <div class="up-stat"><b>{{ money(spentTotal()) }}</b><span>فروش کل (تومان)</span></div>
          <div class="up-stat"><b>{{ toFa(lowStock) }}</b><span>موجودی کم (&lt;۱۰)</span></div>
        </div>

        <div class="admin-tabs">
          <button :class="{ on: tab === 'products' }" @click="tab = 'products'">مدیریت محصولات</button>
          <button :class="{ on: tab === 'orders' }" @click="tab = 'orders'">مدیریت سفارش‌ها</button>
        </div>

        <!-- محصولات -->
        <div v-if="tab === 'products'" class="admin-card">
          <div class="admin-toolbar">
            <button class="btn btn-gold btn-sm" @click="startNew"><svg class="icon"><use href="#i-plus" /></svg> افزودن محصول</button>
            <button class="btn btn-light btn-sm" @click="resetAll">بازگردانی محصولات پیش‌فرض</button>
          </div>
          <div class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>محصول</th><th>دسته</th><th>قیمت پایه (کیلو)</th><th>تخفیف</th><th>موجودی</th><th></th></tr></thead>
              <tbody>
                <tr v-for="p in products" :key="p.id">
                  <td class="td-p"><img :src="p.img" alt=""><div><b>{{ p.name }}</b><small>{{ p.grade }}</small></div></td>
                  <td>{{ catOf(p.cat)?.name || '—' }}</td>
                  <td>{{ money(p.price) }}</td>
                  <td>{{ p.disc ? '٪' + toFa(p.disc) : '—' }}</td>
                  <td><span class="tag" :class="p.stock >= 10 ? 'green' : 'red'">{{ toFa(p.stock) }}</span></td>
                  <td class="td-acts">
                    <button class="btn btn-light btn-sm" @click="startEdit(p)">ویرایش</button>
                    <button class="btn btn-light btn-sm del" @click="del(p)">حذف</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- سفارش‌ها -->
        <div v-else class="admin-card">
          <div v-if="!orders.length" class="up-empty"><svg class="icon"><use href="#i-doc" /></svg><p>هنوز سفارشی ثبت نشده است. بعد از ثبت سفارش از سمت مشتری‌ها این‌جا نمایش داده می‌شود.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>کد</th><th>تاریخ</th><th>اقلام</th><th>مبلغ</th><th>مشتری</th><th>وضعیت</th></tr></thead>
              <tbody>
                <tr v-for="o in orders" :key="o.code">
                  <td><b>{{ o.code }}</b></td>
                  <td>{{ faDate(o.ts) }}</td>
                  <td class="td-items">{{ o.items.map(c => `${prod(c.pid)?.name || '?'} (${weightLabel(c.w)}×${toFa(c.qty)})`).join(' + ') }}</td>
                  <td>{{ money(o.total) }}</td>
                  <td>{{ toFa(o.addr.phone) }}</td>
                  <td>
                    <select class="fld" style="padding:5px 8px;font-size:.78rem" :value="String(orderStep(o))" @change="setStatus(o.code, Number($event.target.value))">
                      <option v-for="(s, i) in STATUS" :key="i" :value="String(i)">{{ s }}</option>
                    </select>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>

  <!-- مودال ویرایش/افزودن محصول -->
  <div class="overlay" :class="{ open: editing }" @click.self="editing = null">
    <div class="modal" style="width:min(620px,100%)">
      <div class="modal-head"><b><svg class="icon"><use href="#i-nut" /></svg> {{ editing && editing.id ? 'ویرایش محصول' : 'افزودن محصول' }}</b><button class="modal-x" aria-label="بستن" @click="editing = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="editing">
        <div class="f-grid c2">
          <div class="fld w" style="grid-column:1/-1"><label>نام محصول *</label><input v-model="editing.name" type="text"></div>
          <div class="fld w"><label>دسته‌بندی</label>
            <select v-model="editing.cat"><option v-for="c in CATS" :key="c.id" :value="c.id">{{ c.name }}</option></select>
          </div>
          <div class="fld w"><label>درجه</label><input v-model="editing.grade" type="text"></div>
          <div class="fld w"><label>قیمت پایه هر کیلو (تومان) *</label><input v-model.number="editing.price" type="number" min="0" step="10000"></div>
          <div class="fld w"><label>تخفیف (٪)</label><input v-model.number="editing.disc" type="number" min="0" max="90"></div>
          <div class="fld w"><label>موجودی</label><input v-model.number="editing.stock" type="number" min="0"></div>
          <div class="fld w"><label>امتیاز (۰ تا ۵)</label><input v-model.number="editing.rate" type="number" min="0" max="5" step="0.1"></div>
          <div class="fld w" style="grid-column:1/-1"><label>توضیحات</label><textarea v-model="editing.desc" rows="2"></textarea></div>
          <div class="fld w" style="grid-column:1/-1"><label>آدرس تصویر</label><input v-model="editing.img" type="url" dir="ltr"></div>
        </div>
        <button class="btn btn-brand btn-block" style="margin-top:12px" @click="save"><svg class="icon"><use href="#i-check" /></svg> ذخیره محصول</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { toFa, money, weightLabel, faDate } from '../data/site';
import { products, CATS, catOf, prod, persistProducts, resetProducts, nextProductId } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import { auth, adminLogin, adminLogout } from '../stores/auth';
import { orders, setStatus, orderStep, STATUS, spentTotal } from '../stores/orders';
import { toast } from '../stores/ui';

useSeo({ title: 'پنل مدیریت', description: 'پنل مدیریت فروشگاه خانم گل', path: '/admin' });

const tab = ref('products');
const au = ref(''), ap = ref('');
const editing = ref(null);
const lowStock = computed(() => products.filter(p => p.stock < 10).length);

function doAdmin() {
  const res = adminLogin(au.value, ap.value);
  if (!res.ok) return toast(res.msg, 'err');
  toast('به پنل مدیریت خوش آمدید 👑', 'gold');
}

function startNew() {
  editing.value = { id: 0, name: '', cat: 'ajil', img: 'https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/66fd0cba7ee8.jpg', price: 1000000, weights: [250, 500, 1000, 2000], stock: 20, disc: 0, grade: 'درجه یک', rate: 4.5, sold: 0, tags: [], sec: [], desc: '' };
}
function startEdit(p) { editing.value = { ...p, tags: [...p.tags], sec: [...p.sec], weights: [...p.weights] }; }
function save() {
  const e = editing.value;
  if (!e.name.trim()) return toast('نام محصول را وارد کنید', 'err');
  if (!e.price || e.price <= 0) return toast('قیمت پایه معتبر وارد کنید', 'err');
  if (!e.id) { e.id = nextProductId(); products.push(e); }
  else {
    const i = products.findIndex(p => p.id === e.id);
    if (i > -1) products.splice(i, 1, e);
  }
  persistProducts();
  editing.value = null;
  toast('محصول ذخیره شد ✅', 'ok');
}
function del(p) {
  if (p.id <= 28 || (p.id >= 90 && p.id <= 96)) return toast('محصولات پایه فقط قابل ویرایش‌اند؛ برای حذف، موجودی را صفر کنید', 'err', 4600);
  const i = products.findIndex(x => x.id === p.id);
  if (i > -1) products.splice(i, 1);
  persistProducts();
  toast('محصول حذف شد', 'ok');
}
function resetAll() {
  resetProducts();
  toast('محصولات پیش‌فرض بازگردانی شد', 'ok');
}
</script>

<style scoped>
.admin-login{max-width:460px;margin:0 auto}
.admin-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}
.admin-tabs{display:flex;gap:8px;margin-bottom:14px}
.admin-tabs button{padding:9px 18px;border-radius:12px;font-weight:700;font-size:.88rem;background:var(--bg-warm);color:var(--ink-2);border:1px solid var(--line)}
.admin-tabs button.on{background:var(--brand-050);color:var(--brand-700);border-color:var(--brand-100)}
.admin-card{background:#fff;border:1px solid var(--line);border-radius:var(--r-md);box-shadow:var(--sh-sm);padding:14px}
.admin-toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.tbl-wrap{overflow-x:auto}
.tbl{width:100%;border-collapse:collapse;font-size:.82rem;min-width:640px}
.tbl th{background:var(--bg-warm);padding:9px 10px;text-align:start;color:var(--ink-2);font-size:.76rem;white-space:nowrap}
.tbl td{padding:9px 10px;border-top:1px solid var(--line);vertical-align:middle}
.td-p{display:flex;align-items:center;gap:9px;min-width:200px}
.td-p img{width:38px;height:38px;border-radius:9px;object-fit:cover;flex:none}
.td-p small{display:block;color:var(--ink-3)}
.td-acts{white-space:nowrap}
.td-acts .del{color:var(--red);border-color:#f7cdc9}
.td-items{max-width:280px;font-size:.74rem;color:var(--ink-2)}
@media(max-width:767px){.admin-stats{grid-template-columns:repeat(2,1fr)}}
</style>
