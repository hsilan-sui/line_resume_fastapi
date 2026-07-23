// server.js (派工版：enqueue only)
/**
 * ✅ do what
 * - 提供 HTTP API：POST /scrape
 * - 轉呼叫 scrapeLandInfo() 跑 Playwright
 *
 * ✅ how
 * - Express + JSON body
 * - 回傳 scrapeLandInfo 結果
 *
 * ✅ why
 * - FastAPI 不跑瀏覽器，改由 Node 微服務專心處理 Playwright
 */
console.log("🔥 RUNNING FILE:", __filename);

const express = require("express");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../.env") });

const { crawlQueue } = require("./queue"); // 你 queue.js export crawlQueue
// const { scrapeLandInfo } = require("./index"); // 你的 index.js
const { requireJobToken } = require("./src/middlewares/jobAuth");
const { rateLimitByUserId } = require("./src/middlewares/rateLimitRedis");

const app = express();

// ✅ do what: 把本機資料夾 public/ 變成可被 HTTP 讀到的靜態網址
// how: express.static 指到 public 資料夾
// why: LINE / 前端都需要「URL」，不能用本機路徑
app.use("/public", express.static(path.join(__dirname, "public")));

app.use(express.json({ limit: "1mb" }));

// 健康檢查
app.get("/health", (req, res) => {
    res.json({
      ok: true,
      service: "landinfo-node_sui",
      file: __filename,
      pid: process.pid,
      ts: new Date().toISOString(),
    });
  });
  

// app.get("/jobs",  (req, res) => {
//     console.log("[/jobs] hit");
//     console.log("[/jobs] body =", req.body);

  
//     // ✅ 立刻回覆，避免 webhook 卡住
//     return res.json({ ok: true, jobId: job.id, traceId });
//   });


app.post("/jobs",requireJobToken, rateLimitByUserId(),  async (req, res) => {
    console.log("[/jobs] hit");
    console.log("[/jobs] body =", req.body);
    const { city, district, section, landNo, userId } = req.body || {};
    if (!userId) return res.status(400).json({ message: "userId is required" });
    if (!city || !district || !landNo) return res.status(400).json({ message: "city/district/landNo required" });
  
    const traceId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  
    const job = await crawlQueue.add("crawl", {
      city, district, section, landNo,
      userId,           // ✅ 關鍵：一定要帶
      traceId
    });
  
    // ✅ 立刻回覆，避免 webhook 卡住
    return res.json({ ok: true, jobId: job.id, traceId });
  });

const PORT = Number(process.env.NODE_LANDINFO_PORT || 3001);
app.listen(PORT, () => {
  console.log(`✅ landinfo-node listening on http://127.0.0.1:${PORT}`);
});


/**
 * POST /scrape
 * body:
 * {
 *   city: "H" or "桃園市",
 *   district: "13",
 *   sectionId?: "1938",
 *   section?: "大利段",
 *   landNo: "1306" or "1306-0000",
 *   headless?: true/false
 * }
 */
//本機測試用
// app.post("/scrape", async (req, res) => {
//   try {
//     const {
//       city,
//       district,
//       sectionId,
//       section,
//       landNo,
//       headless,
//     } = req.body || {};

//     // 最小防呆（真正解析 sectionId 你已在 index.js 內處理）
//     if (!city) return res.status(400).json({ message: "city is required" });
//     if (!district) return res.status(400).json({ message: "district is required" });
//     if (!landNo) return res.status(400).json({ message: "landNo is required" });

//     const result = await scrapeLandInfo({
//       city,
//       district,
//       sectionId,
//       section,
//       landNo,
//       headless: typeof headless === "boolean" ? headless : undefined,
//     });

//     // ✅ 先回本機檔案路徑（下一步再改成回傳 URL）
//     return res.json(result);
//   } catch (err) {
//     console.error("❌ /scrape error:", err);
//     return res.status(500).json({
//       message: "scrape failed",
//       error: String(err?.message || err),
//       stack: process.env.NODE_ENV === "production" ? undefined : String(err?.stack || ""),
//     });
//   }
// });

