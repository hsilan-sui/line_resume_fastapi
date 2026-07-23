//引入模組
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
require('dotenv').config({ path: path.resolve(__dirname, '../.env') }); //讀取.env

// 新增：引入 session helper 與站點專屬的 validate/preload

/**
 *  取得土地圖資資訊與地圖截圖
 * ＠params {Object} options
 * @param {string} options.city
 * @param {string} options.district
 * @param {string} options.section
 * @param {string} options.landNo
 */

async function scrapeLandInfo({
    city = process.env.CITY,            // 舊站建議用代碼：桃園市=H
    district = process.env.DISTRICT,    // 復興區=13
    section = process.env.SECTION,      // 可填：大利段 / 1938 / HC_1938
    landNo = process.env.LANDNO,        // ✅ 修正 typo
    _browser,                           // ★ 共用 browser 由 worker 注入
    headless = process.env.HEADLESS !== 'false'
  } = {}) {
  
    // 1) 解析地段
    const sec = resolveOldSection(section || '大利段');
    if (!sec) throw new Error(`找不到段別：${section}（請確認名稱/代碼）`);
  
    const landNoNorm = normalizeLandNo(landNo);
    if (!landNoNorm) throw new Error('缺少 landNo（或格式無法解析）');
  
    console.log('🏙️ 查詢城市：', city, district, section, landNo);
  
    // 確保輸出資料夾存在
    ensureDir(path.resolve(__dirname, './state'));
    ensureDir(path.resolve(__dirname, './debug'));
    ensureDir(path.resolve(__dirname, './public'));
  
    // 若外部有傳 browser 就用；沒有才自己 launch
    const browser = _browser || await chromium.launch({
      headless,
      args: [
        '--no-sandbox',                   // ✅ 容器/雲端必備
        '--disable-dev-shm-usage',        // ✅ 避免 /dev/shm 太小造成 crash
        '--disable-blink-features=AutomationControlled'
      ]
    });
  
    let context, page, reused;
    let needCloseContext = false;
  
    try {
      // ✅ 用 ensureSession 建好的 context/page 繼續操作
      ({ context, page, reused } = await ensureSession(browser, {
        statePath: path.resolve(__dirname, './state/easymap.json'),
        targetUrl: 'https://easymap.land.moi.gov.tw/Index',
        validate,
        preload,
        login: async () => {},
        headers: {
          'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
          'Referer': 'https://easymap.land.moi.gov.tw/Index'
        },
        ttlHours: 24,
        timeouts: { gotoMs: 45000 },
        debug: { dir: path.resolve(__dirname, './debug'), trace: true },
      }));
      console.log('🔐 session reused?', reused);
      needCloseContext = !reused; // ✅ 新 Context 用完要回收；重用 Context 只關 page
  
      // === Geolocation 設定（可留）
      await context.grantPermissions(['geolocation'], { origin: 'https://easymap.land.moi.gov.tw' });
      await context.setGeolocation({ latitude: 24.786, longitude: 121.29, accuracy: 50 });
  
      // === 收干擾浮層
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
      await page.selectOption('#select_sect_id', sec.oldValue);
      await pause();
  
      // ===== 地號、圖層、查詢 =====
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
  
      // ====== 動態輸出路徑 + 確保資料夾存在 ======
      const slug = s => String(s || '').trim()
        .toLowerCase()
        .replace(/[\s\u3000]/g, '-')
        .replace(/[()（）]/g, '')
        .replace(/[^\w\-一-龥]/g, '');
  
      const citySlug = slug(city || 'taoyuan');
      const distSlug = slug(district || 'fuxing');
      const filename = `map_${sec.id}_${sec.name}_${landNoNorm}.png`;
      const outDir = path.resolve(__dirname, 'public', citySlug, distSlug);
      const screenshotPath = path.join(outDir, filename);
      fs.mkdirSync(outDir, { recursive: true });
  
      const mapEl = await page.$('#content_map');
      if (mapEl) {
        await mapEl.screenshot({ path: screenshotPath });
        console.log(`🖼️ 地圖截圖儲存：${screenshotPath}`);
      } else {
        console.log('⚠️ 找不到地圖容器 #content_map');
      }
  
      return {
        city, district,
        section: sec.name,
        section_id: sec.id,
        landNo: landNoNorm,
        land_info: landInfoJSON,
        map_image_path: screenshotPath
      };
    } finally {
      // ✅ 每個 job 的收尾策略
      try { if (page)    await page.close(); } catch {}
      try {
        if (needCloseContext && context) {   // 只有「新建的」context 需要收
          await context.close();
        }
      } catch {}
      // ✅ 只有在「沒有注入」的情況才關瀏覽器（單檔測試時）
      if (!_browser) {
        try { await browser.close(); } catch {}
      }
    }
  }
  

if (require.main === module) {
    scrapeLandInfo().then(result => {
      console.log("✅ 查詢完成：");
      console.log(result);
    }).catch(err => {
      console.error("❌ 查詢失敗：", err);
    });
  }