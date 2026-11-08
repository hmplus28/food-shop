/* ---------- علاقه‌مندی‌ها ---------- */
import { reactive, computed } from 'vue';
import { LS } from '../data/site';
import { toast } from './ui';

export const fav = reactive({
  ids: LS.get('favs', []),
});
const save = () => LS.set('favs', fav.ids);

export const favCount = computed(() => fav.ids.length);
export const isFav = id => fav.ids.includes(Number(id));

export function toggleFav(pid) {
  const i = fav.ids.indexOf(Number(pid));
  if (i > -1) { fav.ids.splice(i, 1); toast('از علاقه‌مندی‌ها حذف شد', 'ok'); }
  else { fav.ids.push(Number(pid)); toast('به علاقه‌مندی‌ها اضافه شد ❤️', 'gold'); }
  save();
}
