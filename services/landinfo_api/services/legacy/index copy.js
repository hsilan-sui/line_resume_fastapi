//用 Playwright 自動到 EasyMap 站查土地資料，抓表格文字成 JSON，截地圖圖片存到 public/...，並且支援「可重用 session/browser」給 BullMQ worker 做微服務
// land_info：從結果表格 #one-column-emphasis 抓 key-value
// map_image_path：從 #content_map 截圖
// 同時把路徑整理成 public/<city>/<district>/map_<sectionId>_<sectionName>_<landNo>.png

//引入模組
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
require('dotenv').config({ path: path.resolve(__dirname, '../.env') }); //讀取.env

//B) 段名/段號處理：resolveOldSection
// ===引入 session helper 與站點專屬的 validate/preload ===
const { resolveOldSection } = require('../helpers/normalizeSections/resolve-old');

//D) session 管理：ensureSession + validate + preload
const { ensureSession } = require('../helpers/session/session-helper');
const { validate } = require('../helpers/session/validate-easymap');
const { preload } = require('../helpers/session/preload-easymap');

//C) 地號正規化：normalizeLandNo
//加一個地號正規化小工具（把「1306」「1306-0000」「01306」統一成舊站喜歡的格式；你要的話可保留連字號）
function normalizeLandNo(input) {
    const s = String(input || '').trim();
    if (!s) return s;
    // 支援「1234-5678」或純數字，純數字視為前四碼+後四碼（不足左補0）
    const m = s.match(/^(\d{1,4})[-~ ]?(\d{0,4})$/);
    if (!m) return s;
    const a = m[1].padStart(4, '0');
    const b = (m[2] || '').padStart(4, '0');
    return b === '0000' ? a : `${a}-${b}`;
  }

  
// 小工具：人類化停頓

const pause = (min = 250, max = 900) =>
    new Promise(r => setTimeout(r, min + Math.random() * (max - min)));
const ensureDir = (dir) => { if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true }); };

/** ★ 新增：關閉地圖浮層/標記（OpenLayers 常見 DOM）
 * - 先找 popup 關閉鈕
 * - 再嘗試點擊向量圖層 svgRoot（用前後綴匹配，避免硬編號）
 * - 再者嘗試在 .ol-viewport/canvas 內點一下空白
 * - 最後備援按 ESC
 */
async function dismissMapOverlays(page) {
    // A) 常見 popup 關閉鈕
    const closers = page.locator('.ol-popup-closer, .ol-popup .ol-close, button[title="Close"], button:has-text("關閉")');
    if (await closers.count()) { try { await closers.first().click({ timeout: 1200 }); return; } catch {} }
  
    // B) OpenLayers 向量圖層 svgRoot（避免寫死 42）
    const vectorSvg = page.locator('[id^="OpenLayers.Layer.Vector_"][id$="_svgRoot"]');
    if (await vectorSvg.count()) { try { await vectorSvg.first().click(); return; } catch {} }
  
    // C) 可能是 canvas：往 .ol-viewport 或地圖容器內點一下
    const viewport = page.locator('.ol-viewport, canvas.ol-layer, #map, .map, [class*="ol-map"]');
    if (await viewport.count()) {
      try {
        const box = await viewport.first().boundingBox();
        if (box) { await page.mouse.click(box.x + 30, box.y + 30); return; }
        await viewport.first().click(); return;
      } catch {}
    }
  
    // D) 備援：按 ESC
    try { await page.keyboard.press('Escape'); } catch {}
  }


/**
 *  取得土地圖資資訊與地圖截圖
 * ＠params {Object} options
 * @param {string} options.city
 * @param {string} options.district
 * @param {string} options.section
 * @param {string} options.landNo
 */

async function scrapeLandInfo({
    city = process.env.CITY, //// 舊站建議用代碼：桃園市=H
    district = process.env.DISTRICT, //// 復興區=13
    section = process.env.SECTION, //// 可填：大利段 / 1938 / HC_1938
    landNo = process.env.LANDNO,
    _browser,                      // ★ 新增：可注入既有 browser（供 worker 重用）
    headless = process.env.HEADLESS !== 'false' // ★ 新增：可控 headless
  } = {}) {

    // 1) 解析地段
    const sec = resolveOldSection(section || '大利段');
    if (!sec) throw new Error(`找不到段別：${section}（請確認名稱/代碼）`);
    const landNoNorm = normalizeLandNo(landNo);
    console.log('🏙️ 查詢城市：', city, district, section, landNo);
  
    // 確保輸出資料夾存在
    ensureDir(path.resolve(__dirname, './state'));
    ensureDir(path.resolve(__dirname, './debug'));
    ensureDir(path.resolve(__dirname, './public'));
  
    // 若外部有傳 browser 就用；沒有才自己 launch
    const browser = _browser || await chromium.launch({
        headless,
        args: ['--disable-blink-features=AutomationControlled']
    });
  
    try {
      // ✅ 用 ensureSession 建好的 context/page 繼續操作（不要再 newContext/newPage/goto）
      const { context, page, reused } = await ensureSession(browser, {
        statePath: path.resolve(__dirname, './state/easymap.json'),
        targetUrl: 'https://easymap.land.moi.gov.tw/Index',
        validate,
        preload,
        login: async () => {}, // Easymap 無帳密
        headers: {
          'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
          'Referer': 'https://easymap.land.moi.gov.tw/Index'
        },
        ttlHours: 24,
        timeouts: { gotoMs: 45000 },
        debug: { dir: path.resolve(__dirname, './debug'), trace: true },
      });
      console.log('🔐 session reused?', reused);

      // === ★ 我新增：地理定位（Geolocation）設定 ===
       // 說明：因為 context 已經由 ensureSession 建好，這裡用 API 後設置即可
      // - grantPermissions：自動允許地理位置，不會跳「允許定位」彈窗
      // - setGeolocation：預設台灣某點的座標
      await context.grantPermissions(['geolocation'], { origin: 'https://easymap.land.moi.gov.tw' });
      await context.setGeolocation({ latitude: 24.786, longitude: 121.29, accuracy: 50 });

      // === ★ 我新增：一開始先把地圖上的浮層/標記關掉，避免擋到互動 ===
      await dismissMapOverlays(page);
  
      // ===== 連動選單：城市 -> 鄉鎮 =====
      await page.selectOption('#select_city_id', city);
      await Promise.all([
        page.waitForResponse(r => r.url().toLowerCase().includes('town') && r.status() === 200, { timeout: 15000 }).catch(()=>{}),
        page.waitForFunction(() => document.querySelector('#select_town_id')?.options.length > 1, { timeout: 15000 }),
      ]);
      await pause();
  
      // ===== 鄉鎮 -> 段 =====
      await page.selectOption('#select_town_id', district);
      await Promise.all([
        page.waitForResponse(r => r.url().toLowerCase().includes('section') && r.status() === 200, { timeout: 15000 }).catch(()=>{}),
        page.waitForFunction(() => document.querySelector('#select_sect_id')?.options.length > 1, { timeout: 15000 }),
      ]);
      await pause();
  
      // ===== 段 =====
    //   await page.selectOption('#select_sect_id', section);
      await page.selectOption('#select_sect_id', sec.oldValue); //// 例如 HC_1938
      await pause();
  
      // ===== 地號、圖層、查詢 =====
    //   await page.getByRole('textbox', { name: '請輸入地號' }).fill(landNo);
      await page.getByRole('textbox', { name: '請輸入地號' }).fill(landNoNorm);
      await pause(200, 400);
      await page.locator('#mapTile_id').selectOption('EMAP2');
      await pause(200, 400);
      await page.getByRole('link', { name: '查詢' }).click();
  
      // 等表格出現
      await page.waitForSelector('#one-column-emphasis', { timeout: 20000 });
  
      // 關提示/標記框（若有）
      const infoIcon = page.locator('#cada_span_id img');
      if (await infoIcon.isVisible().catch(()=>false)) {
        await infoIcon.click();
        await pause(300, 700);
      }
    //   await page.locator('[id="OpenLayers.Layer.Vector_42_svgRoot"]').click({ trial: true }).catch(()=>{});
    // ★ 改：用穩健的關閉邏輯取代硬編號 svgRoot
      await dismissMapOverlays(page);
  
      // 取表格
      const landInfoJSON = await page.$eval('#one-column-emphasis', (table) => {
        const rows = table.querySelectorAll('tr');
        const result = {};
        rows.forEach(row => {
          const th = row.querySelector('th');
          const td = row.querySelector('td');
          if (th && td && !td.hasAttribute('colspan')) {
            result[th.innerText.trim()] = td.innerText.trim();
          }
        });
        return result;
      });

      // ====== ★★ 這裡開始：動態輸出路徑 + 確保資料夾存在 ★★ ======

        // 將「桃園市 / 復興區」等轉成資料夾安全的小寫 slug
      const slug = s => String(s || '').trim()
        .toLowerCase()
        .replace(/[\s\u3000]/g, '-')          // 空白轉 -
        .replace(/[()（）]/g, '')             // 去括號
        .replace(/[^\w\-一-龥]/g, '');         // 保留中英數、-、底線與中日韓
    
      // 截圖
      // 若你用代碼 (H/13)，也可用對應中文名稱來輸出資料夾；
      // 這裡先直接用你傳入的 city/district 值當 slug
      const citySlug = slug(city || 'taoyuan');
      const distSlug = slug(district || 'fuxing');

      // 用解析後的 sec 與正規化地號當檔名元素
      const filename = `map_${sec.id}_${sec.name}_${landNoNorm}.png`;

      // 組成目錄與檔案路徑
      const outDir = path.resolve(__dirname, 'public', citySlug, distSlug);
      const screenshotPath = path.join(outDir, filename);

      // 確保目錄存在（這行要在組出 screenshotPath 之後）
      fs.mkdirSync(outDir, { recursive: true });

    //   const screenshotPath = path.resolve(
    //     __dirname,
    //     'public',
    //     cityName,
    //     distName,
    //     `map_${section}_${landNo}.png`
    //   );
      //// 截圖
      const mapEl = await page.$('#content_map');
      if (mapEl) {
        await mapEl.screenshot({ path: screenshotPath });
        console.log(`🖼️ 地圖截圖儲存：${screenshotPath}`);
      } else {
        console.log('⚠️ 找不到地圖容器 #content_map');
      }
  
      return {
        city, district,
        section: sec.name,            // 回傳段名（更直觀）
        section_id: sec.id,           // 回傳段號（方便檔名比對）
        landNo: landNoNorm,           // 回傳正規化後的地號
        land_info: landInfoJSON,
        map_image_path: screenshotPath
      };
    } finally {
        // ★ 只在「不是注入」的情況才關瀏覽器
        if (!_browser) {
            await browser.close();
        }
    }
  }
  
  if (require.main === module) {
    scrapeLandInfo().then(result => {
      console.log('✅ 查詢完成：');
      console.log(result);
    }).catch(err => {
      console.error('❌ 查詢失敗：', err);
    });
  }

module.exports= { scrapeLandInfo }