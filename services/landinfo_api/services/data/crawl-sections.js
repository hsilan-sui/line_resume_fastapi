//做「段名很大截不到全圖」那種情境（需要自動調整比例尺再截圖），可以在現有流程後面加一個「定位段名 → 檢查畫布覆蓋率 → 逐級縮放直到完整入鏡」的小模組，直接銜接這份程式
/**
 * 爬取「內政部國土測繪圖資服務 - 地籍便民系統」的「段名清單」
 * 流程：
 *   1) 進入 Z10Web/Normal 頁面，關閉導覽視窗（若有）
 *   2) 讀取全國「縣市」下拉選單（#land_city_id）
 *   3) 逐一選取縣市 → 等待系統以 POST 打 TOWN_API 回傳鄉鎮清單
 *   4) 讀取該縣市的「鄉鎮市區」下拉選單（#land_town_id）
 *   5) 逐一選取鄉鎮 → 等待系統以 POST 打 SECTION_API 回傳段名清單
 *   6) 以 JSON 輸出：
 *        - 每個鄉鎮一個檔（<城市>/<鄉鎮>.json）
 *        - 每個城市聚合檔（<城市>/_city-<城市>.json）
 *        - 全國聚合檔（out/all-sections.json）
 *
 * 設計重點：
 *   - 使用 waitForResponse 監聽 POST API，以確保抓到最新資料
 *   - 仍搭配 DOM 重試與小延遲，避免快取或渲染延遲造成的空資料
 *   - 手機版 UA：部分站台會依 UA 調整載入模式；此處沿用既有設定
 *   - 所有錯誤以「不中斷主流程」為優先，盡量寫出可用的 JSON 檔
 */

const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');

// === 站台與 API 端點 ===
const BASE = 'https://easymap.land.moi.gov.tw';
const PAGE_URL = `${BASE}/Z10Web/Normal`;                 // 入口頁
const TOWN_API = `${BASE}/Z10Web/City_json_getTownList`;   // 選縣市後，伺服器回傳「鄉鎮清單」的 POST API
const SECTION_API = `${BASE}/Z10Web/City_json_getSectionList`; // 選鄉鎮後，伺服器回傳「段名清單」的 POST API

// === 檔案輸出設定 ===
const OUT_DIR = './out';    // 會輸出在 out/ 目錄底下

// === 節流 / 重試設定（依實測可調） ===
const DELAY_MS = 200;       // 每步驟基礎延遲（防抖動、防畫面尚未完成）
const RETRIES = 12;         // 讀取下拉選單 options 的最大重試次數
const STEP   = 300;         // 兩次重試間的等待間隔（毫秒）

// 小工具：睡眠
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// 小工具：安全檔名（移除 OS 不允許的字元）
const safe = s => String(s || '').replace(/[\\/:*?"<>|]/g, '_');

/**
 * 讀取 <select> 的 <option> 清單（在瀏覽器端執行）
 * @param {import('playwright').Page} page
 * @param {string} selector - 例如 '#land_city_id'
 * @returns {Promise<Array<{value:string, text:string}>>}
 */
async function getOptions(page, selector) {
  return await page.$eval(selector, sel => {
    return Array.from(sel.querySelectorAll('option'))
      .map(o => ({ value: (o.value || '').trim(), text: (o.textContent || '').trim() }))
      // 過濾「請選擇」等空白/提示項
      .filter(o => o.value && !/請選擇/.test(o.text));
  });
}

/**
 * 帶重試的 <select> options 讀取
 * - 有些站台會因載入/渲染延遲導致 options 尚未到位，這裡做線性重試
 * @param {import('playwright').Page} page
 * @param {string} selector
 * @param {number} wantMin - 預期至少要幾個 options（預設 1）
 * @returns {Promise<Array<{value:string, text:string}>>}
 */
async function readOptionsWithRetry(page, selector, wantMin = 1) {
  for (let i = 0; i < RETRIES; i++) {
    try {
      const opts = await getOptions(page, selector);
      if (opts.length >= wantMin) return opts; // 足夠就回傳
    } catch {}
    await sleep(STEP); // 沒抓到就等一下再試
  }
  // 最後再嘗試一次，仍失敗就回空陣列，交由呼叫端決策
  try { return await getOptions(page, selector); } catch { return []; }
}

/**
 * 若頁面有「導覽說明」(guide modal)，嘗試關閉
 * - 直接用 locator.count() 判斷，避免對 Locator 使用 try/catch
 */
async function closeGuideIfAny(page) {
  try {
    // 等待導覽彈窗可見（若沒有會 timeout，被 catch 吃掉）
    await page.waitForSelector('#guideModal', { state: 'visible', timeout: 1500 });
  } catch (_) {}
  // 嘗試用 ARIA role 找「關閉導覽」按鈕
  const btn = page.getByRole('button', { name: /關閉導覽/ });
  if (await btn.count() > 0) {
    await btn.first().click().catch(()=>{});
    await sleep(200);
    return;
  }
  // 後備選項：找 data-bs-dismiss="modal" 的按鈕
  const fb = page.locator('#guideModal [data-bs-dismiss="modal"], #guideModal button');
  if (await fb.count() > 0) {
    await fb.first().click().catch(()=>{});
    await sleep(200);
  }
}

/**
 * 人工觸發 <select> 的 change/input 事件
 * - 有些框架（例如舊版 Vue/React/原生監聽）需要事件才會發後續 AJAX
 */
async function fireChange(page, selector) {
  await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return;
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('input',  { bubbles: true }));
  }, selector);
}

async function main() {
  // 確保輸出資料夾存在
  await fs.ensureDir(OUT_DIR);

  // 啟動瀏覽器（headless 模式）
  const browser = await chromium.launch({ headless: true });

  // 建立瀏覽情境，這邊使用手機 UA（沿用原設定）
  const ctx = await browser.newContext({
    userAgent:
      'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36'
  });
  const page = await ctx.newPage();

  console.log('→ 開啟頁面…', PAGE_URL);
  await page.goto(PAGE_URL, { waitUntil: 'domcontentloaded' });

  // 若有導覽彈窗先關掉，避免擋住操作
  await closeGuideIfAny(page);

  // 頁面中兩個核心下拉選單
  const citySel = '#land_city_id'; // 縣市
  const townSel = '#land_town_id'; // 鄉鎮市區

  // 1) 讀全國縣市（value 會是 A/C/F/H… 等代碼）
  let cities = await readOptionsWithRetry(page, citySel, 10 /* 至少 10 個才合理 */);
  if (!cities.length) throw new Error('縣市選單沒抓到');
  console.log(`縣市數：${cities.length}`);

  const allNation = []; // 全國聚合（所有段名）

  // 2) 逐縣市處理
  for (const city of cities) {
    console.log(`\n→ 城市：${city.text}（code=${city.value}）`);

    // 預先掛一個等待：當我們 select 縣市時，網站應該會以 POST 打 TOWN_API
    // 這裡先等，等不到（例如快取/瞬間完成）也不導致中斷
    const waitTown = page.waitForResponse(
      r => r.url().startsWith(TOWN_API) && r.request().method() === 'POST' && r.ok(),
      { timeout: 15000 }
    ).catch(() => null);

    // 觸發縣市變更 → 以便站台載入鄉鎮
    await page.selectOption(citySel, city.value).catch(()=>{});
    await fireChange(page, citySel);
    await waitTown;        // 盡量等 POST 完成（若站台使用快取，這裡可能拿不到 response）
    await sleep(DELAY_MS); // 再緩一點，給前端把 DOM 填好

    // 讀該縣市的「鄉鎮市區」清單（用重試機制兜底）
    const towns = await readOptionsWithRetry(page, townSel, 1);
    console.log(`  鄉鎮市區數：${towns.length}`);

    // 為該縣市準備輸出資料夾與聚合陣列
    const cityDir = path.join(OUT_DIR, safe(city.text));
    await fs.ensureDir(cityDir);
    const cityAgg = []; // 該市所有段名

    // 3) 逐鄉鎮處理
    for (const town of towns) {
      await sleep(DELAY_MS); // 每輪稍微降速，減輕站台壓力

      // 預先等待 SECTION_API：選鄉鎮後，站台會以 POST 回傳段名清單
      const waitSec = page.waitForResponse(
        r => r.url().startsWith(SECTION_API) && r.request().method() === 'POST' && r.ok(),
        { timeout: 20000 }
      ).catch(() => null);

      // ⚠️ 有些站在切縣市時會刷新鄉鎮列表；為穩定起見，每次都確認「縣市→鄉鎮」連續選取
      await page.selectOption(citySel, city.value).catch(()=>{});
      await fireChange(page, citySel);
      await page.selectOption(townSel, town.value).catch(()=>{});
      await fireChange(page, townSel);

      let sections = [];
      try {
        const res = await waitSec; // 可能是 null（例如快取很快、或事件已發生）
        if (res) {
          // 後端回傳通常為陣列，每個元素包含 id/name/officeCode/townCode 等
          const json = await res.json();
          if (Array.isArray(json)) {
            sections = json.map(s => ({
              id: String(s.id ?? ''),
              name: String(s.name ?? ''),
              officeCode: String(s.officeCode ?? ''),
              townCode: String(s.townCode ?? ''),
              cityName: city.text,
              townName: town.text
            }));
          }
        }
      } catch (e) {
        // 解析失敗就讓 sections 留空，下面還有延遲兜底
      }

      // 有些站點：即便 API 回來了，DOM/內部狀態更新仍需時間；再等一下以提升成功率
      if (!sections.length) await sleep(400);

      // 4) 寫出「鄉鎮」級 JSON：<out>/<城市>/<鄉鎮>.json
      const fpath = path.join(cityDir, `${safe(town.text)}.json`);
      await fs.writeJson(fpath, sections, { spaces: 2 });
      console.log(`  ✓ ${city.text}/${town.text} → ${sections.length} 筆`);

      // 聚合到該市與全國
      cityAgg.push(...sections);
      allNation.push(...sections);
    }

    // 5) 寫該城市的聚合檔：<out>/<城市>/_city-<城市>.json
    const fcity = path.join(cityDir, `_city-${safe(city.text)}.json`);
    await fs.writeJson(fcity, cityAgg, { spaces: 2 });
    console.log(`→ 存檔：${fcity}（${cityAgg.length} 筆）`);
  }

  // 6) 最後輸出全國聚合檔：out/all-sections.json
  const allFile = path.join(OUT_DIR, `all-sections.json`);
  await fs.writeJson(allFile, allNation, { spaces: 2 });
  console.log(`\n✅ 全國完成：${allFile}（共 ${allNation.length} 筆）`);

  await browser.close();
}

// 入口：發生例外時印出錯誤並以非 0 結束碼退出（方便 CI 監控）
main().catch(err => {
  console.error('❌ 錯誤：', err);
  process.exit(1);
});
