// Renderiza fotogramas de preview.html a PNG y monta una hoja de contactos para revisar la animación.
// Uso: node tools/anim/render.js animations/correr/preview.html <carpeta-salida> [vistas] [frames]
//   vistas: lista separada por comas (34,side,front,back). Por defecto: 34,side
//   frames: lista separada por comas. Por defecto: 0..duración-1
const path = require('path');
const fs = require('fs');
let playwright;
try { playwright = require('playwright'); } catch { playwright = require('/opt/node22/lib/node_modules/playwright'); }

(async () => {
  const html = path.resolve(process.argv[2]);
  const out = path.resolve(process.argv[3] || 'render');
  const views = (process.argv[4] || '34,side').split(',');
  fs.mkdirSync(out, { recursive: true });

  const browser = await playwright.chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const page = await browser.newPage({ viewport: { width: Number(process.env.W || 440), height: Math.round(Number(process.env.W || 440) * 11 / 16) }, deviceScaleFactor: 1 });
  await page.goto('file://' + html + '?shot=1&frame=0');
  const N = await page.evaluate(() => window.ANIM.duracionFrames);
  const frames = process.argv[5] ? process.argv[5].split(',').map(Number) : [...Array(N).keys()];

  const shots = [];
  for (const v of views) {
    for (const f of frames) {
      await page.goto(`file://${html}?shot=1&frame=${f}&view=${v}`);
      await page.waitForSelector('body[data-ready="1"]');
      const file = path.join(out, `${v}_${String(f).padStart(2, '0')}.png`);
      await page.locator('#view').screenshot({ path: file });
      shots.push({ v, f, file });
    }
  }

  // Hoja de contactos: una fila por vista
  const cols = frames.length;
  const sheet = `<html><body style="margin:0;background:#222;font:12px monospace;color:#eee">
    ${views.map((v) => `<div style="display:grid;grid-template-columns:repeat(${Math.min(cols, 10)},220px);gap:2px;margin-bottom:6px">
      ${shots.filter((s) => s.v === v).map((s) => `<div style="position:relative"><img src="file://${s.file}" style="width:220px;display:block"><span style="position:absolute;left:4px;top:2px;background:#000a;padding:0 3px">${v} f${s.f}</span></div>`).join('')}
    </div>`).join('')}</body></html>`;
  const sheetPath = path.join(out, 'sheet.html');
  fs.writeFileSync(sheetPath, sheet);
  const sp = await browser.newPage({ viewport: { width: Math.min(cols, 10) * 222, height: 200 } });
  await sp.goto('file://' + sheetPath);
  await sp.screenshot({ path: path.join(out, 'sheet.png'), fullPage: true });
  await browser.close();
  console.log(`OK: ${shots.length} fotogramas + sheet.png en ${out}`);
})().catch((e) => { console.error(e); process.exit(1); });
