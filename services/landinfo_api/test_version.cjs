const { chromium } = require("playwright");

async function waitForOverlayGone(page, timeoutMs = 30000) {
  const overlay = page.locator(".blockUI.blockOverlay, .blockUI.blockMsg, .blockUI");
  // overlay 可能不存在，所以 catch
  await overlay.first().waitFor({ state: "hidden", timeout: timeoutMs }).catch(() => {});
}

async function safeClick(locator, page) {
  await waitForOverlayGone(page, 30000);
  // 先正常點，失敗再 force（避免被 overlay/其他元素擋）
  try {
    await locator.click({ timeout: 8000 });
  } catch {
    await locator.click({ timeout: 8000, force: true });
  }
  await page.waitForTimeout(150);
}

// ✅ 等地圖真的重繪完再截圖（解你說的「太快截圖」）
async function waitMapStable(page) {
  // 先確保遮罩不在
  await waitForOverlayGone(page, 30000);

  // 等幾個 animation frame，讓 canvas 有機會 repaint
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => r())));

  // 政府站偶爾渲染慢，再保守等一下
  await page.waitForTimeout(600);
}

async function main() {
  const browser = await chromium.launch({ headless: false });

  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    deviceScaleFactor: 2,
  });

  await page.goto("https://easymap.moi.gov.tw/Z10Web/Normal", {
    waitUntil: "domcontentloaded",
  });

  // codegen 風格：關閉導覽
  const closeGuide = page.getByRole("button", { name: /關閉導覽/ });
  if (await closeGuide.count()) await safeClick(closeGuide.first(), page);

  // codegen 風格：切底圖 → 正射影像
  await safeClick(page.getByRole("link", { name: "底圖切換" }), page);
  await safeClick(page.getByRole("link", { name: "正射影像" }), page);

  // codegen 風格：輸入查詢
  await page.locator("#land_city_id").selectOption("H");
  await page.locator("#land_town_id").selectOption("13");
  await page.locator("#land_section_id").selectOption("1933"); //1939
  await page.locator("#land_landno").fill("0382"); //0524

  // 查詢
  await safeClick(page.getByRole("link", { name: "查詢", exact: true }), page);

  // 等地圖 canvas 出現
  await page.locator("canvas").first().waitFor({ state: "visible", timeout: 20000 });

  // ✅ 你要的 codegen 節點順序（補丁）
  const toggleSidebar = page.getByTitle("收合側邊面板");
  const zoomOut = page.getByRole("button", { name: "−" }).first();

  await safeClick(toggleSidebar, page);
  await safeClick(zoomOut, page);
  await safeClick(zoomOut, page);
  await safeClick(toggleSidebar, page);

  // ✅ 關鍵：等地圖縮放後重繪完成，再截圖（不然會「太快截圖」）
  await waitMapStable(page);

  // 截圖
  const screenshotPath = "parcel.png";
  await page.screenshot({ path: screenshotPath, fullPage: true });

  // 文字資料 → JSON
  const textJson = await page.evaluate(() => {
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
  const cleanText = Object.fromEntries(Object.entries(textJson).filter(([k]) => allowKeys.has(k)));

  console.log(
    JSON.stringify(
      {
        query: { city: "H", town: "13", sectionId: "1938", landNo: "1306" },
        screenshotPath,
        text: cleanText,
        ts: new Date().toISOString(),
      },
      null,
      2
    )
  );

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
