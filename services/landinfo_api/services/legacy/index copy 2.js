/**
 * index.js (Unified: New site default + Old site fallback)
 *
 * ✅ 目標（do what）
 * - 用 Playwright 自動查 EasyMap 地號
 * - 抓「土地文字資料」→ JSON
 * - 抓「地圖畫面」→ 截圖存到 public/<city>/<district>/map_<sectionId>_<sectionName>_<landNo>.png
 * - 支援新站（Z10Web/Normal）與舊站（Index）兩套流程
 * - 支援 BullMQ worker 注入 _browser 重用：避免每個 job 都重開瀏覽器（省時間/省資源）
 *
 * ✅ 為什麼要整合（why）
 * - 舊站會慢慢汰換：所以先用新站當主流程
 * - 但新站還不穩（遮罩 blockUI + canvas 重繪）：所以保留舊站當 fallback，確保服務不中斷
 *
 * ✅ 比喻（why）
 * - 你把它想成「外送員」
 *   - 新路（新站）比較近，但施工多（遮罩、重繪）
 *   - 舊路（舊站）比較慢，但很穩
 *   - auto 模式：先走新路，卡住就改走舊路，確保餐一定送到
 */

// =============================
// A) 基本依賴（do what / why）
// =============================

// do what: Playwright 的瀏覽器控制工具（我們用 chromium 控制網站）
// why: 政府站沒有穩定 API 給你直接拿畫面，只能用瀏覽器自動化做「像人一樣操作」。
const { chromium } = require("playwright");

// do what: 存檔與路徑工具（截圖要寫檔、要建資料夾）
// why: 你要把截圖放到 public，再上傳 R2 或回傳 URL
const fs = require("fs");
const path = require("path");

// do what: 讀 .env
// why: city/district/section/landNo/headless/site 等都可用環境變數控制（worker/服務好部署）
require("dotenv").config({ path: path.resolve(__dirname, "../.env") });


// ==========================================
// B) 舊站專用 helper（do what / why）
// ==========================================

// do what: 把 section 的各種輸入（大利段 / 1938 / HC_1938）統一解析成一個物件
// how: 回傳 { id, name, oldValue } 這種結構
// why: 新站要用「段號 id」、舊站要用「oldValue (HC_1938)」，用同一套解析器最省事
const { resolveOldSection } = require("../helpers/normalizeSections/resolve-old");

// do what: session 管理（舊站用）
// how: 會建立/重用 context + page，並套用 storageState（避免每次都像第一次開站）
// why: worker 長跑時很需要「重用 session」降低失敗率、加快速度
const { ensureSession } = require("../helpers/session/session-helper");

// do what: validate/preload 是你舊站 session helper 的「站點專屬檢查與預載」
// why: 政府站常常要等資源/載入檔案；preload 可提高穩定性，validate 可確認 session 可用
const { validate } = require("../helpers/session/validate-easymap");
const { preload } = require("../helpers/session/preload-easymap");


// ==========================================
// C) 共用小工具（do what / how / why）
// ==========================================

// do what: 偽裝成「真人操作的節奏」
// how: 每一步加一點隨機延遲
// why: 政府站有時候 UI 還在更新，你太快點會撞牆；另外也更像人，降低卡住機率
const pause = (min = 250, max = 900) =>
  new Promise((r) => setTimeout(r, min + Math.random() * (max - min)));

// do what: 確保資料夾存在（沒有就建立）
// why: 截圖存檔時，如果資料夾不存在會直接 throw
const ensureDir = (dir) => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
};

// do what: 把 city/district 變成「適合做資料夾名」的 slug
// how: 轉小寫、空白變 -、移除括號、保留中英數/-/_
// why: 檔案系統不喜歡奇怪字元；你也不希望輸出路徑每次都爆炸
function slug(s) {
  return String(s || "")
    .trim()
    .toLowerCase()
    .replace(/[\s\u3000]/g, "-")
    .replace(/[()（）]/g, "")
    .replace(/[^\w\-一-龥]/g, "");
}

// do what: 地號正規化（你原本那支保留）
// how:
// - 支援 "1306"、"1306-0000"、"01306"
// - 統一成 "1306" 或 "1306-1234"
// why:
// - 舊站對地號格式比較挑；你希望所有輸入都能吃
function normalizeLandNo(input) {
  const s = String(input || "").trim();
  if (!s) return s;
  const m = s.match(/^(\d{1,4})[-~ ]?(\d{0,4})$/);
  if (!m) return s;
  const a = m[1].padStart(4, "0");
  const b = (m[2] || "").padStart(4, "0");
  return b === "0000" ? a : `${a}-${b}`;
}


// ====================================================
// D) 新站穩定器（blockUI + canvas 重繪）
// ====================================================
//
// 新站最常見的問題：
// 1) blockUI 遮罩會蓋住按鈕 → 你點不到（你之前 Timeout 就是這個）
// 2) 你縮放完立刻截圖 → canvas 還沒 repaint，造成「太快截圖」
// 所以要做三件事：等遮罩消失、點擊要能 force、縮放後等重繪

// do what: 等遮罩消失
// how: 找 .blockUI* 這些 overlay，等它 hidden（不存在也 OK）
// why: 遮罩在時，Playwright 會說「intercepts pointer events」導致 click timeout
async function waitForOverlayGone(page, timeoutMs = 30000) {
  const overlay = page.locator(".blockUI.blockOverlay, .blockUI.blockMsg, .blockUI");
  await overlay.first().waitFor({ state: "hidden", timeout: timeoutMs }).catch(() => {});
}

// do what: 安全點擊（先正常點、失敗改 force）
// why: 政府站 UI 疊層很常出現：你看得到但點不到
async function safeClick(locator, page) {
  await waitForOverlayGone(page, 30000);
  try {
    await locator.click({ timeout: 8000 });
  } catch {
    await locator.click({ timeout: 8000, force: true });
  }
  await page.waitForTimeout(150); // why: 給 UI 一點時間完成狀態切換
}

// do what: 等地圖重繪完成（避免太快截圖）
// how:
// - 等 overlay 不在
// - 等 3 次 requestAnimationFrame（讓瀏覽器有機會 repaint canvas）
// - 再保守等 600ms
// why: canvas 的 repaint 不一定跟你點擊同步，你要等它真正畫好才截
async function waitMapStable(page) {
  await waitForOverlayGone(page, 30000);
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.waitForTimeout(600);
}


// ==========================================
// E) 舊站：清掉 OpenLayers 浮層（你的保留）
// ==========================================
//
// do what: 把地圖上 popup/標記關掉，不然會擋截圖或擋操作
// why: OpenLayers 的 popup 常常卡在畫面上，還會吃點擊事件
// how: 依序嘗試：
//  A) 找關閉按鈕
//  B) 點 vector svgRoot（不寫死 id）
//  C) 點地圖空白處
//  D) 最後按 ESC
async function dismissMapOverlays(page) {
  const closers = page.locator(
    ".ol-popup-closer, .ol-popup .ol-close, button[title='Close'], button:has-text('關閉')"
  );
  if (await closers.count()) {
    try {
      await closers.first().click({ timeout: 1200 });
      return;
    } catch {}
  }

  const vectorSvg = page.locator('[id^="OpenLayers.Layer.Vector_"][id$="_svgRoot"]');
  if (await vectorSvg.count()) {
    try {
      await vectorSvg.first().click();
      return;
    } catch {}
  }

  const viewport = page.locator(".ol-viewport, canvas.ol-layer, #map, .map, [class*='ol-map']");
  if (await viewport.count()) {
    try {
      const box = await viewport.first().boundingBox();
      if (box) {
        await page.mouse.click(box.x + 30, box.y + 30);
        return;
      }
      await viewport.first().click();
      return;
    } catch {}
  }

  try {
    await page.keyboard.press("Escape");
  } catch {}
}


// ==========================================
// F) 共用：抓表格文字 → JSON
// ==========================================
//
// do what: 把 table 的 key-value 轉成 JSON
// how: 掃描所有 table tr，取第一格當 key、第二格當 value
// why:
// - 新站 DOM 你還沒固定 selector（先用「通用掃表」比較快能跑）
// - 舊站雖然有 #one-column-emphasis，但你想統一輸出就可以共用這套
async function extractKeyValueFromAllTables(page) {
  return await page.evaluate(() => {
    const kv = {};
    const rows = Array.from(document.querySelectorAll("table tr"));
    for (const tr of rows) {
      const tds = tr.querySelectorAll("td,th");
      if (tds.length >= 2) {
        const k = (tds[0].textContent || "").trim();
        const v = (tds[1].textContent || "").trim();
        if (k && v && k.length <= 30) kv[k] = v;
      }
    }
    return kv;
  });
}

// do what: 白名單挑欄位（你要的核心欄位）
// why:
// - 有些 table 會混入「快速套疊」「位置」「樓層」這種不重要或會變的欄位
// - 你要把 JSON 當資料庫/回 LINE 用，欄位穩才好維護
function pickFields(textJson) {
  const allowKeys = new Set([
    "行政區",
    "地政事務所",
    "地段",
    "地號",
    "面積",
    "使用分區",
    "用地類別",
    "公告現值",
    "公告地價",
    "土地參考資訊",
  ]);
  return Object.fromEntries(Object.entries(textJson).filter(([k]) => allowKeys.has(k)));
}


// =========================================================
// 1) New site implementation (easymap.moi.gov.tw/Z10Web/Normal)
// =========================================================
//
// do what（新站要做的事）
// - 用 codegen 那套流程：關導覽 → 切正射 → 選縣市/區/段/地號 → 查詢
// - 為了讓紅框不被裁：收合側欄 → 縮小兩次 → 展開側欄
// - 等 canvas 重繪 → 截圖 → 抓表格 JSON
//
// why（為什麼這樣）
// - 新站會出現 blockUI 遮罩擋住 click，所以所有 click 都用 safeClick
// - 新站 canvas 重繪有延遲，所以縮放後要 waitMapStable 才截
async function scrapeLandInfoNewSite({ city, district, section, landNo, page, outDir }) {
  // do what: 用同一個 section parser，把「大利段/1938/HC_1938」統一
  // why: 新站需要段號 id，舊站需要 oldValue；統一在這一步最省事
  const sec = resolveOldSection(section || "大利段");
  if (!sec) throw new Error(`(NEW) 找不到段別：${section}`);

  // do what: 新站 landNo 先不做舊站那種 4+4 正規化，因為你目前實測是填 "0382" 這種就能查
  // why: 新站欄位規則可能不同；先「最小改動」讓它跑起來
  const landNoNorm = String(landNo || "").trim();
  if (!landNoNorm) throw new Error("(NEW) landNo is required");

  // do what: 統一輸出檔名規格（跟舊站一致）
  // why: 你之後上傳 R2、或報告引用檔名時，不想分兩套命名
  const filename = `map_${sec.id}_${sec.name}_${landNoNorm}.png`;
  const screenshotPath = path.join(outDir, filename);

  // do what: 打開新站
  // why: 新站入口固定，直接 goto 即可
  await page.goto("https://easymap.moi.gov.tw/Z10Web/Normal", {
    waitUntil: "domcontentloaded",
  });

  // do what: 關閉導覽（有就關，沒有就跳過）
  // why: 導覽 UI 可能會遮住按鈕或吃點擊
  const closeGuide = page.getByRole("button", { name: /關閉導覽/ });
  if (await closeGuide.count()) await safeClick(closeGuide.first(), page);

  // do what: 切到底圖 → 正射影像
  // why: 你想截「正射」背景，對地塊辨識更清楚
  await safeClick(page.getByRole("link", { name: "底圖切換" }), page);
  await safeClick(page.getByRole("link", { name: "正射影像" }), page);

  // do what: 填查詢條件（縣市/鄉鎮/段號/地號）
  // how:
  // - #land_city_id：縣市代碼 (H)
  // - #land_town_id：區代碼 (13)
  // - #land_section_id：段號 (1938/1933...)
  // - #land_landno：地號 (0382)
  // why: 這是新站查詢表單的核心輸入
  await page.locator("#land_city_id").selectOption(city);
  await page.locator("#land_town_id").selectOption(district);
  await page.locator("#land_section_id").selectOption(String(sec.id));
  await page.locator("#land_landno").fill(landNoNorm);

  // do what: 點查詢
  // why: 觸發地圖畫紅框 + 右側表格資料
  await safeClick(page.getByRole("link", { name: "查詢", exact: true }), page);

  // do what: 等 canvas 出現（代表地圖至少已渲染）
  // why: 沒 canvas 就截不到地圖
  await page.locator("canvas").first().waitFor({ state: "visible", timeout: 20000 });

  // do what: 按你指定的 codegen 節點順序操作
  // why:
  // - 收合側邊欄：避免縮放時 UI 擋到地塊
  // - 縮小兩次：讓紅框地塊「完整入鏡」避免被裁切
  // - 再展開：你截 fullPage 時希望側欄也回來（或至少回到你想要的狀態）
  const toggleSidebar = page.getByTitle("收合側邊面板");
  const zoomOut = page.getByRole("button", { name: "−" }).first();

  await safeClick(toggleSidebar, page);
  await safeClick(zoomOut, page);
  await safeClick(zoomOut, page);
  await safeClick(toggleSidebar, page);

  // do what: 等縮放後地圖 repaint
  // why: 不等的話就會「太快截圖」，紅框可能還在舊畫面或還沒完整畫出
  await waitMapStable(page);

  // do what: 截圖
  // why: 你初版要先能用；fullPage 最穩（之後再優化成只截地圖）
  await page.screenshot({ path: screenshotPath, fullPage: true });

  // do what: 抓文字表格 → JSON
  // why: 你要把土地資訊送去 worker 結果、存 DB、或組 LINE Flex
  const textJson = await extractKeyValueFromAllTables(page);
  const cleanText = pickFields(textJson);

  // do what: 回傳統一格式
  // why: 上層不需要知道你到底跑新站或舊站，拿到結果就能用
  return {
    site: "new",
    city,
    district,
    section: sec.name,
    section_id: sec.id,
    landNo: landNoNorm,
    land_info: cleanText,
    map_image_path: screenshotPath,
  };
}


// =========================================================
// 2) Old site implementation (easymap.land.moi.gov.tw/Index)
// =========================================================
//
// do what（舊站要做的事）
// - 用 ensureSession 的 page/context（可以重用 session）
// - 依序選 city -> town -> section（需要等待 option 載入）
// - 填地號、選底圖、查詢
// - 等 #one-column-emphasis 出現（結果表格）
// - 截 #content_map（舊站地圖容器固定）
//
// why（為什麼保留）
// - 新站如果失敗（遮罩/DOM 變）你至少還能用舊站確保服務不中斷
async function scrapeLandInfoOldSite({ city, district, section, landNo, context, page, outDir }) {
  const sec = resolveOldSection(section || "大利段");
  if (!sec) throw new Error(`(OLD) 找不到段別：${section}`);

  // do what: 舊站對 landNo 格式比較挑，所以用 normalizeLandNo
  const landNoNorm = normalizeLandNo(landNo);
  if (!landNoNorm) throw new Error("(OLD) landNo is required");

  const filename = `map_${sec.id}_${sec.name}_${landNoNorm}.png`;
  const screenshotPath = path.join(outDir, filename);

  // do what: 自動允許定位 + 設定預設座標
  // why: 舊站可能會跳定位提示；自動允許可以減少互動阻塞
  await context.grantPermissions(["geolocation"], { origin: "https://easymap.land.moi.gov.tw" });
  await context.setGeolocation({ latitude: 24.786, longitude: 121.29, accuracy: 50 });

  // do what: 清掉浮層
  await dismissMapOverlays(page);

  // do what: 選 city 後等待 town 下拉選單真的載入
  // why: 這是典型「連動下拉」：不等資料回來就選 district 會失敗
  await page.selectOption("#select_city_id", city);
  await Promise.all([
    page
      .waitForResponse((r) => r.url().toLowerCase().includes("town") && r.status() === 200, {
        timeout: 15000,
      })
      .catch(() => {}),
    page.waitForFunction(() => document.querySelector("#select_town_id")?.options.length > 1, {
      timeout: 15000,
    }),
  ]);
  await pause();

  // do what: 選 district 後等待 section 下拉真的載入
  await page.selectOption("#select_town_id", district);
  await Promise.all([
    page
      .waitForResponse((r) => r.url().toLowerCase().includes("section") && r.status() === 200, {
        timeout: 15000,
      })
      .catch(() => {}),
    page.waitForFunction(() => document.querySelector("#select_sect_id")?.options.length > 1, {
      timeout: 15000,
    }),
  ]);
  await pause();

  // do what: 選段（舊站要 oldValue，例如 HC_1938）
  await page.selectOption("#select_sect_id", sec.oldValue);
  await pause();

  // do what: 填地號、選底圖、查詢
  // why:
  // - mapTile_id = EMAP2 是你原本想要的底圖
  // - 查詢後會出現結果表格 + 地圖紅框
  await page.getByRole("textbox", { name: "請輸入地號" }).fill(landNoNorm);
  await pause(200, 400);
  await page.locator("#mapTile_id").selectOption("EMAP2");
  await pause(200, 400);
  await page.getByRole("link", { name: "查詢" }).click();

  // do what: 等結果表格出現
  // why: 有表格才代表查詢真的成功
  await page.waitForSelector("#one-column-emphasis", { timeout: 20000 });

  // do what: 如果有提示 icon，就關掉避免擋畫面
  const infoIcon = page.locator("#cada_span_id img");
  if (await infoIcon.isVisible().catch(() => false)) {
    await infoIcon.click();
    await pause(300, 700);
  }
  await dismissMapOverlays(page);

  // do what: 抓 #one-column-emphasis 的 key-value
  // why: 舊站表格結構穩定，直接針對它抓最乾淨
  const landInfoJSON = await page.$eval("#one-column-emphasis", (table) => {
    const rows = table.querySelectorAll("tr");
    const result = {};
    rows.forEach((row) => {
      const th = row.querySelector("th");
      const td = row.querySelector("td");
      if (th && td && !td.hasAttribute("colspan")) {
        result[th.innerText.trim()] = td.innerText.trim();
      }
    });
    return result;
  });

  // do what: 截地圖容器 #content_map
  // why: 舊站地圖容器固定，截這個比 fullPage 更乾淨
  const mapEl = await page.$("#content_map");
  if (mapEl) {
    await mapEl.screenshot({ path: screenshotPath });
  } else {
    throw new Error("(OLD) 找不到地圖容器 #content_map");
  }

  return {
    site: "old",
    city,
    district,
    section: sec.name,
    section_id: sec.id,
    landNo: landNoNorm,
    land_info: landInfoJSON,
    map_image_path: screenshotPath,
  };
}


// =========================================================
// 3) 對外入口：scrapeLandInfo（新站預設、舊站 fallback）
// =========================================================
//
// do what:
// - 統一對外提供一個函式 scrapeLandInfo()
// - 你 worker/fastapi 只要呼叫它，不用管到底跑新站或舊站
//
// how:
// - site = "new": 只跑新站
// - site = "old": 只跑舊站（用 ensureSession）
// - site = "auto": 先跑新站，失敗就跑舊站（最推薦）
//
// why:
// - 你說舊站會慢慢汰換：所以 new 當主流程
// - 但新站不穩：auto 可保證「服務不中斷」
async function scrapeLandInfo({
  city = process.env.CITY,            // e.g. H
  district = process.env.DISTRICT,    // e.g. 13
  section = process.env.SECTION,      // e.g. 大利段 / 1938 / HC_1938
  landNo = process.env.LANDNO,
  site = process.env.EASYMAP_SITE || "new", // new | old | auto
  _browser,                            // do what: worker 可注入重用 browser
  headless = process.env.HEADLESS !== "false",
} = {}) {
  // do what: 準備資料夾
  // why: 截圖、session state、debug trace 都需要落盤
  ensureDir(path.resolve(__dirname, "./state"));
  ensureDir(path.resolve(__dirname, "./debug"));
  ensureDir(path.resolve(__dirname, "./public"));

  // do what: 根據 city/district 建輸出資料夾
  // why: 讓你檔案好整理（也方便做 R2 key）
  const citySlug = slug(city || "city");
  const distSlug = slug(district || "district");
  const outDir = path.resolve(__dirname, "public", citySlug, distSlug);
  fs.mkdirSync(outDir, { recursive: true });

  // do what: 若外部有注入 _browser 就用（worker 重用），沒有才自己 launch
  // why: 重用瀏覽器可以大幅提升 BullMQ 吞吐量，避免每個 job 都 cold start
  const browser =
    _browser ||
    (await chromium.launch({
      headless,
      args: ["--disable-blink-features=AutomationControlled"],
    }));

  try {
    // ---------------------
    // A) 強制跑舊站
    // ---------------------
    if (site === "old") {
      const { context, page } = await ensureSession(browser, {
        statePath: path.resolve(__dirname, "./state/easymap.json"),
        targetUrl: "https://easymap.land.moi.gov.tw/Index",
        validate,
        preload,
        login: async () => {}, // 舊站無帳密
        headers: {
          "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
          Referer: "https://easymap.land.moi.gov.tw/Index",
        },
        ttlHours: 24,
        timeouts: { gotoMs: 45000 },
        debug: { dir: path.resolve(__dirname, "./debug"), trace: true },
      });

      return await scrapeLandInfoOldSite({
        city,
        district,
        section,
        landNo,
        context,
        page,
        outDir,
      });
    }

    // ---------------------
    // B) 強制跑新站
    // ---------------------
    if (site === "new") {
      const page = await browser.newPage({
        viewport: { width: 1600, height: 1000 },
        deviceScaleFactor: 2,
      });

      return await scrapeLandInfoNewSite({
        city,
        district,
        section,
        landNo,
        page,
        outDir,
      });
    }

    // ---------------------
    // C) auto：先新站，失敗 fallback 舊站
    // ---------------------
    if (site === "auto") {
      try {
        // 先嘗試新站
        const page = await browser.newPage({
          viewport: { width: 1600, height: 1000 },
          deviceScaleFactor: 2,
        });

        return await scrapeLandInfoNewSite({
          city,
          district,
          section,
          landNo,
          page,
          outDir,
        });
      } catch (eNew) {
        // 新站失敗，改走舊站
        const { context, page } = await ensureSession(browser, {
          statePath: path.resolve(__dirname, "./state/easymap.json"),
          targetUrl: "https://easymap.land.moi.gov.tw/Index",
          validate,
          preload,
          login: async () => {},
          headers: {
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            Referer: "https://easymap.land.moi.gov.tw/Index",
          },
          ttlHours: 24,
          timeouts: { gotoMs: 45000 },
          debug: { dir: path.resolve(__dirname, "./debug"), trace: true },
        });

        const rOld = await scrapeLandInfoOldSite({
          city,
          district,
          section,
          landNo,
          context,
          page,
          outDir,
        });

        // do what: 把新站錯誤一起帶回
        // why: 你可以在 worker log 監控「新站壞的頻率」，決定何時能正式移除舊站
        rOld.fallback_from = "new";
        rOld.new_error = String(eNew?.message || eNew);
        return rOld;
      }
    }

    // 任何未支援模式都丟錯
    throw new Error(`Unknown site option: ${site}`);
  } finally {
    // do what: 若不是注入 _browser，才關瀏覽器
    // why: worker 注入時，browser 是共用資源，你關掉會害下一個 job 全掛
    if (!_browser) await browser.close();
  }
}


// =========================================================
// 4) CLI 測試入口（本機 node index.js 直接跑）
// =========================================================
//
// do what: 讓你不用 worker，也能直接用 node 測試
// why: debug 最快（你現在就是用這種方式一直跑）
if (require.main === module) {
  scrapeLandInfo({ site: process.env.EASYMAP_SITE || "new" })
    .then((result) => {
      console.log("✅ 查詢完成：");
      console.log(JSON.stringify(result, null, 2));
    })
    .catch((err) => {
      console.error("❌ 查詢失敗：", err);
      process.exit(1);
    });
}

// do what: 給 worker / 其他模組 import 使用
module.exports = { scrapeLandInfo };
