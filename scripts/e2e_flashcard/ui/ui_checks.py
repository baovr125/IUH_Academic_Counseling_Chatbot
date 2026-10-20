"""Đoạn JavaScript chạy trong trình duyệt để đo tương phản chữ (WCAG) và phát hiện tràn ngang. Dùng chung cho shots*.py."""

CONTRAST_JS = r'''
() => {
  const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const over = (top, bottom) => { const a = top.a + bottom.a * (1 - top.a); if (a === 0) return { r: 0, g: 0, b: 0, a: 0 };
    return { r: (top.r * top.a + bottom.r * bottom.a * (1 - top.a)) / a, g: (top.g * top.a + bottom.g * bottom.a * (1 - top.a)) / a,
             b: (top.b * top.a + bottom.b * bottom.a * (1 - top.a)) / a, a }; };
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const dark = document.documentElement.classList.contains('dark');
  const bgOf = (el) => { const layers = []; let e = el;
    while (e) { const cs = getComputedStyle(e);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return null;
      const c = parse(cs.backgroundColor); if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
      e = e.parentElement; }
    let base = dark ? { r: 15, g: 23, b: 42, a: 1 } : { r: 255, g: 255, b: 255, a: 1 };
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return base; };
  const opacityOf = (el) => { let o = 1, e = el; while (e) { o *= parseFloat(getComputedStyle(e).opacity || '1'); e = e.parentElement; } return o; };
  const dialog = document.querySelector('[role=dialog]');
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3 && n.textContent.trim()).map((n) => n.textContent.trim()).join(' ');
    if (!own) continue;
    if (dialog && !dialog.contains(el)) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    if (el.closest('[disabled],[aria-disabled=true],.sr-only')) continue;
    const bg = bgOf(el); if (!bg) continue;
    let fg = parse(cs.color); if (!fg) continue;
    fg = { ...fg, a: fg.a * opacityOf(el) };
    const eff = over(fg, bg);
    const l1 = lum(eff), l2 = lum(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const px = parseFloat(cs.fontSize); const bold = parseInt(cs.fontWeight) >= 700;
    const large = px >= 24 || (px >= 18.66 && bold);
    const need = large ? 3 : 4.5;
    if (ratio < need) out.push({ text: own.slice(0, 40), ratio: Math.round(ratio * 100) / 100, need, size: px, cls: (el.className || '').toString().split(/\s+/).filter((c) => /text-|dark:text-|bg-/.test(c)).slice(0, 6).join(' '), tag: el.tagName });
  }
  return out;
}
'''

OVERFLOW_JS = r'''
() => {
  const main = document.querySelector('main');
  const vw = document.documentElement.clientWidth;
  const bad = [];
  if (main && main.scrollWidth > main.clientWidth + 1) bad.push({ kind: 'main-scroll', sw: main.scrollWidth, cw: main.clientWidth });
  if (document.documentElement.scrollWidth > vw + 1) bad.push({ kind: 'page-scroll', sw: document.documentElement.scrollWidth, cw: vw });
  const dialog = document.querySelector('[role=dialog]');
  const root = dialog || main || document.body;
  for (const el of root.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (el.closest('.overflow-x-auto, .overflow-hidden, svg')) continue;
    if (r.right > vw + 1 || r.left < -1) bad.push({ kind: 'element-outside', tag: el.tagName, cls: (el.className || '').toString().slice(0, 80), left: Math.round(r.left), right: Math.round(r.right), text: (el.textContent || '').trim().slice(0, 30) });
    if (bad.length > 12) break;
  }
  return bad;
}
'''
