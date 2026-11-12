/* ---------- داده‌های فروشگاه خانم گل ---------- */
import { reactive } from 'vue';
import { LS } from './site';

/* تصاویر روی خود هاست در /img/ (دانلود با scripts/fetch_assets.py)؛ در نبود فایل، fallback خودکار به منبع اصلی (main.js) */
export const IMG = (import.meta.env.BASE_URL || '/') + 'img/';

/* دسته‌بندی‌ها (۱۳ دسته) */
export const CATS = [
  { id: 'ajil', name: 'آجیل و مغزها', icon: 'i-nut', subs: ['آجیل مخلوط شور', 'آجیل مخلوط شیرین', 'آجیل چهارمغز', 'مغزهای خام', 'آجیل سویسالی', 'آجیل رژیمی'], feat: { img: IMG + '66fd0cba7ee8.jpg', t: 'آجیل مخلوط خانم گل', s: 'پنج‌مغز منتخب؛ تازه بو داده' } },
  { id: 'pistachio', name: 'پسته', icon: 'i-nut', subs: ['پسته اکبری', 'پسته احمدآقایی', 'پسته فندقی', 'پسته خوئی', 'مغز پسته سبز', 'پسته شور لیمویی'], feat: { img: IMG + 'ec01895c5c0b.jpg', t: 'پسته اکبری رفسنجان', s: 'ملکه پسته‌های ایران' } },
  { id: 'almond', name: 'بادام', icon: 'i-nut', subs: ['بادام درختی خام', 'بادام مامایی', 'بادام بو داده', 'مغز بادام', 'بادام پوست کاغذی'], feat: { img: IMG + 'c6b8b1936b7c.jpg', t: 'بادام بو داده نمکین', s: 'عصرانه‌ای سالم و خوش‌طعم' } },
  { id: 'walnut', name: 'گردو', icon: 'i-nut', subs: ['مغز گردو هفت‌پر', 'گردوی درشت چانچاله', 'گردوی تویسرکان', 'گردوی خشک'], feat: { img: IMG + '40ca66cd7225.webp', t: 'مغز گردو هفت‌پر', s: 'روشن و بدون تلخی' } },
  { id: 'hazelnut', name: 'فندق', icon: 'i-nut', subs: ['فندق خام', 'فندق بو داده', 'فندق شکلاتی'], feat: { img: IMG + '77db1fb48eed.jpg', t: 'فندق درشت اردبیل', s: 'تازه‌رس پاییز' } },
  { id: 'seeds', name: 'تخمه و مغز تخمه', icon: 'i-leaf', subs: ['تخمه کدو گوشتی', 'مغز تخمه آفتابگردان', 'تخمه ژاپنی', 'مغز هندوانه', 'تخمه هلیله‌ای'], feat: { img: IMG + '5675e680be54.jpg', t: 'تخمه کدو گوشتی', s: 'کم‌نمک و بو داده' } },
  { id: 'dryfruit', name: 'میوه خشک', icon: 'i-leaf', subs: ['برگه زردآلو', 'آلو بخارا', 'چیپس میوه', 'میوه خشک مخلوط', 'لیمو عمانی خشک'], feat: { img: IMG + '4aa5a36466e4.jpg', t: 'میوه خشک مخلوط', s: 'سفره رنگی میوه‌های آفتابی' } },
  { id: 'raisin', name: 'کشمش و مویز', icon: 'i-leaf', subs: ['کشمش سبز قلمی', 'مویز بدون هسته', 'کشمش پلویی', 'کشمش مالایر', 'مویز آفتابی'], feat: { img: IMG + '184fecd2458a.jpg', t: 'کشمش سبز قلمی', s: 'شیرین و ملایم ملایر' } },
  { id: 'date', name: 'خرما و رطب', icon: 'i-leaf', subs: ['خرما پیارم', 'خرمای مضافتی', 'خرمای رطب مازافتی', 'خرمای شاهانی', 'خرمای کبکاب'], feat: { img: IMG + '42f5d4b9754e.jpg', t: 'خرمای مضافتی بم', s: 'شیرین و مرطوب' } },
  { id: 'mulberryfig', name: 'توت خشک و انجیر', icon: 'i-leaf', subs: ['توت خشک سفید', 'انجیر خشک استهبان', 'انجیر پرورده', 'توت پرورده'], feat: { img: IMG + '7b3e238840f4.jpeg', t: 'انجیر استهبان', s: 'شیرین‌ترین انجیر ایران' } },
  { id: 'saffron', name: 'زعفران و ادویه', icon: 'i-fire', subs: ['زعفران سرگل', 'زعفران پوشال', 'زعفران نگین', 'ادویه پلویی'], feat: { img: IMG + '2c259b7044c5.jpg', t: 'زعفران سرگل قائنات', s: 'قرمز و خوش‌رنگ، عطر بی‌نظیر' } },
  { id: 'tea', name: 'دمنوش و محصولات طبیعی', icon: 'i-leaf', subs: ['دمنوش گاوزبان', 'دمنوش آرامش', 'چای ترش', 'دمنوش لاغری', 'عسل طبیعی'], feat: { img: IMG + '36eff119ff2f.jpg', t: 'دمنوش‌های گیاهی', s: 'از دل طبیعت تا فنجان شما' } },
  { id: 'giftbox', name: 'آجیل و پک‌های هدیه', icon: 'i-gift', subs: ['پک هدیه یلدا', 'پک هدیه نوروز', 'جعبه هدیه لوکس', 'پک سازمانی'], feat: { img: IMG + 'ed59578015d4.jpeg', t: 'پک‌های هدیه خانم گل', s: 'بسته‌بندی لوکس با کارت تبریک', hot: true } },
];

/* محصولات پایه (۲۸ محصول) */
const BASE = [
  { id: 1, name: 'پسته اکبری ممتاز رفسنجان', cat: 'pistachio', img: IMG + 'ec01895c5c0b.jpg', price: 1980000, weights: [250, 500, 1000, 2000], stock: 42, disc: 10, grade: 'ممتاز', rate: 4.9, sold: 1240, tags: ['پرفروش', 'ممتاز'], sec: ['best', 'amz'], desc: 'پسته اکبری درشت و خندار رفسنجان؛ بو داده با نمک دریا و کاملاً تازه. عالی برای مهمانی و شب یلدا.' },
  { id: 2, name: 'پسته احمدآقایی ممتاز', cat: 'pistachio', img: IMG + 'f6d280936b47.jpg', price: 1750000, weights: [250, 500, 1000, 2000], stock: 38, disc: 0, grade: 'ممتاز', rate: 4.8, sold: 980, tags: ['پرفروش'], sec: ['best'], desc: 'پسته احمدآقایی باریک و خندان با مغز سبز تیره؛ محبوب‌ترین پسته برای پذیرایی.' },
  { id: 3, name: 'پسته فندقی بو داده', cat: 'pistachio', img: IMG + 'e218521bb098.jpg', price: 1450000, weights: [250, 500, 1000, 2000], stock: 55, disc: 5, grade: 'درجه یک', rate: 4.7, sold: 760, tags: [], sec: ['best'], desc: 'پسته فندقی ریز و خوش‌مزه؛ مناسب عصرانه و تنقلات روزانه خانواده.' },
  { id: 4, name: 'مغز پسته سبز پرزدار', cat: 'pistachio', img: IMG + '99b54d43d43f.jpg', price: 2950000, weights: [250, 500, 1000], stock: 22, disc: 0, grade: 'ممتاز', rate: 4.9, sold: 530, tags: ['ممتاز'], sec: ['best', 'new'], desc: 'مغز پسته سبز درجه یک برای شیرینی‌پزی، سالاد و پذیرایی؛ رنگ و طعم بی‌نظیر.' },
  { id: 5, name: 'بادام درختی خام (مامایی)', cat: 'almond', img: IMG + '5f3a2793e06f.jpg', price: 850000, weights: [250, 500, 1000, 2000], stock: 64, disc: 0, grade: 'درجه یک', rate: 4.8, sold: 1105, tags: ['پرفروش'], sec: ['best'], desc: 'بادام مامایی درشت و پوست‌کاغذی؛ تازه از باغ‌های سمنان و ارسنجان.' },
  { id: 6, name: 'بادام درختی بو داده نمکین', cat: 'almond', img: IMG + 'c6b8b1936b7c.jpg', price: 920000, weights: [250, 500, 1000, 2000], stock: 47, disc: 8, grade: 'درجه یک', rate: 4.7, sold: 640, tags: [], sec: ['amz'], desc: 'بادام بو داده با نمک دریایی؛ روزانه تازه برشته می‌شود.' },
  { id: 7, name: 'بادام هندی شور', cat: 'ajil', img: IMG + 'eddf227382bb.png', price: 1450000, weights: [250, 500, 1000, 2000], stock: 51, disc: 12, grade: 'درجه یک', rate: 4.8, sold: 1520, tags: ['پرفروش'], sec: ['best', 'amz'], desc: 'بادام هندی درشت و کرمی با نمک متعادل؛ محبوب‌ترین مغز مهمانی.' },
  { id: 8, name: 'مغز گردو هفت‌پر تویسرکان', cat: 'walnut', img: IMG + '40ca66cd7225.webp', price: 1250000, weights: [250, 500, 1000, 2000], stock: 36, disc: 15, grade: 'ممتاز', rate: 4.9, sold: 870, tags: ['پرفروش'], sec: ['best', 'amz'], desc: 'مغز گردو روشن و هفت‌پر بدون تلخی؛ سرشار از امگا۳.' },
  { id: 9, name: 'فندق خام درشت', cat: 'hazelnut', img: IMG + '77db1fb48eed.jpg', price: 780000, weights: [250, 500, 1000, 2000], stock: 58, disc: 0, grade: 'درجه یک', rate: 4.6, sold: 690, tags: [], sec: ['best'], desc: 'فندق درشت اردبیل؛ خام و سالم، مناسب بو دادن خانگی و شکلات‌سازی.' },
  { id: 10, name: 'تخمه کدو گوشتی بو داده', cat: 'seeds', img: IMG + '5675e680be54.jpg', price: 920000, weights: [250, 500, 1000, 2000], stock: 44, disc: 10, grade: 'درجه یک', rate: 4.8, sold: 930, tags: ['پرفروش'], sec: ['best', 'amz'], desc: 'تخمه کدو گوشتی سبز و بدون پوست با نمک کم؛ میان‌وعده‌ای سالم برای همه سنین.' },
  { id: 11, name: 'مغز تخمه آفتابگردان', cat: 'seeds', img: IMG + '397a7c914638.png', price: 690000, weights: [250, 500, 1000, 2000], stock: 70, disc: 0, grade: 'درجه یک', rate: 4.5, sold: 410, tags: [], sec: ['new'], desc: 'مغز تخمه آفتابگردان تمیز و تازه؛ برای سالاد، نان و آشپزی.' },
  { id: 12, name: 'تخمه ژاپنی نمکین', cat: 'seeds', img: IMG + 'bacd7f52d5e8.jpg', price: 290000, weights: [250, 500, 1000, 2000], stock: 88, disc: 5, grade: 'درجه یک', rate: 4.4, sold: 1240, tags: [], sec: [], desc: 'تخمه ژاپنی خوش‌بهر با نمک لیمویی؛ همراه همیشگی دورهمی‌ها.' },
  { id: 13, name: 'انجیر خشک استهبان ممتاز', cat: 'mulberryfig', img: IMG + '7b3e238840f4.jpeg', price: 640000, weights: [250, 500, 1000, 2000], stock: 40, disc: 10, grade: 'ممتاز', rate: 4.9, sold: 540, tags: ['ممتاز'], sec: ['new', 'amz'], desc: 'انجیر خشک استهبان با گلوی سفید و شیرینی طبیعی؛ چیده‌شده از باغ‌های فارس.' },
  { id: 14, name: 'توت خشک سفید درشت', cat: 'mulberryfig', img: IMG + '83e1a888b37f.jpg', price: 720000, weights: [250, 500, 1000, 2000], stock: 33, disc: 0, grade: 'ممتاز', rate: 4.8, sold: 470, tags: [], sec: ['new'], desc: 'توت خشک سفید درشت و پرشیرینی؛ جایگزین سالم قند کنار چای.' },
  { id: 15, name: 'کشمش سبز قلمی ملایم', cat: 'raisin', img: IMG + '184fecd2458a.jpg', price: 380000, weights: [250, 500, 1000, 2000], stock: 76, disc: 8, grade: 'درجه یک', rate: 4.7, sold: 810, tags: [], sec: ['new'], desc: 'کشمش سبز قلمی با شیرینی ملایم؛ عالی برای پلئو، شیرینی و میان‌وعده.' },
  { id: 16, name: 'مویز بدون هسته (کشمش سیاه)', cat: 'raisin', img: IMG + '1e147cae76b8.jpg', price: 420000, weights: [250, 500, 1000, 2000], stock: 62, disc: 0, grade: 'ممتاز', rate: 4.8, sold: 520, tags: [], sec: ['new'], desc: 'مویز تیره و آفتابی بدون هسته؛ سرشار از آهن و انرژی طبیعی.' },
  { id: 17, name: 'کشمش پلویی طلایی', cat: 'raisin', img: IMG + 'aa25c7492bb4.jpg', price: 260000, weights: [250, 500, 1000, 2000], stock: 90, disc: 5, grade: 'درجه یک', rate: 4.5, sold: 1150, tags: [], sec: [], desc: 'کشمش پلویی روشن و کم‌شیرین؛ انتخاب اول قابلمه‌های ایرانی.' },
  { id: 18, name: 'خرما پیارم ممتاز حصکوه', cat: 'date', img: IMG + 'fb2be35ef680.jpeg', price: 890000, weights: [250, 500, 1000, 2000], stock: 29, disc: 10, grade: 'ممتاز', rate: 4.9, sold: 640, tags: ['ممتاز'], sec: ['new', 'amz'], desc: 'خرما پیارم درشت و مرطوب با شیرینی کاراملی؛ لقب «خرمای شاهانه» را دارد.' },
  { id: 19, name: 'خرمای مضافتی بم', cat: 'date', img: IMG + '42f5d4b9754e.jpg', price: 320000, weights: [250, 500, 1000, 2000], stock: 96, disc: 12, grade: 'درجه یک', rate: 4.8, sold: 1980, tags: ['پرفروش'], sec: ['amz'], desc: 'خرمای مضافتی تازه و مرطوب بم؛ شیرین، نرم و محبوب همه.' },
  { id: 20, name: 'برگه زردآلو آفتابی', cat: 'dryfruit', img: IMG + 'b2f2d1414a8d.jpg', price: 560000, weights: [250, 500, 1000, 2000], stock: 37, disc: 0, grade: 'ممتاز', rate: 4.7, sold: 380, tags: [], sec: ['new'], desc: 'برگه زردآلو خشک‌شده زیر آفتاب بدون افزودن شکر؛ ترش و شیرین طبیعی.' },
  { id: 21, name: 'آلو خشک بخارا', cat: 'dryfruit', img: IMG + '3cb5b008199c.jpg', price: 340000, weights: [250, 500, 1000, 2000], stock: 54, disc: 5, grade: 'درجه یک', rate: 4.6, sold: 760, tags: [], sec: [], desc: 'آلو بخارای آبدار و گوشت‌دار؛ برای خورشت، پلئو و میان‌وعده.' },
  { id: 22, name: 'چیپس میوه مخلوط بدون قند', cat: 'dryfruit', img: IMG + 'f668152a2bcf.png', price: 480000, weights: [250, 500, 1000], stock: 31, disc: 15, grade: 'درجه یک', rate: 4.6, sold: 290, tags: [], sec: ['new', 'amz'], desc: 'چیپس سیب، هلو و موز خشک‌شده بدون قند افزودنی؛ اسنک سالم بچه‌ها.' },
  { id: 23, name: 'میوه خشک مخلوط مهمانی', cat: 'dryfruit', img: IMG + '4aa5a36466e4.jpg', price: 620000, weights: [250, 500, 1000, 2000], stock: 48, disc: 0, grade: 'ممتاز', rate: 4.8, sold: 450, tags: [], sec: ['new'], desc: 'ترکیبی رنگارنگ از برگه‌ها و میوه‌های خشک؛ پذیرایی متفاوت و سالم.' },
  { id: 24, name: 'آجیل مخلوط شور (پنج‌مغز)', cat: 'ajil', img: IMG + '66fd0cba7ee8.jpg', price: 1680000, weights: [250, 500, 1000, 2000], stock: 26, disc: 10, grade: 'ممتاز', rate: 4.9, sold: 2100, tags: ['پرفروش'], sec: ['best', 'amz'], desc: 'پسته، بادام، فندق، مغز گردو و بادام هندی؛ با نسبت طلایی و تازه بو داده.' },
  { id: 25, name: 'آجیل مخلوط شیرین چهارمغز', cat: 'ajil', img: IMG + 'ca78178474b1.png', price: 1590000, weights: [250, 500, 1000, 2000], stock: 34, disc: 0, grade: 'ممتاز', rate: 4.7, sold: 380, tags: [], sec: ['best'], desc: 'مغزهای بدون نمک برای بارداری، رژیم و ورزشکاران؛ ترکیب متعادل چهار مغز.' },
  { id: 26, name: 'زعفران سرگل ممتاز قائنات', cat: 'saffron', img: IMG + '2c259b7044c5.jpg', price: 165000000, weights: [2, 5, 10, 25], stock: 60, disc: 5, grade: 'ممتاز', rate: 5.0, sold: 340, tags: ['ممتاز'], sec: ['new'], desc: 'زعفران سرگل درجه یک قائنات با رنگ‌دهی فوق‌العاده؛ بسته‌بندی شکستنی با پلمپ.' },
  { id: 27, name: 'دمنوش گل گاوزبان و سنبل‌الطیب', cat: 'tea', img: IMG + '36eff119ff2f.jpg', price: 380000, weights: [100, 250, 500], stock: 65, disc: 0, grade: 'درجه یک', rate: 4.8, sold: 420, tags: [], sec: ['new'], desc: 'دمنوش آرام‌بخش با گل گاوزبان، سنبل‌الطیب و اسطوخودوس؛ آرامش شبانه.' },
  { id: 28, name: 'دمنوش آرامش (به‌لیمو و گل محمدی)', cat: 'tea', img: IMG + 'e5e69256f8fd.jpg', price: 420000, weights: [100, 250, 500], stock: 52, disc: 10, grade: 'درجه یک', rate: 4.7, sold: 260, tags: [], sec: ['amz'], desc: 'ترکیب معطر به‌لیمو، گل محمدی و بهارنارنج؛ نوشیدنی برگزیده عصرها.' },
];

/* پک‌های تخفیفی کارت دورانی */
export const PACKS = [
  { pid: 24, w: 500, old: 1290000, now: 969000, hours: 24, name: 'پک آجیل مهمانی', sub: 'آجیل پنج‌مغز + بسته‌بندی مهمانی' },
  { pid: 4, w: 250, old: 1150000, now: 977000, hours: 48, name: 'پک مغز پسته سبز', sub: 'مغز پسته + پسته شور ویژه' },
  { pid: 23, w: 500, old: 780000, now: 585000, hours: 24, name: 'پک میوه خشک سالم', sub: 'میوه خشک مخلوط + چیپس میوه' },
  { pid: 27, w: 250, old: 520000, now: 416000, hours: 48, name: 'پک دمنوش آرامش', sub: 'دو دمنوش گیاهی منتخب' },
];

/* خرید اطمینان (کالای هر روز) */
export const TRUST = [
  { day: 6, name: 'کاسه سرو چوبی دست‌ساز با دو قاشق', img: IMG + 'c7db525d1daf.jpg', old: 850000, price: 637000, off: 25 },
  { day: 0, name: 'کاسه سرامیک لعاب‌دار نارنجی (دست‌ساز لالجین)', img: IMG + '05508d4b4470.jpg', old: 690000, price: 586000, off: 15 },
  { day: 1, name: 'سرویس استکان چای‌خوری طرح طلایی ۶ نفره', img: IMG + '12c552f00b7b.jpg', old: 1850000, price: 1480000, off: 20 },
  { day: 2, name: 'سینی برجسته برنجی سنتی قلم‌زنی', img: IMG + '19d13838919c.jpg', old: 2400000, price: 1920000, off: 20 },
  { day: 3, name: 'کاسه چوب گردو با لبه موجی', img: IMG + 'cd5ba20a33e2.jpg', old: 780000, price: 624000, off: 20 },
  { day: 4, name: 'سینی مسی قلم‌زنی‌شده اصفهان', img: IMG + 'e569cfd83324.jpg', old: 2150000, price: 1612000, off: 25 },
  { day: 5, name: 'کاسه سرامیک سبز مات دست‌ساز', img: IMG + '7f5b9c96c99e.jpg', old: 640000, price: 512000, off: 20 },
];
export const TRUST_WHY = 'اعتماد شما بزرگ‌ترین سرمایه ماست! هر روز یک کالای منتخب — لوازم سرو و دکور سنتی — را با قیمت ویژه به سبد شما اضافه می‌کنیم؛ چون به خانم گل اعتماد دارید، به ما مطمئنید.';
export const TRUST_VPIDS = {};
TRUST.forEach((t, i) => { TRUST_VPIDS[t.day] = 90 + i; });

/* کارت شانس */
export const PRIZES = [
  { c: 'SHIP0', t: 'ارسال رایگان سفارش!', d: 'هزینه ارسال سفارش فعلی شما رایگان شد.', ic: 'i-truck', w: 20 },
  { c: 'LUCK5', t: '۵٪ تخفیف فوری', d: 'کد تخفیف ۵ درصدی برای همین سفارش.', ic: 'i-percent', w: 26 },
  { c: 'NEXT15', t: '۱۵٪ تخفیف خرید بعدی', d: 'برای خرید بعدی‌تان ۱۵ درصد تخفیف بگیرید.', ic: 'i-tag', w: 17 },
  { c: 'SAMEDAY', t: 'اولویت ارسال همان روز', d: 'سفارش شما با اولویت «ارسال همان روز» پردازش می‌شود.', ic: 'i-fire', w: 10 },
  { c: 'LUCK20', t: 'جایزه بزرگ: ۲۰٪ تخفیف!', d: 'شانس طلایی! ۲۰ درصد تخفیف ویژه خانم گل.', ic: 'i-star', w: 5 },
  { c: 'CASH50', t: '۵۰٬۰۰۰ تومان اعتبار خرید', d: 'اعتبار ۵۰ هزار تومانی در کیف پول پنل شما.', ic: 'i-wallet', w: 12 },
];

/* کدهای تخفیف */
export const COUPONS = {
  WELCOME10: { type: 'pct', val: 10, min: 500000, first: true, label: '۱۰٪ تخفیف اولین خرید (حداقل ۵۰۰٬۰۰۰ تومان)' },
  LUCK5: { type: 'pct', val: 5, min: 0, label: '۵٪ تخفیف کارت شانس' },
  LUCK20: { type: 'pct', val: 20, min: 300000, label: '۲۰٪ تخفیف طلایی (حداقل ۳۰۰٬۰۰۰ تومان)' },
  NEXT15: { type: 'pct', val: 15, min: 0, label: '۱۵٪ تخفیف خرید بعدی' },
  SHIP0: { type: 'ship', val: 0, min: 0, label: 'ارسال رایگان' },
  CASH50: { type: 'cash', val: 50000, min: 300000, label: '۵۰٬۰۰۰ تومان اعتبار (حداقل ۳۰۰٬۰۰۰ تومان)' },
  SAMEDAY: { type: 'day', val: 0, min: 0, label: 'اولویت ارسال همان روز' },
};

/* تم‌های رنگی */
export const THEMES = [
  { id: 'default', name: 'پسته‌ای', color: '#48b500' },
  { id: 'anari', name: 'اناری', color: '#c03045' },
  { id: 'zeitoni', name: 'زیتونی طبیعی', color: '#6d8f2f' },
  { id: 'gahvei', name: 'قهوه‌ای کلاسیک', color: '#6b4a2b' },
  { id: 'tousi', name: 'طوسی مدرن', color: '#5c6b75' },
  { id: 'banafsh', name: 'بنفش اسطوخودوس', color: '#7a5fa8' },
  { id: 'abi', name: 'آبی نفتی', color: '#1f5a73' },
];

/* ---------- فهرست واکنش‌گرای محصولات (با ادغام تغییرات پنل مدیر) ---------- */
function buildBase() {
  const list = BASE.map(p => ({ ...p, tags: [...p.tags], sec: [...p.sec], weights: [...p.weights] }));
  /* محصولات مجازی بخش خرید اطمینان (قابل افزودن به سبد؛ در فروشگاه نمایش داده نمی‌شوند) */
  TRUST.forEach((t, i) => {
    list.push({ id: 90 + i, name: t.name, cat: 'giftbox', img: t.img, price: t.price * 1000, weights: [1], stock: 8, disc: 0, grade: 'دست‌ساز', rate: 4.9, sold: 88, tags: ['خرید اطمینان'], sec: [], hide: true, desc: 'کالای منتخب بخش «خرید اطمینان»؛ هر روز با قیمت ویژه.' });
  });
  return list;
}

export const products = reactive(buildBase());

/* اعمال ویرایش‌های آزمایشی پنل مدیر (LocalStorage) روی فهرست فعلی —
   بعد از همگام‌سازی بک‌اند هم دوباره صدا زده می‌شود تا ویرایش‌ها حفظ شوند. */
export function applyAdminOverrides() {
  if (String(import.meta.env.VITE_API_ENABLED).toLowerCase() === 'true') return;   // با سرور فعال، سرور مرجع است
  const saved = LS.get('adminProducts', null);
  if (Array.isArray(saved) && saved.length) products.splice(0, products.length, ...saved);
}
applyAdminOverrides();

/* ---- محصولات «مجازی» (پک‌ها و خرید اطمینان): در فهرست عمومی سرور نیستند؛ از دادهٔ /site ساخته می‌شوند ---- */
let VIRTUAL = [];
export function virtualFrom(packs = [], trust = [], img = u => u) {
  const mk = (pid, name, image, price, stock, kind) => ({ id: Number(pid), name, cat: 'giftbox', img: img(image || ''), price: Number(price) * 1000, weights: [1],
    stock: Number(stock) || 0, disc: 0, grade: kind, rate: 5, sold: 0, tags: [], sec: ['__virtual'], desc: '', hide: true });
  return [
    ...packs.filter(p => p.pid).map(p => mk(p.pid, p.name, p.image, p.now, p.stock, 'پک تخفیفی')),
    ...trust.filter(t => t.pid).map(t => mk(t.pid, t.name, t.image, t.price, t.stock, 'خرید اطمینان')),
  ];
}
export function applyVirtualProducts() {
  for (const v of VIRTUAL) {
    const i = products.findIndex(p => p.id === v.id);
    if (i > -1) products.splice(i, 1, v); else products.push(v);
  }
}
export function setVirtualProducts(list) { VIRTUAL = list; applyVirtualProducts(); }
/* از کش مرورگر هنگام بارگذاری: سبد ذخیره‌شده با پک/کالای اعتماد بعد از رفرش پاک نشود */
if (String(import.meta.env.VITE_API_ENABLED).toLowerCase() === 'true') {
  const c = LS.get('shopCache', {});
  if (c && (c.packs || c.trust)) VIRTUAL = virtualFrom(c.packs, c.trust, u => u);
  applyVirtualProducts();
}

export const prod = id => products.find(p => p.id === Number(id));
export const catOf = id => CATS.find(c => c.id === id);
export const visibleProducts = () => products.filter(p => !p.hide);

export function persistProducts() { LS.set('adminProducts', JSON.parse(JSON.stringify(products))); }
export function resetProducts() { LS.del('adminProducts'); products.splice(0, products.length, ...buildBase()); }
export function nextProductId() { return Math.max(100, ...products.map(p => p.id)) + 1; }
