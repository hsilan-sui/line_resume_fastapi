// index.js (New site only, but supports sectionId OR section name)
// 目標：用 Playwright 自動操作「新版地政便民系統」
// 1) 輸入縣市/鄉鎮/段號/地號
// 2) 查詢後抓土地文字表格 => JSON
// 3) 地圖縮放調整，確保紅色地塊不被裁切
// 4) 等地圖重繪完成後截圖，存到 public/<city>/<district>/...

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../.env") });

// ✅ 用你舊站既有的段名解析器（超重要）
// do what: 讓你可以丟「大利段」也能自動算出 sectionId=1938
// why: LINE 使用者輸入通常是段名，不會記段號
// const { resolveOldSection } = require("./helpers/normalizeSections/resolve-old");
const { resolveSection } = require("../helpers/sections/resolve-section");

const sec = resolveSection({
  city,              // H 或 桃園市
  townCode: district, // 13
  section,           // 大利段 or 1938
});

const resolvedSectionId = sectionId || sec?.sectionId;


// -----------------------------
// 小工具：確保資料夾存在
// do what: 保證輸出路徑存在
// how: 如果不存在就 recursive mkdir
// why: 截圖寫檔前沒資料夾會直接失敗
// -----------------------------
function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

// -----------------------------
// 小工具：把 city/district 變成資料夾安全字串
// do what: 產生可當資料夾名稱的 slug
// how: 去空白、轉小寫、移除不合法字元
// why: 避免檔名限制或特殊符號造成寫檔失敗
// -----------------------------
function slug(s) {
  return String(s || "")
    .trim()
    .toLowerCase()
    .replace(/[\s\u3000]/g, "-")
    .replace(/[()（）]/g, "")
    .replace(/[^\w\-一-龥]/g, "");
}

// -----------------------------
// 新站常見問題：blockUI overlay 擋住 click
// do what: 等 overlay 消失
// how: 等 .blockUI.* hidden（可能不存在就 catch）
// why: 遮罩會攔截 click（intercepts pointer events）
// -----------------------------
async function waitForOverlayGone(page, timeoutMs = 30000) {
  const overlay = page.locator(".blockUI.blockOverlay, .blockUI.blockMsg, .blockUI");
  await overlay.first().waitFor({ state: "hidden", timeout: timeoutMs }).catch(() => {});
}

// -----------------------------
// 安全點擊：先等 overlay，再 click；失敗就 force click
// do what: 提高 click 成功率
// how: normal click -> catch -> force click
// why: UI 疊層常見「看得到但點不到」
// -----------------------------
async function safeClick(locator, page) {
  await waitForOverlayGone(page, 30000);
  try {
    await locator.click({ timeout: 8000 });
  } catch {
    await locator.click({ timeout: 8000, force: true });
  }
  await page.waitForTimeout(150);
}

// -----------------------------
// 等地圖重繪穩定再截圖
// do what: 避免截到縮放前/半渲染畫面
// how: overlay gone + 3 個 animation frame + sleep 600ms
// why: canvas/webgl 渲染非同步，不等會「太快截圖」
// -----------------------------
async function waitMapStable(page) {
  await waitForOverlayGone(page, 30000);
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.waitForTimeout(600);
}

// -----------------------------
// 把頁面上所有 table 的 key/value 抓成 JSON
// do what: 把「土地資訊表格」轉成 {欄位:值}
// how: 掃描 table tr，取第一格當 key、第二格當 value
// why: 新站 selector 可能變，掃全 table 更耐用
// -----------------------------
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

// -----------------------------
// 白名單欄位：只保留你真正想要的資料
// do what: 避免抓到 UI 雜訊欄位
// how: allowKeys filter
// why: 輸出 JSON 穩定，後續給 FastAPI / DB / LINE Flex 好維護
// -----------------------------
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
// Public API: scrapeLandInfo (new site only)
// =========================================================
async function scrapeLandInfo({
  city = process.env.CITY,                 // H
  district = process.env.DISTRICT,         // 13
  sectionId = process.env.SECTION_ID,      // 可選：1938（最快）
  section = process.env.SECTION,           // 可選：大利段（最友善）
  landNo = process.env.LANDNO,             // 1306 / 0382
  _browser,
  headless = process.env.HEADLESS !== "false",
} = {}) {
  // -----------------------------
  // 1) 參數決策：sectionId / section
  // do what: 讓你「兩種輸入都能跑」
  // how:
  // - 有 sectionId 就直接用
  // - 沒有 sectionId 但有 section → resolveOldSection(section).id
  // why: 你的 LINE/前端常輸入段名，但系統查詢需要段號
  // -----------------------------
  let resolvedSectionId = sectionId ? String(sectionId).trim() : "";

  if (!resolvedSectionId) {
    const sec = resolveOldSection(section || "");
    if (sec?.id) resolvedSectionId = String(sec.id);
  }

  if (!city) throw new Error("city is required");
  if (!district) throw new Error("district is required");
  if (!resolvedSectionId) {
    throw new Error("sectionId is required (provide SECTION_ID or SECTION/section name)");
  }
  if (!landNo) throw new Error("landNo is required");

  // -----------------------------
  // 2) 輸出路徑
  // do what: public/<city>/<district>/map_<sectionId>_<landNo>.png
  // why: 讓你後面上傳 R2 / 回傳 URL 很一致
  // -----------------------------
  ensureDir(path.resolve(__dirname, "./public"));
  const citySlug = slug(city);
  const distSlug = slug(district);
  const outDir = path.resolve(__dirname, "public", citySlug, distSlug);
  ensureDir(outDir);

  const filename = `map_${resolvedSectionId}_${String(landNo).trim()}.png`;
  const screenshotPath = path.join(outDir, filename);

  // -----------------------------
  // 3) browser 可注入（worker 重用）
  // do what: 沒傳入才 launch
  // why: BullMQ 每個 job 重開瀏覽器很慢
  // -----------------------------
  const browser =
    _browser ||
    (await chromium.launch({
      headless,
      args: ["--disable-blink-features=AutomationControlled"],
    }));

  try {
    const page = await browser.newPage({
      viewport: { width: 1600, height: 1000 },
      deviceScaleFactor: 2,
    });

    // -----------------------------
    // 4) 進新站
    // -----------------------------
    await page.goto("https://easymap.moi.gov.tw/Z10Web/Normal", {
      waitUntil: "domcontentloaded",
    });

    // 可能會跳導覽：有就關
    const closeGuide = page.getByRole("button", { name: /關閉導覽/ });
    if (await closeGuide.count()) await safeClick(closeGuide.first(), page);

    // 底圖切換 → 正射影像
    await safeClick(page.getByRole("link", { name: "底圖切換" }), page);
    await safeClick(page.getByRole("link", { name: "正射影像" }), page);

    // -----------------------------
    // 5) 填查詢條件
    // do what: 選縣市/鄉鎮/段號 + 填地號
    // why: 這是觸發紅框與表格資料的必要輸入
    // -----------------------------
    await page.locator("#land_city_id").selectOption(String(city));
    await page.locator("#land_town_id").selectOption(String(district));
    await page.locator("#land_section_id").selectOption(String(resolvedSectionId));
    await page.locator("#land_landno").fill(String(landNo));

    // 查詢
    await safeClick(page.getByRole("link", { name: "查詢", exact: true }), page);

    // 等地圖 canvas 出現
    await page.locator("canvas").first().waitFor({ state: "visible", timeout: 20000 });

    // -----------------------------
    // 6) 你指定的 codegen 節點順序：收合 → 縮小兩次 → 展開
    // why: 讓紅框地塊完整入鏡，不要被裁切
    // -----------------------------
    const toggleSidebar = page.getByTitle("收合側邊面板");
    const zoomOut = page.getByRole("button", { name: "−" }).first();

    await safeClick(toggleSidebar, page);
    await safeClick(zoomOut, page);
    await safeClick(zoomOut, page);
    await safeClick(toggleSidebar, page);

    // 等縮放後地圖重繪
    await waitMapStable(page);

    // 截圖（先 fullPage）
    await page.screenshot({ path: screenshotPath, fullPage: true });

    // 抓土地文字資料
    const rawText = await extractKeyValueFromAllTables(page);
    const landInfo = pickFields(rawText);

    return {
      site: "new",
      query: {
        city: String(city),
        district: String(district),
        sectionId: String(resolvedSectionId),
        landNo: String(landNo),
      },
      land_info: landInfo,
      map_image_path: screenshotPath,
      ts: new Date().toISOString(),
    };
  } finally {
    if (!_browser) await browser.close();
  }
}

// CLI 測試入口
if (require.main === module) {
  scrapeLandInfo()
    .then((result) => {
      console.log("✅ 查詢完成：");
      console.log(JSON.stringify(result, null, 2));
    })
    .catch((err) => {
      console.error("❌ 查詢失敗：", err);
      process.exit(1);
    });
}

module.exports = { scrapeLandInfo };
