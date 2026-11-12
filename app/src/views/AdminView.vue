<template>
  <div class="section">
    <div class="container">
      <!-- ورود مدیر -->
      <div v-if="!auth.isAdmin" class="admin-login">
        <div class="auth-card">
          <h1 style="font-size:1.1rem;display:flex;align-items:center;gap:8px;margin-bottom:16px"><svg class="icon"><use href="#i-lock" /></svg> ورود مدیر فروشگاه</h1>
          <form class="auth-form" @submit.prevent="doAdmin">
            <div class="fld w"><label>نام کاربری یا موبایل</label><input v-model="au" type="text" autocomplete="username"></div>
            <div class="fld w"><label>رمز عبور</label><input v-model="ap" type="password" autocomplete="current-password"></div>
            <button class="btn btn-brand btn-block" type="submit" :disabled="loggingIn">{{ loggingIn ? 'در حال ورود…' : 'ورود به پنل مدیریت' }}</button>
          </form>
        </div>
      </div>

      <!-- پنل مدیریت -->
      <template v-else>
        <div class="sec-head">
          <span class="en"><span class="sec-ic"><svg class="icon"><use href="#i-box" /></svg></span>
            <div><h1 class="sec-title">پنل <i>مدیریت</i> خانم گل</h1><span class="sec-sub">محصولات، سفارش‌ها، مشتریان، پنل پیامک و ظاهر سایت</span></div></span>
          <div class="sec-actions"><button class="btn btn-light btn-sm" @click="adminLogout(); toast('از پنل مدیر خارج شدید', 'ok')"><svg class="icon"><use href="#i-x" /></svg> خروج</button></div>
        </div>

        <div class="admin-stats">
          <div class="up-stat"><b>{{ toFa(stats.products ?? plist.length) }}</b><span>محصول</span></div>
          <div class="up-stat"><b>{{ toFa(stats.orders ?? 0) }}</b><span>سفارش</span></div>
          <div class="up-stat"><b>{{ toFa(stats.users ?? 0) }}</b><span>مشتری</span></div>
          <div class="up-stat"><b>{{ money(stats.revenue ?? 0) }}</b><span>فروش کل (تومان)</span></div>
          <div class="up-stat"><b>{{ toFa(stats.lowStock ?? 0) }}</b><span>موجودی کم (&lt;۱۰)</span></div>
        </div>

        <div class="admin-tabs">
          <button :class="{ on: tab === 'dash' }" @click="tab = 'dash'">داشبورد</button>
          <button :class="{ on: tab === 'products' }" @click="tab = 'products'">محصولات</button>
          <button :class="{ on: tab === 'orders' }" @click="tab = 'orders'">سفارش‌ها</button>
          <button :class="{ on: tab === 'coupons' }" @click="tab = 'coupons'">کدهای تخفیف</button>
          <button :class="{ on: tab === 'lucky' }" @click="tab = 'lucky'">کارت شانس</button>
          <button :class="{ on: tab === 'shipping' }" @click="tab = 'shipping'">هزینه ارسال</button>
          <button :class="{ on: tab === 'home' }" @click="tab = 'home'">صفحهٔ اصلی</button>
          <button :class="{ on: tab === 'media' }" @click="tab = 'media'">تصاویر</button>
          <button :class="{ on: tab === 'content' }" @click="tab = 'content'">محتوا و صفحات</button>
          <button :class="{ on: tab === 'consults' }" @click="tab = 'consults'">مشاوره‌ها<span v-if="stats.consults" class="badge-hide" style="background:var(--red);color:#fff;border-color:var(--red)">{{ toFa(stats.consults) }}</span></button>
          <button :class="{ on: tab === 'users' }" @click="tab = 'users'">کاربران</button>
          <button :class="{ on: tab === 'sms' }" @click="tab = 'sms'">پنل پیامک</button>
          <button :class="{ on: tab === 'look' }" @click="tab = 'look'">ظاهر سایت</button>
        </div>

        <!-- داشبورد -->
        <div v-if="tab === 'dash'" class="dash">
          <div class="admin-card">
            <h3 class="dh">فروش ۷ روز اخیر</h3>
            <div class="bars" role="img" aria-label="نمودار فروش ۷ روز اخیر">
              <div v-for="d in (stats.daily || [])" :key="d.date" class="bar-col" :title="`${faDate(Date.parse(d.date))}: ${d.orders} سفارش، ${money(d.revenue)} تومان`">
                <small>{{ d.revenue ? shortMoney(d.revenue) : '' }}</small>
                <div class="bar"><i :style="{ height: barH(d.revenue) + '%' }"></i></div>
                <span>{{ weekday(d.date) }}</span>
              </div>
            </div>
          </div>
          <div class="dash-grid">
            <div class="admin-card">
              <h3 class="dh">وضعیت سفارش‌ها</h3>
              <div v-for="(label, i) in STATUS" :key="i" class="dl"><span>{{ label }}</span><b>{{ toFa((stats.byStatus || {})[String(i)] || 0) }}</b></div>
            </div>
            <div class="admin-card">
              <h3 class="dh">پرفروش‌ترین‌ها</h3>
              <div v-if="!(stats.top || []).length" class="dl"><span>هنوز فروشی ثبت نشده است.</span></div>
              <div v-for="t in (stats.top || [])" :key="t.pid" class="dl"><span>{{ t.name }}</span><b>{{ toFa(t.qty) }} عدد</b></div>
            </div>
            <div class="admin-card">
              <h3 class="dh">موجودی کم</h3>
              <div v-if="!(stats.lowStockItems || []).length" class="dl"><span>همهٔ محصولات موجودی کافی دارند ✅</span></div>
              <div v-for="p in (stats.lowStockItems || [])" :key="p.id" class="dl"><a href="#" @click.prevent="editById(p.id)">{{ p.name }}</a><b class="red">{{ toFa(p.stock) }}</b></div>
            </div>
          </div>
          <div class="admin-card">
            <h3 class="dh">آخرین سفارش‌ها</h3>
            <div v-if="!olist.length" class="dl"><span>سفارشی ثبت نشده است.</span></div>
            <div v-for="o in olist.slice(0, 5)" :key="o.code" class="dl">
              <a href="#" @click.prevent="detail = o"><b>{{ o.code }}</b> — {{ o.addr.name }}</a>
              <span>{{ money(o.total) }} تومان · {{ STATUS[o.status] }}</span>
            </div>
          </div>
        </div>

        <AdminLucky v-else-if="tab === 'lucky'" />
        <AdminShipping v-else-if="tab === 'shipping'" />
        <AdminHome v-else-if="tab === 'home'" />
        <AdminMedia v-else-if="tab === 'media'" />
        <AdminContent v-else-if="tab === 'content'" />
        <AdminConsults v-else-if="tab === 'consults'" />

        <!-- کدهای تخفیف -->
        <div v-else-if="tab === 'coupons'" class="admin-card">
          <div class="admin-toolbar">
            <button class="btn btn-gold btn-sm" @click="newCoupon"><svg class="icon"><use href="#i-plus" /></svg> کد تخفیف جدید</button>
            <button class="btn btn-light btn-sm" @click="bulk = { cat: '', pct: 10 }">تخفیف گروهی روی محصولات</button>
            <button class="btn btn-light btn-sm" @click="loadCoupons">به‌روزرسانی ⟳</button>
          </div>
          <div v-if="!clist.length" class="up-empty"><svg class="icon"><use href="#i-percent" /></svg><p>کد تخفیفی وجود ندارد.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>کد</th><th>نوع</th><th>حداقل خرید</th><th>استفاده</th><th>انقضا</th><th>وضعیت</th><th></th></tr></thead>
              <tbody>
                <tr v-for="c in clist" :key="c.id">
                  <td><b dir="ltr">{{ c.code }}</b><small style="display:block;color:var(--ink-3)">{{ c.label }}</small></td>
                  <td>{{ couponKind(c) }}<span v-if="c.first" class="badge-hide">اولین خرید</span></td>
                  <td>{{ c.min ? money(c.min) : '—' }}</td>
                  <td>{{ toFa(c.used) }} / {{ c.maxUses ? toFa(c.maxUses) : '∞' }}</td>
                  <td>{{ c.expiresAt ? faDate(Date.parse(c.expiresAt)) : '—' }}</td>
                  <td><span class="tag" :class="c.status === 'قابل استفاده' ? 'green' : 'red'">{{ c.status }}</span></td>
                  <td class="td-acts">
                    <button class="btn btn-light btn-sm" @click="editCoupon(c)">ویرایش</button>
                    <button class="btn btn-light btn-sm" @click="toggleCoupon(c)">{{ c.active ? 'غیرفعال' : 'فعال' }}</button>
                    <button class="btn btn-light btn-sm del" @click="delCoupon(c)">حذف</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- محصولات -->
        <div v-else-if="tab === 'products'" class="admin-card">
          <div class="admin-toolbar">
            <button class="btn btn-gold btn-sm" @click="startNew"><svg class="icon"><use href="#i-plus" /></svg> افزودن محصول</button>
            <button class="btn btn-light btn-sm" @click="bulk = { cat: '', pct: 10 }">تخفیف گروهی</button>
            <input v-model="pq" class="fld" type="search" placeholder="جستجوی محصول…" style="max-width:220px">
            <button class="btn btn-light btn-sm" @click="loadProducts">به‌روزرسانی ⟳</button>
          </div>
          <div v-if="!shownProducts.length" class="up-empty"><svg class="icon"><use href="#i-box" /></svg><p>محصولی پیدا نشد.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>محصول</th><th>دسته</th><th>قیمت پایه (کیلو)</th><th>تخفیف</th><th>موجودی</th><th></th></tr></thead>
              <tbody>
                <tr v-for="p in shownProducts" :key="p.id">
                  <td class="td-p"><img :src="p.img" alt=""><div><b>{{ p.name }}</b><span v-if="p.hide" class="badge-hide">پنهان</span><small>{{ p.grade }}</small></div></td>
                  <td>{{ catOf(p.cat)?.name || '—' }}</td>
                  <td>{{ money(p.price) }}</td>
                  <td>{{ p.disc ? '٪' + toFa(p.disc) : '—' }}</td>
                  <td><span class="tag" :class="p.stock >= 10 ? 'green' : 'red'">{{ toFa(p.stock) }}</span></td>
                  <td class="td-acts">
                    <button class="btn btn-light btn-sm" @click="startEdit(p)">ویرایش</button>
                    <button class="btn btn-light btn-sm" @click="toggleHide(p)">{{ p.hide ? 'نمایش' : 'پنهان' }}</button>
                    <button class="btn btn-light btn-sm del" @click="del(p)">حذف</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- سفارش‌ها -->
        <div v-else-if="tab === 'orders'" class="admin-card">
          <div class="admin-toolbar">
            <select v-model="ostatus" class="fld" style="max-width:170px" @change="loadOrders">
              <option value="">همهٔ وضعیت‌ها</option>
              <option v-for="(s, i) in STATUS" :key="i" :value="String(i)">{{ s }}</option>
            </select>
            <input v-model="oq" class="fld" type="search" placeholder="کد سفارش یا موبایل…" style="max-width:220px" @keydown.enter="loadOrders">
            <button class="btn btn-light btn-sm" @click="loadOrders">جست‌وجو / به‌روزرسانی ⟳</button>
            <button class="btn btn-light btn-sm" :disabled="!olist.length" @click="exportOrders">خروجی CSV</button>
          </div>
          <div v-if="!olist.length" class="up-empty"><svg class="icon"><use href="#i-doc" /></svg><p>سفارشی پیدا نشد.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>کد</th><th>تاریخ</th><th>اقلام</th><th>مبلغ</th><th>مشتری</th><th>وضعیت</th><th></th></tr></thead>
              <tbody>
                <tr v-for="o in olist" :key="o.code">
                  <td><b>{{ o.code }}</b></td>
                  <td>{{ faDate(o.ts) }}</td>
                  <td class="td-items">{{ o.items.map(c => `${c.pname || '?'} (${weightLabel(c.w)}×${toFa(c.qty)})`).join(' + ') }}</td>
                  <td>{{ money(o.total) }}</td>
                  <td>{{ o.addr.name }}<small style="display:block;color:var(--ink-3)">{{ toFa(o.addr.phone) }}</small></td>
                  <td>
                    <select class="fld" style="padding:5px 8px;font-size:.78rem" :value="String(o.status)" @change="changeStatus(o, Number($event.target.value))">
                      <option v-for="(s, i) in STATUS" :key="i" :value="String(i)">{{ s }}</option>
                    </select>
                  </td>
                  <td class="td-acts"><button class="btn btn-light btn-sm" @click="detail = o">جزئیات</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- مشتریان -->
        <div v-else-if="tab === 'users'" class="admin-card">
          <div class="admin-toolbar">
            <input v-model="uq" class="fld" type="search" placeholder="نام یا موبایل…" style="max-width:240px" @keydown.enter="loadUsers">
            <button class="btn btn-light btn-sm" @click="loadUsers">جست‌وجو / به‌روزرسانی ⟳</button>
            <span class="sync-chip on">{{ toFa(usersTotal) }} کاربر</span>
          </div>
          <div v-if="!ulist.length" class="up-empty"><svg class="icon"><use href="#i-user" /></svg><p>کاربری پیدا نشد.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>نام</th><th>موبایل</th><th>نقش</th><th>وضعیت</th><th>عضویت</th><th>سفارش‌ها</th><th>مجموع خرید</th><th></th></tr></thead>
              <tbody>
                <tr v-for="u in ulist" :key="u.id">
                  <td>{{ u.name }}</td>
                  <td dir="ltr" style="text-align:end">{{ toFa(u.phone) }}</td>
                  <td><span class="tag" :class="u.role === 'admin' ? 'red' : 'green'">{{ u.role === 'admin' ? 'مدیر' : 'مشتری' }}</span></td>
                  <td><span class="tag" :class="u.active ? 'green' : 'red'">{{ u.active ? 'فعال' : 'غیرفعال' }}</span></td>
                  <td>{{ faDate(Date.parse(u.joined)) }}</td>
                  <td>{{ toFa(u.orders) }}</td>
                  <td>{{ money(u.spent) }} تومان</td>
                  <td class="td-acts">
                    <template v-if="!isMe(u)">
                      <button class="btn btn-light btn-sm" @click="patchUser(u, { active: !u.active })">{{ u.active ? 'غیرفعال' : 'فعال' }}</button>
                      <button class="btn btn-light btn-sm" @click="patchUser(u, { role: u.role === 'admin' ? 'user' : 'admin' })">{{ u.role === 'admin' ? 'گرفتن مدیریت' : 'ارتقا به مدیر' }}</button>
                      <button class="btn btn-light btn-sm" @click="resetPass(u)">رمز جدید</button>
                    </template>
                    <span v-else class="badge-hide">شما</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ظاهر سایت -->
        <div v-else-if="tab === 'look'" class="admin-card">
          <SiteStudio inline />
        </div>

        <!-- پنل پیامک -->
        <div v-else class="admin-card">
          <div class="sms-head">
            <span class="sync-chip" :class="smsReady ? 'on' : 'off'">
              {{ smsReady ? `● سرویس پیامک: ${smsProviderLabel}` : '○ پنل پیامک متصل نیست (حالت توسعه)' }}
            </span>
            <button class="btn btn-light btn-sm" @click="loadSms">به‌روزرسانی ⟳</button>
          </div>

          <div class="sms-test">
            <input v-model="smsTestTo" class="fld" type="tel" inputmode="tel" placeholder="شماره برای پیامک آزمایشی (۰۹…)" dir="rtl" style="max-width:240px">
            <button class="btn btn-gold btn-sm" :disabled="smsSending" @click="sendTestSms">{{ smsSending ? 'در حال ارسال…' : 'ارسال پیامک تست' }}</button>
          </div>

          <div v-if="!smsRows.length" class="up-empty" style="margin-top:10px"><svg class="icon"><use href="#i-sms" /></svg><p>هنوز پیامکی ثبت نشده است.</p></div>
          <div v-else class="tbl-wrap">
            <table class="tbl">
              <thead><tr><th>زمان</th><th>گیرنده</th><th>نوع</th><th>وضعیت</th><th>متن</th></tr></thead>
              <tbody>
                <tr v-for="(s, i) in smsRows" :key="i">
                  <td style="white-space:nowrap">{{ toFa(faTime(s.ts)) }} — {{ faDate(s.ts) }}</td>
                  <td dir="ltr" style="text-align:end">{{ toFa(s.to) }}</td>
                  <td>{{ smsTagLabel(s.tag) }}</td>
                  <td><span class="tag" :class="s.ok ? 'green' : 'red'">{{ s.ok ? 'موفق' : 'ناموفق' }}</span></td>
                  <td class="td-items" style="max-width:340px">{{ s.text }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>

  <!-- ویرایش/ساخت کد تخفیف -->
  <div class="overlay" :class="{ open: !!cedit }" @click.self="cedit = null">
    <div class="modal" style="width:min(560px,100%)">
      <div class="modal-head"><b><svg class="icon"><use href="#i-percent" /></svg> {{ cedit && cedit.id ? 'ویرایش کد تخفیف' : 'کد تخفیف جدید' }}</b><button class="modal-x" aria-label="بستن" @click="cedit = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="cedit">
        <div class="f-grid c2">
          <div class="fld w"><label>کد (انگلیسی/عدد) *</label><input v-model="cedit.code" type="text" dir="ltr" maxlength="30" style="text-transform:uppercase"></div>
          <div class="fld w"><label>نوع</label>
            <select v-model="cedit.type"><option value="pct">درصدی</option><option value="cash">مبلغ ثابت (تومان)</option><option value="ship">ارسال رایگان</option><option value="day">ارسال همان روز</option></select>
          </div>
          <div v-if="cedit.type === 'pct' || cedit.type === 'cash'" class="fld w"><label>{{ cedit.type === 'pct' ? 'درصد تخفیف' : 'مبلغ تخفیف (تومان)' }}</label><input v-model.number="cedit.val" type="number" min="1"></div>
          <div class="fld w"><label>حداقل مبلغ سفارش (تومان)</label><input v-model.number="cedit.min" type="number" min="0" step="10000"></div>
          <div class="fld w"><label>سقف دفعات استفاده (۰ = نامحدود)</label><input v-model.number="cedit.maxUses" type="number" min="0"></div>
          <div class="fld w"><label>تاریخ انقضا (شمسی، اختیاری)</label><input v-model="cedit.expiresAt" type="text" dir="ltr" inputmode="numeric" placeholder="۱۴۰۵/۱۲/۲۹" maxlength="10"></div>
          <div class="fld w" style="grid-column:1/-1"><label>توضیح نمایشی</label><input v-model="cedit.label" type="text" maxlength="120" placeholder="مثلاً ۱۰٪ تخفیف یلدا"></div>
          <label class="chk"><input v-model="cedit.first" type="checkbox"> فقط اولین خرید</label>
          <label class="chk"><input v-model="cedit.active" type="checkbox"> فعال</label>
        </div>
        <button class="btn btn-brand btn-block" style="margin-top:12px" @click="saveCoupon"><svg class="icon"><use href="#i-check" /></svg> ذخیره کد تخفیف</button>
      </div>
    </div>
  </div>

  <!-- تخفیف گروهی روی محصولات -->
  <div class="overlay" :class="{ open: !!bulk }" @click.self="bulk = null">
    <div class="modal" style="width:min(460px,100%)">
      <div class="modal-head"><b><svg class="icon"><use href="#i-percent" /></svg> تخفیف گروهی محصولات</b><button class="modal-x" aria-label="بستن" @click="bulk = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="bulk">
        <div class="fld w"><label>دسته‌بندی</label>
          <select v-model="bulk.cat"><option value="">همهٔ محصولات</option><option v-for="c in CATS" :key="c.id" :value="c.id">{{ c.name }}</option></select>
        </div>
        <div class="fld w" style="margin-top:10px"><label>درصد تخفیف (۰ = حذف تخفیف، حداکثر ۹۰)</label><input v-model.number="bulk.pct" type="number" min="0" max="90"></div>
        <p style="font-size:.78rem;color:var(--ink-3);margin:10px 0">روی {{ toFa(bulkTargets.length) }} محصول اعمال می‌شود و تخفیف قبلی آن‌ها جایگزین می‌شود.</p>
        <button class="btn btn-brand btn-block" :disabled="bulkBusy || !bulkTargets.length" @click="applyBulk">{{ bulkBusy ? 'در حال اعمال…' : 'اعمال تخفیف' }}</button>
      </div>
    </div>
  </div>

  <!-- جزئیات سفارش -->
  <div class="overlay" :class="{ open: !!detail }" @click.self="detail = null">
    <div class="modal" style="width:min(620px,100%)">
      <div class="modal-head"><b><svg class="icon"><use href="#i-doc" /></svg> سفارش {{ detail && detail.code }}</b><button class="modal-x" aria-label="بستن" @click="detail = null"><svg class="icon"><use href="#i-x" /></svg></button></div>
      <div class="modal-body" v-if="detail">
        <div class="od-grid">
          <div><b>گیرنده:</b>{{ detail.addr.name }}</div>
          <div><b>موبایل:</b><span dir="ltr">{{ toFa(detail.addr.phone) }}</span></div>
          <div><b>استان / شهر:</b>{{ detail.addr.prov }} {{ detail.addr.city }}</div>
          <div><b>تاریخ:</b>{{ faDate(detail.ts) }} {{ toFa(faTime(detail.ts)) }}</div>
          <div style="grid-column:1/-1"><b>آدرس:</b>{{ detail.addr.addr }}</div>
          <div><b>ارسال:</b>{{ detail.shipLabel }} ({{ detail.shipDays }})</div>
          <div><b>کد تخفیف:</b>{{ detail.coupon || '—' }}</div>
          <div v-if="detail.note" style="grid-column:1/-1"><b>توضیح مشتری:</b>{{ detail.note }}</div>
        </div>
        <div class="ord-mgmt">
          <h4 class="ad-h" style="margin-bottom:8px">مدیریت وضعیت سفارش</h4>
          <div class="ad-grid">
            <div class="fld w"><label>وضعیت</label>
              <select v-model.number="ost.status" :disabled="detail.status === 4"><option v-for="(l, i) in STATUS" :key="i" :value="i">{{ l }}</option></select>
            </div>
            <div class="fld w"><label>کد رهگیری مرسوله</label><input v-model="ost.tracking" type="text" dir="ltr" maxlength="60" placeholder="مثلاً ۲۴۰۱۲۳۴۵۶۷۸۹"></div>
            <div class="fld w full"><label>توضیح برای مشتری (در پیامک و پیگیری دیده می‌شود، اختیاری)</label><input v-model="ost.note" type="text" maxlength="200" placeholder="مثلاً بسته به پست تحویل داده شد"></div>
          </div>
          <button class="btn btn-brand btn-sm" :disabled="ost.busy || (detail.status === 4)" @click="saveOrderStatus">{{ ost.busy ? 'در حال ثبت…' : 'ثبت وضعیت' }}</button>
          <span v-if="detail.status === 4" class="badge-hide">سفارش لغو شده و قابل تغییر نیست</span>
          <div v-if="detail.events && detail.events.length" class="ord-hist">
            <b>تاریخچه</b>
            <div v-for="(e, i) in detail.events" :key="i">{{ jDateTime(e.ts) }} — {{ e.label }}<template v-if="e.note">: {{ e.note }}</template></div>
          </div>
        </div>
        <div class="tbl-wrap">
          <table class="tbl" style="min-width:0">
            <thead><tr><th>کالا</th><th>وزن</th><th>تعداد</th><th>جمع</th></tr></thead>
            <tbody><tr v-for="(c, i) in detail.items" :key="i"><td>{{ c.pname }}</td><td>{{ weightLabel(c.w) }}</td><td>{{ toFa(c.qty) }}</td><td>{{ money(c.cost) }}</td></tr></tbody>
          </table>
        </div>
        <div class="od-grid" style="margin-top:12px">
          <div><b>جمع کالاها:</b>{{ money(detail.sub) }}</div>
          <div><b>تخفیف:</b>{{ money(detail.off) }}</div>
          <div><b>هزینه ارسال:</b>{{ money(detail.shipCost) }}</div>
          <div><b>قابل پرداخت:</b><strong>{{ money(detail.total) }} تومان</strong></div>
        </div>
      </div>
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
          <div class="fld w" style="grid-column:1/-1"><label>تصویر محصول</label><ImageField v-model="editing.img" /></div>
          <div class="fld w" style="grid-column:1/-1"><label>نمایش در بخش‌های صفحهٔ اصلی</label>
            <div class="sec-chk">
              <label class="chk"><input v-model="editing.sec" type="checkbox" value="best"> پرفروش‌ترین‌ها</label>
              <label class="chk"><input v-model="editing.sec" type="checkbox" value="amz"> پیشنهاد شگفت‌انگیز</label>
              <label class="chk"><input v-model="editing.sec" type="checkbox" value="new"> محصولات جدید</label>
            </div>
          </div>
          <div class="fld w" style="grid-column:1/-1"><label>برچسب‌ها (با ویرگول جدا کنید؛ مثلاً پرفروش، ممتاز)</label><input v-model="tagsText" type="text" maxlength="120"></div>
          <label class="chk" style="grid-column:1/-1"><input v-model="editing.hide" type="checkbox"> پنهان از فروشگاه (در سایت نمایش داده نشود)</label>
        </div>
        <button class="btn btn-brand btn-block" style="margin-top:12px" @click="save"><svg class="icon"><use href="#i-check" /></svg> ذخیره محصول</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { toFa, money, weightLabel, faDate, faTime, toEn } from '../data/site';
import { CATS, catOf, IMG } from '../data/catalog';
import { useSeo } from '../composables/useSeo';
import SiteStudio from '../components/SiteStudio.vue';
import AdminLucky from './admin/AdminLucky.vue';
import AdminShipping from './admin/AdminShipping.vue';
import AdminContent from './admin/AdminContent.vue';
import AdminHome from './admin/AdminHome.vue';
import AdminMedia from './admin/AdminMedia.vue';
import ImageField from '../components/ImageField.vue';
import { jDateTime } from '../data/jalali';
import AdminConsults from './admin/AdminConsults.vue';
import { jalaliInputToIso, isoToJalaliInput } from '../data/jalali';
import '../assets/admin.css';
import { auth, adminLogin, adminLogout } from '../stores/auth';
import { STATUS } from '../stores/orders';
import { toast } from '../stores/ui';
import { adminCall, apiCall, adminStatsApi, ordersListApi, patchOrderStatusApi, adminSmsLogApi, adminSmsTestApi, adminUsersApi,
  adminProductsApi, productCreateApi, productUpdateApi, productDeleteApi, syncCatalog } from '../services/api';
import { pruneCart } from '../stores/cart';
import { loadShop } from '../stores/shop';

useSeo({ title: 'پنل مدیریت', description: 'پنل مدیریت فروشگاه خانم گل', path: '/admin' });

const tab = ref('dash');
const au = ref(''), ap = ref('');
const loggingIn = ref(false);
const editing = ref(null);
const detail = ref(null);
const stats = ref({});

async function loadStats() { const s = await adminStatsApi(); if (s) stats.value = s; }

/* ---------- محصولات (همیشه از سرور؛ شامل پنهان‌ها) ---------- */
const plist = ref([]);
const pq = ref('');
const shownProducts = computed(() => {
  const q = pq.value.trim();
  return q ? plist.value.filter(p => (p.name + ' ' + (catOf(p.cat)?.name || '')).includes(q)) : plist.value;
});
async function loadProducts() {
  const l = await adminProductsApi();
  if (l) plist.value = l.filter(p => !(p.sec || []).includes('__virtual')); else toast('دریافت محصولات از سرور انجام نشد', 'err');
}
/* پس از هر تغییر، کاتالوگ عمومی و آمار هم تازه می‌شود */
async function afterChange() { await Promise.all([loadProducts(), loadStats(), Promise.all([loadShop(), syncCatalog()]).then(pruneCart)]); }

function startNew() {
  editing.value = { id: 0, name: '', cat: 'ajil', img: IMG + '66fd0cba7ee8.jpg', price: 1000000, weights: [250, 500, 1000, 2000], stock: 20, disc: 0, grade: 'درجه یک', rate: 4.5, sold: 0, tags: [], sec: [], desc: '', hide: false };
  tagsText.value = '';
}
const tagsText = ref('');
function startEdit(p) { editing.value = { ...p, tags: [...p.tags], sec: [...p.sec], weights: [...p.weights], hide: !!p.hide }; tagsText.value = p.tags.join('، '); }

async function save() {
  const e = editing.value;
  if (!e.name.trim()) return toast('نام محصول را وارد کنید', 'err');
  if (!e.price || e.price <= 0) return toast('قیمت پایه معتبر وارد کنید', 'err');
  if (e.disc < 0 || e.disc > 90) return toast('تخفیف باید بین ۰ تا ۹۰ باشد', 'err');
  e.tags = tagsText.value.split(/[،,]/).map(x => x.trim()).filter(Boolean).slice(0, 8);
  const res = e.id ? await productUpdateApi(e.id, e) : await productCreateApi(e);
  if (!res) return toast('ذخیرهٔ محصول روی سرور انجام نشد؛ دوباره وارد شوید یا اتصال را بررسی کنید', 'err');
  editing.value = null;
  toast('محصول ذخیره شد ✅', 'ok');
  afterChange();
}
async function toggleHide(p) {
  const res = await productUpdateApi(p.id, { ...p, hide: !p.hide });
  if (!res) return toast('تغییر انجام نشد', 'err');
  toast(p.hide ? 'محصول دوباره نمایش داده می‌شود' : 'محصول از فروشگاه پنهان شد', 'ok');
  afterChange();
}
async function del(p) {
  if (!window.confirm(`«${p.name}» برای همیشه حذف شود؟ (برای پنهان‌کردن موقت از دکمهٔ «پنهان» استفاده کنید)`)) return;
  if (!(await productDeleteApi(p.id))) return toast('حذف روی سرور انجام نشد', 'err');
  toast('محصول حذف شد', 'ok');
  afterChange();
}

/* ---------- سفارش‌ها ---------- */
const olist = ref([]);
const ostatus = ref('');
const oq = ref('');
function mapServerOrder(o) {
  return {
    code: o.code, ts: o.ts, status: o.status, sub: o.sub, off: o.off, coupon: o.coupon, note: o.note || '',
    shipCost: o.ship_cost, shipLabel: o.ship_label, shipDays: o.ship_days, total: o.total, tracking: o.tracking || '', events: o.events || [],
    items: (o.items || []).map(c => ({ pid: c.pid, w: c.w, qty: c.qty, pname: c.name, cost: c.cost })),
    addr: { name: '', phone: '', prov: '', city: '', addr: '', ...(o.addr || {}) },
  };
}
async function loadOrders() {
  const r = await ordersListApi({ limit: 200, status: ostatus.value, q: oq.value.trim() });
  if (r) olist.value = (r.results || []).map(mapServerOrder); else toast('دریافت سفارش‌ها از سرور انجام نشد', 'err');
}
/* ---- مدیریت وضعیت سفارش (وضعیت + کد رهگیری + توضیح؛ تاریخچه و پیامک) ---- */
const ost = reactive({ status: 0, note: '', tracking: '', busy: false });
watch(detail, d => { if (d) { ost.status = d.status; ost.note = ''; ost.tracking = d.tracking || ''; } });
async function saveOrderStatus() {
  const d = detail.value;
  if (ost.status === 4 && d.status !== 4 && !window.confirm('با لغو سفارش، موجودی کالاها برمی‌گردد و این کار قابل بازگشت نیست. ادامه می‌دهید؟')) return;
  ost.busy = true;
  const r = await apiCall('/orders/' + encodeURIComponent(d.code), { method: 'PATCH', body: { status: ost.status, note: ost.note, tracking: ost.tracking } });
  ost.busy = false;
  if (!r.ok) return toast(r.msg || 'ثبت وضعیت انجام نشد', 'err');
  toast(`وضعیت سفارش ${d.code} ثبت شد ✅`, 'ok');
  await loadOrders(); loadStats();
  detail.value = olist.value.find(x => x.code === d.code) || null;
}

async function changeStatus(o, st) {
  if (st === 4) { detail.value = o; ost.status = 4; return loadOrders(); }   // لغو فقط از پنجرهٔ مدیریت (با توضیح و تأیید)
  if (!(await patchOrderStatusApi(o.code, st))) { toast('تغییر وضعیت روی سرور انجام نشد', 'err'); return loadOrders(); }
  o.status = st;
  toast(`وضعیت سفارش ${o.code} به «${STATUS[st]}» تغییر کرد`, 'ok');
}

/* ---------- مشتریان ---------- */
const ulist = ref([]);
const uq = ref('');
const usersTotal = ref(0);
async function loadUsers() {
  const r = await adminUsersApi(uq.value.trim());
  if (r) { ulist.value = r.users || []; usersTotal.value = r.total || 0; } else toast('دریافت مشتریان از سرور انجام نشد', 'err');
}

/* ---------- ورود مدیر ---------- */
async function doAdmin() {
  loggingIn.value = true;
  const res = await adminLogin(au.value, ap.value);
  loggingIn.value = false;
  if (!res.ok) return toast(res.msg, 'err');
  toast('به پنل مدیریت خوش آمدید 👑', 'gold');
  loadAll();
}

/* ---------- پنل پیامک ---------- */
const smsRows = ref([]);
const smsMeta = ref(null);
const smsTestTo = ref('');
const smsSending = ref(false);
const smsReady = computed(() => !!(smsMeta.value && smsMeta.value.configured));
const smsProviderLabel = computed(() => ({
  console: 'حالت توسعه', kavenegar: 'کاوه‌نگار', smsir: 'SMS.ir', ghasedak: 'قاصدک', melipayamak: 'ملی پیامک',
}[smsMeta.value?.provider] || smsMeta.value?.provider || '—'));

const SMS_TAGS = { 'order-customer': 'تأیید سفارش', 'order-admin': 'اطلاع به مدیر', 'status-change': 'تغییر وضعیت', test: 'تست', send: 'ارسال' };
const smsTagLabel = t => SMS_TAGS[t] || t || '—';

async function loadSms() {
  const r = await adminSmsLogApi(50);
  if (!r) return;
  smsMeta.value = r.provider || null;
  smsRows.value = r.results || [];
}

async function sendTestSms() {
  const p = toEn(smsTestTo.value).replace(/\D/g, '');
  if (!/^09\d{9}$/.test(p)) return toast('شمارهٔ معتبر ۰۹… وارد کنید', 'err');
  smsSending.value = true;
  const r = await adminSmsTestApi(p);
  smsSending.value = false;
  if (!r) return toast('اتصال به سرور برقرار نشد', 'err');
  toast(r.ok && r.sent ? 'پیامک تست ارسال شد 📩' : 'ارسال پیامک ناموفق بود — تنظیمات پنل پیامک را بررسی کنید', r.ok && r.sent ? 'ok' : 'err');
  loadSms();
}

/* ---------- داشبورد ---------- */
const shortMoney = n => (n >= 1e6 ? toFa((n / 1e6).toFixed(1).replace(/\.0$/, '')) + 'م' : toFa(Math.round(n / 1e3)) + 'ه');
const barMax = computed(() => Math.max(1, ...(stats.value.daily || []).map(d => d.revenue)));
const barH = v => (v ? Math.max(6, Math.round(v / barMax.value * 100)) : 0);
const WD = ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه'];
const weekday = d => WD[new Date(d + 'T12:00:00').getDay()];
function editById(id) { const p = plist.value.find(x => x.id === id); if (p) { tab.value = 'products'; startEdit(p); } }

/* ---------- کدهای تخفیف ---------- */
const clist = ref([]);
const cedit = ref(null);
const couponKind = c => ({ pct: `${toFa(c.val)}٪ تخفیف`, cash: `${money(c.val)} تومان`, ship: 'ارسال رایگان', day: 'ارسال همان روز' }[c.type] || c.type);
async function loadCoupons() {
  const r = await adminCall('/admin/coupons');
  if (r.ok) clist.value = r.coupons || []; else toast(r.msg || 'دریافت کدها انجام نشد', 'err');
}
function newCoupon() { cedit.value = { id: 0, code: '', type: 'pct', val: 10, min: 0, maxUses: 0, expiresAt: '', label: '', first: false, active: true }; }
function editCoupon(c) { cedit.value = { id: c.id, code: c.code, type: c.type, val: c.val, min: c.min, maxUses: c.maxUses, expiresAt: c.expiresAt ? isoToJalaliInput(c.expiresAt) : '', label: c.label === c.code ? '' : c.label, first: c.first, active: c.active }; }
async function saveCoupon() {
  const c = cedit.value;
  const iso = jalaliInputToIso(c.expiresAt);
  if (iso === null) return toast('تاریخ انقضا را شمسی و به شکل ۱۴۰۵/۱۲/۲۹ وارد کنید', 'err');
  const body = { code: c.code, type: c.type, val: c.val, min: c.min || 0, maxUses: c.maxUses || 0, expiresAt: iso, label: c.label, first: c.first, active: c.active };
  const r = await adminCall(c.id ? '/admin/coupons/' + c.id : '/admin/coupons', { method: c.id ? 'PUT' : 'POST', body });
  if (!r.ok) return toast(r.msg || 'ذخیره نشد', 'err');
  cedit.value = null; toast('کد تخفیف ذخیره شد ✅', 'ok'); loadCoupons(); loadStats();
}
async function toggleCoupon(c) {
  const r = await adminCall('/admin/coupons/' + c.id, { method: 'PUT', body: { active: !c.active } });
  if (!r.ok) return toast(r.msg, 'err');
  toast(c.active ? 'کد غیرفعال شد' : 'کد فعال شد', 'ok'); loadCoupons();
}
async function delCoupon(c) {
  if (!window.confirm(`کد «${c.code}» حذف شود؟`)) return;
  const r = await adminCall('/admin/coupons/' + c.id, { method: 'DELETE' });
  if (!r.ok) return toast(r.msg, 'err');
  toast('کد حذف شد', 'ok'); loadCoupons();
}

/* ---------- تخفیف گروهی محصولات ---------- */
const bulk = ref(null);
const bulkBusy = ref(false);
const bulkTargets = computed(() => (bulk.value ? plist.value.filter(p => !bulk.value.cat || p.cat === bulk.value.cat) : []));
async function applyBulk() {
  const pct = Number(bulk.value.pct);
  if (!Number.isFinite(pct) || pct < 0 || pct > 90) return toast('درصد باید بین ۰ تا ۹۰ باشد', 'err');
  bulkBusy.value = true;
  let fail = 0;
  for (const p of bulkTargets.value) { if (!(await productUpdateApi(p.id, { ...p, disc: pct }))) fail++; }
  bulkBusy.value = false; bulk.value = null;
  toast(fail ? `${toFa(fail)} محصول به‌روز نشد` : 'تخفیف گروهی اعمال شد ✅', fail ? 'err' : 'ok');
  afterChange();
}

/* ---------- مدیریت کاربران ---------- */
const isMe = u => u.phone === auth.user?.phone;
async function patchUser(u, body) {
  const r = await adminCall('/admin/users/' + u.id, { method: 'PATCH', body });
  if (!r.ok) return toast(r.msg || 'انجام نشد', 'err');
  toast('تغییر ذخیره شد ✅', 'ok'); loadUsers(); loadStats();
}
function resetPass(u) {
  const pw = window.prompt(`رمز جدید برای ${u.name} (حداقل ۴ کاراکتر):`);
  if (pw) patchUser(u, { password: pw });
}

/* ---------- خروجی CSV سفارش‌ها ---------- */
function exportOrders() {
  const q = v => '"' + String(v ?? '').replace(/"/g, '""') + '"';
  const head = ['کد', 'تاریخ', 'نام', 'موبایل', 'استان', 'شهر', 'آدرس', 'اقلام', 'جمع کالاها', 'تخفیف', 'ارسال', 'قابل پرداخت', 'کد تخفیف', 'وضعیت'];
  const rows = olist.value.map(o => [o.code, faDate(o.ts), o.addr.name, o.addr.phone, o.addr.prov, o.addr.city, o.addr.addr,
    o.items.map(c => `${c.pname} (${c.w}×${c.qty})`).join(' + '), o.sub, o.off, o.shipCost, o.total, o.coupon, STATUS[o.status]]);
  const csv = '\ufeff' + [head, ...rows].map(r => r.map(q).join(',')).join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  a.download = 'orders-' + new Date().toISOString().slice(0, 10) + '.csv';
  a.click(); URL.revokeObjectURL(a.href);
}

function loadAll() { loadStats(); loadProducts(); loadOrders(); loadUsers(); loadSms(); loadCoupons(); }
onMounted(() => { if (auth.isAdmin) loadAll(); });
watch(() => auth.isAdmin, v => { if (v) loadAll(); });
</script>

<style scoped>
.admin-login{max-width:460px;margin:0 auto}
.admin-stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:16px 0}
.admin-tabs{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.admin-tabs button{padding:9px 18px;border-radius:12px;font-weight:700;font-size:.88rem;background:var(--bg-warm);color:var(--ink-2);border:1px solid var(--line)}
.admin-tabs button.on{background:var(--brand-050);color:var(--brand-700);border-color:var(--brand-100)}
.admin-card{background:#fff;border:1px solid var(--line);border-radius:var(--r-md);box-shadow:var(--sh-sm);padding:14px}
.admin-toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
.sync-chip{font-size:.72rem;padding:6px 12px;border-radius:999px;font-weight:700}
.sync-chip.on{background:var(--brand-050);color:var(--brand-700);border:1px solid var(--brand-100)}
.sync-chip.off{background:var(--bg-warm);color:var(--ink-3);border:1px solid var(--line)}
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
.sms-head{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap}
.dash{display:grid;gap:14px}
.dash-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.dh{font-size:.92rem;margin-bottom:10px;color:var(--ink)}
.dl{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px dashed var(--line);font-size:.82rem;color:var(--ink-2)}
.dl:first-of-type{border-top:0}
.dl b.red{color:var(--red)}
.bars{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;align-items:end;height:190px}
.bar-col{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;gap:4px}
.bar-col small{font-size:.66rem;color:var(--ink-3);min-height:14px}
.bar{width:100%;max-width:46px;height:120px;display:flex;align-items:flex-end;background:var(--bg-warm);border-radius:9px;overflow:hidden}
.bar i{display:block;width:100%;background:linear-gradient(180deg,var(--brand),var(--brand-700));border-radius:9px 9px 0 0;transition:height .4s ease}
.bar-col span{font-size:.7rem;color:var(--ink-2)}
@media(max-width:767px){.dash-grid{grid-template-columns:1fr}.bars{gap:4px}}
.ord-mgmt{border:1px solid var(--line);border-radius:14px;padding:12px;margin-bottom:12px;background:var(--bg-warm)}
.ord-hist{margin-top:10px;font-size:.76rem;color:var(--ink-2);display:grid;gap:3px}
.sec-chk{display:flex;gap:14px;flex-wrap:wrap}
.chk{display:flex;align-items:center;gap:8px;font-size:.84rem;color:var(--ink-2)}
.od-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;font-size:.84rem;margin-bottom:12px}
.od-grid b{color:var(--ink-3);font-weight:600;margin-inline-end:4px}
.badge-hide{background:var(--bg-warm);color:var(--ink-3);border:1px solid var(--line);border-radius:999px;font-size:.66rem;padding:1px 8px;margin-inline-start:6px}
.sms-hint{font-size:.78rem;color:var(--ink-2);background:var(--bg-warm);border:1px dashed var(--line);border-radius:12px;padding:10px 14px;margin-bottom:12px;line-height:2}
.sms-hint code{background:#fff;border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:.74rem}
.sms-test{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
@media(max-width:767px){.admin-stats{grid-template-columns:repeat(2,1fr)}.od-grid{grid-template-columns:1fr}}
</style>
