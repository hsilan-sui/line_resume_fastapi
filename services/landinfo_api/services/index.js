/**
 * index.js (New site only, supports sectionId OR section name)
 *
 * ✅ do what
 * - Playwright 自動操作新版地籍便民系統（Z10Web/Normal）
 * - 支援輸入：city + district(townCode) + (sectionId 或 sectionName) + landNo
 * - 查詢後抓土地文字表格 => JSON
 * - 地圖縮放調整避免紅框地塊被裁切
 * - 等地圖重繪後截圖，存到 public/<city>/<district>/...
 *
 * ✅ how
 * - sectionId 優先；沒有就用 resolveSection() 從你的「全國段名清單」解析出 sectionId
 * - 所有 click 都走 safeClick：避免 blockUI overlay 擋點擊
 * - 縮放後用 waitMapStable：避免 canvas 尚未 repaint 就截圖
 *
 * ✅ why
 * - 新站查詢必須用 numeric sectionId
 * - LINE 使用者通常輸入段名，所以要有段名 -> 段號解析器（你已經有全國資料）
 */

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../.env") });

// ✅ 你自己的「全國段名解析器」：用 city + townCode + section(段名/段號) 找到 sectionId
// 期望回傳格式（你可以在 resolver 裡統一）
// { sectionId: "1938", sectionName: "大利段", officeCode: "HC", ... }
const { resolveSection } = require("./helpers/sections/resolve-section");

// -----------------------------
// 小工具：確保資料夾存在
// -----------------------------
function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

// -----------------------------
// 小工具：把 city/district 變成資料夾安全字串
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
// -----------------------------
async function waitForOverlayGone(page, timeoutMs = 30000) {
  const overlay = page.locator(".blockUI.blockOverlay, .blockUI.blockMsg, .blockUI");
  await overlay.first().waitFor({ state: "hidden", timeout: timeoutMs }).catch(() => {});
}

// -----------------------------
// 安全點擊：先等 overlay，再 click；失敗就 force click
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
// 切換底圖到正射影像
// -----------------------------
async function switchToPhotoBasemap(page) {
  await waitForOverlayGone(page, 30000);

  const changed = await page.evaluate(() => {
    const select = document.getElementById("1_baseLayer_sel");
    if (!select) return false;
    select.value = "PHOTO_MIX";
    select.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  });

  if (changed) {
    await waitMapStable(page);
    return;
  }

  const trigger = page.locator('a.btn-triger[title="底圖切換"]').first();
  const photoButton = page.locator('a.btn-subtool[title="正射影像"]').first();

  try {
    if (await trigger.count()) {
      await safeClick(trigger, page);
      await photoButton.waitFor({ state: "visible", timeout: 5000 });
      await safeClick(photoButton, page);
      await waitMapStable(page);
      return;
    }
  } catch (e) {
    console.warn("[basemap] floating button failed, fallback to select:", e?.message || e);
  }

  throw new Error("cannot find basemap controls for photo layer");
}

// -----------------------------
// 等地圖重繪穩定再截圖（避免太快截到舊畫面）
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
  city = process.env.CITY,                 // 例：H 或 桃園市（由 resolveSection 內部決定怎麼處理）
  district = process.env.DISTRICT,         // 例：13（townCode）
  sectionId = process.env.SECTION_ID,      // 可選：1938（最快）
  section = process.env.SECTION,           // 可選：大利段（最友善）
  landNo = process.env.LANDNO,             // 例：1306 / 0382
  _browser,
  headless = process.env.HEADLESS !== "false",
} = {}) {
  if (!city) throw new Error("city is required");
  if (!district) throw new Error("district is required");
  if (!landNo) throw new Error("landNo is required");

  // -----------------------------
  // 1) 解析段號 resolvedSectionId（sectionId 優先，否則用全國段名清單解析）
  // -----------------------------
  let resolvedSectionId = sectionId ? String(sectionId).trim() : "";

  if (!resolvedSectionId) {
    const sec = resolveSection({
      city,                    // H 或 桃園市
      townCode: String(district), // 13
      section,                 // 大利段 or 1938
    });

    // 兼容不同 key 命名：sectionId / id
    resolvedSectionId = String(sec?.sectionId || sec?.id || "").trim();
    if (!resolvedSectionId) {
      throw new Error(
        `sectionId is required: cannot resolve from section="${section}" (city=${city}, townCode=${district})`
      );
    }
  }

  // -----------------------------
  // 2) 輸出路徑
  // -----------------------------
  ensureDir(path.resolve(__dirname, "./public"));
  const citySlug = slug(city);
  const distSlug = slug(district);
  const outDir = path.resolve(__dirname, "public", citySlug, distSlug);
  ensureDir(outDir);

  const landNoNorm = String(landNo).trim();
  const filename = `map_${resolvedSectionId}_${landNoNorm}.png`;
  const screenshotPath = path.join(outDir, filename);

  // -----------------------------
  // 3) browser 可注入（worker 重用）
  // -----------------------------
  const browser =
    _browser ||
    (await chromium.launch({
      headless,
      args: ["--disable-blink-features=AutomationControlled"],
    }));

  let page; //browser 共享是對的，但 page 不能共享、也不能不關，否則會一直堆。
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
    await switchToPhotoBasemap(page);

    // -----------------------------
    // 5) 填查詢條件
    // -----------------------------
    await page.locator("#land_city_id").selectOption(String(city));
    await page.locator("#land_town_id").selectOption(String(district));
    await page.locator("#land_section_id").selectOption(String(resolvedSectionId));
    await page.locator("#land_landno").fill(landNoNorm);

    // 查詢
    await safeClick(page.getByRole("link", { name: "查詢", exact: true }), page);

    // 等地圖 canvas 出現
    await page.locator("canvas").first().waitFor({ state: "visible", timeout: 20000 });

    // -----------------------------
    // 6) codegen 節點順序：收合 → 縮小兩次 → 展開
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

    const publicRelPath = `/public/${citySlug}/${distSlug}/${filename}`;

    // 你可以先用 env，沒有就 fallback localhost
    const baseUrl = process.env.PUBLIC_BASE_URL || "http://127.0.0.1:3001";

    return {
      site: "new",
      query: {
        city: String(city),
        district: String(district),
        sectionId: String(resolvedSectionId),
        landNo: String(landNoNorm),
      },
      land_info: landInfo,
      // 保留本機路徑（debug 用）
      map_image_path: screenshotPath,

      // ✅ 新增：給前端/LINE 用的 URL
      map_image_url: `${baseUrl}${publicRelPath}`,
      ts: new Date().toISOString(),
    };
  } finally {
    try { await page?.close(); } catch {}
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
