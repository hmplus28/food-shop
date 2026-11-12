<template>
  <div class="admin-card">
    <div class="admin-toolbar">
      <span class="sync-chip" :class="pending ? 'off' : 'on'">{{ toFa(pending) }} درخواست در انتظار پیگیری</span>
      <button class="btn btn-light btn-sm" @click="load">به‌روزرسانی ⟳</button>
    </div>
    <div v-if="!rows.length" class="up-empty"><svg class="icon"><use href="#i-headset" /></svg><p>درخواست مشاوره‌ای ثبت نشده است.</p></div>
    <div v-else class="tbl-wrap">
      <table class="tbl">
        <thead><tr><th>نام</th><th>موبایل</th><th>موضوع</th><th>زمان ثبت</th><th>وضعیت</th><th></th></tr></thead>
        <tbody>
          <tr v-for="c in rows" :key="c.id">
            <td>{{ c.name }}</td>
            <td dir="ltr" style="text-align:end"><a :href="'tel:' + c.phone">{{ toFa(c.phone) }}</a></td>
            <td>{{ c.topic || '—' }}</td>
            <td style="white-space:nowrap">{{ jDateTime(c.at) }}</td>
            <td><span class="tag" :class="c.done ? 'green' : 'red'">{{ c.done ? 'پیگیری شد' : 'در انتظار' }}</span></td>
            <td class="td-acts">
              <button class="btn btn-light btn-sm" @click="toggle(c)">{{ c.done ? 'بازگردانی' : 'پیگیری شد' }}</button>
              <button class="btn btn-light btn-sm del" @click="remove(c)">حذف</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { toFa } from '../../data/site';
import { jDateTime } from '../../data/jalali';
import { apiCall } from '../../services/api';
import { toast } from '../../stores/ui';
import '../../assets/admin.css';

const rows = ref([]);
const pending = ref(0);
async function load() {
  const r = await apiCall('/admin/consults');
  if (!r.ok) return toast(r.msg || 'دریافت درخواست‌ها انجام نشد', 'err');
  rows.value = r.consults; pending.value = r.pending;
}
async function toggle(c) {
  const r = await apiCall('/admin/consults/' + c.id, { method: 'PATCH', body: { done: !c.done } });
  r.ok ? load() : toast(r.msg, 'err');
}
async function remove(c) {
  if (!window.confirm('این درخواست حذف شود؟')) return;
  const r = await apiCall('/admin/consults/' + c.id, { method: 'DELETE' });
  r.ok ? load() : toast(r.msg, 'err');
}
onMounted(load);
</script>
