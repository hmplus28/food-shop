/* ---------- نمایش امن متن صفحات (توسط مدیر نوشته می‌شود) ----------
   قالب: «## عنوان»، «- مورد»، «1. گام»، **پررنگ**، پاراگراف‌ها با خط خالی. هر چیز دیگر escape می‌شود
   (هیچ HTML یا اسکریپتی اجرا نمی‌شود). */
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const inline = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

export function renderRichText(text) {
  const lines = String(text || '').replace(/\r/g, '').split('\n');
  const out = [];
  let list = null;          // 'ul' | 'ol'
  let para = [];
  const flushPara = () => { if (para.length) { out.push('<p>' + inline(para.join(' ')) + '</p>'); para = []; } };
  const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const raw of lines) {
    const line = raw.trim();
    let m;
    if (!line) { flushPara(); closeList(); continue; }
    if ((m = line.match(/^(#{2,3})\s+(.+)$/))) { flushPara(); closeList(); out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); continue; }
    if ((m = line.match(/^[-•]\s+(.+)$/))) { flushPara(); if (list !== 'ul') { closeList(); out.push('<ul>'); list = 'ul'; } out.push('<li>' + inline(m[1]) + '</li>'); continue; }
    if ((m = line.match(/^(\d+|[۰-۹]+)[.)]\s+(.+)$/))) { flushPara(); if (list !== 'ol') { closeList(); out.push('<ol>'); list = 'ol'; } out.push('<li>' + inline(m[2]) + '</li>'); continue; }
    closeList(); para.push(line);
  }
  flushPara(); closeList();
  return out.join('\n');
}
