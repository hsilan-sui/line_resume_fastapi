// services/worker.js
// 說明：BullMQ Worker（Presign → PUT R2 → /result 帶 URL 版）

const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../.env") });

const { Worker } = require("bullmq");
const { crawlEvents, connection, QUEUE_NAME } = require("./queue");

// 共用 Browser 單例
const { ensureBrowser, markBrowserUsed, closeBrowser } = require("./browser-singleton");

// 你的爬蟲主函式（需支援 _browser；有傳入時不可自行 launch/close）
const { scrapeLandInfo } = require("./index");

// Node 18+ 內建 fetch；Node 16 需動態載入 node-fetch
const fetchSafe = global.fetch
  ? global.fetch
  : (...args) => import("node-fetch").then(({ default: f }) => f(...args));

const concurrency = parseInt(process.env.WORKER_CONCURRENCY || process.env.CONCURRENCY || "1", 10);

const BASE = (process.env.CF_WORKER_URL || process.env.WORKER_BASE || "").replace(/\/+$/, "");
const TOKEN = process.env.WORKER_TOKEN || "";

if (!BASE) console.error("❌ CF_WORKER_URL / WORKER_BASE 未設定");
if (!TOKEN) console.error("❌ WORKER_TOKEN 未設定");

// -------------------------
// 小工具：呼叫 Cloudflare Worker /result
// -------------------------
async function postResultToCF({ userId, traceId, status, payload }) {
  if (!BASE) throw new Error("CF_WORKER_URL / WORKER_BASE 未設定");
  if (!TOKEN) throw new Error("WORKER_TOKEN 未設定");
  if (!userId) throw new Error("缺少 userId（LINE 真實 userId）");

  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), 10_000);

  try {
    const res = await fetchSafe(`${BASE}/result`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "authorization": `Bearer ${TOKEN}`,
      },
      body: JSON.stringify({ userId, traceId, status, payload }),
      signal: ac.signal,
    });

    const text = await res.text();
    if (!res.ok) console.error("❌ /result 回應非 2xx：", res.status, text);
    else console.log("✅ /result 成功回應：", text);
  } finally {
    clearTimeout(t);
  }
}

// -------------------------
// 小工具：上傳 PNG 到 R2（presign -> put）
// 回傳：{ key, imageUrl }
// -------------------------
async function uploadPngToR2({ pngBuf }) {
  const key = `screenshots/${new Date().toISOString().slice(0, 10)}/${Date.now()}-${Math.random()
    .toString(16)
    .slice(2)}.png`;

  // 1) presign
  const presignRes = await fetchSafe(`${BASE}/presign`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "authorization": `Bearer ${TOKEN}`,
    },
    body: JSON.stringify({
      key,
      contentType: "image/png",
      expiresInSec: 300,
    }),
  });

  const presignText = await presignRes.text();
  if (!presignRes.ok) {
    throw new Error(`/presign 失敗：${presignRes.status} ${presignText}`);
  }

  let presignJson;
  try {
    presignJson = JSON.parse(presignText);
  } catch {
    throw new Error(`/presign 非 JSON 回應：${presignText}`);
  }

  const { putUrl, s3Url, cdnUrl } = presignJson || {};
  if (!putUrl) throw new Error("/presign 缺少 putUrl");

  // 2) put upload
  const putRes = await fetchSafe(putUrl, {
    method: "PUT",
    headers: {
      "content-type": "image/png",
      "content-length": String(pngBuf.length),
    },
    body: pngBuf,
  });

  const putText = await putRes.text();
  if (!putRes.ok) {
    throw new Error(`PUT R2 失敗：${putRes.status} ${putText}`);
  }

  const imageUrl = (cdnUrl || s3Url || "").trim();
  return { key, imageUrl };
}

// Worker：負責拿 job 來跑
const worker = new Worker(
  QUEUE_NAME,
  async (job) => {
    const { city, district, section, landNo, userId, traceId } = job.data;

    // ✅ 1) traceId 保底（job 沒帶也不會斷）
    const safeTraceId = traceId || `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    // 這些資訊即使失敗也要能回傳（HR 會知道你在查什麼）
    const basePayload = {
      city: city || process.env.CITY,
      district: district || process.env.DISTRICT,
      section: section || process.env.SECTION,
      landNo: landNo || process.env.LANDNO,
    };

    let br;
    try {
      // 0) 基本檢查（先擋掉不可能成功的）
      if (!BASE) throw new Error("CF_WORKER_URL / WORKER_BASE 未設定");
      if (!TOKEN) throw new Error("WORKER_TOKEN 未設定");
      if (!userId) throw new Error("缺少 userId（LINE 真實 userId）");

      // 1) 取得共用 Browser
      br = await ensureBrowser();

      // 2) 跑爬蟲（最常 throw 的地方）
      const result = await scrapeLandInfo({
        city: basePayload.city,
        district: basePayload.district,
        section: basePayload.section,
        landNo: basePayload.landNo,
        _browser: br,
        headless: String(process.env.HEADLESS ?? "true") !== "false",
      });

      // 記錄使用次數（配合 MAX_USES/MAX_AGE_MS 決定是否需重啟）
      markBrowserUsed();

      // 3) 讀 screenshot PNG
      if (!result?.map_image_path) {
        throw new Error("scrapeLandInfo 未回傳 map_image_path");
      }
      const pngBuf = fs.readFileSync(result.map_image_path);

      // 4) 上傳到 R2
      const { key, imageUrl } = await uploadPngToR2({ pngBuf });

      // ✅ 2) 上傳成功後刪掉本機 PNG（避免磁碟慢慢被塞滿）
      // 如果你想保留圖做 debug，把這段移到 push 成功後再刪也可以
      try { fs.unlinkSync(result.map_image_path); } catch {}

      // 5) 成功 → 推結果（只推一次）
      await postResultToCF({
        userId,
        traceId: safeTraceId,
        status: "ok",
        payload: {
          city: result.city ?? basePayload.city,
          district: result.district ?? basePayload.district,
          section: result.section ?? basePayload.section,
          landNo: result.landNo ?? basePayload.landNo,
          land_info: result.land_info || {},
          imageUrls: imageUrl ? [imageUrl] : [],
          r2Key: key,
        },
      });

      return result;
    } catch (err) {
      const errorMessage = String(err?.message || err);

      // 失敗也推一次（只推一次）
      try {
        await postResultToCF({
          userId,
          traceId: safeTraceId,
          status: "failed",
          payload: {
            ...basePayload,
            errorMessage,
          },
        });
      } catch (pushErr) {
        console.error("❌ 失敗回傳 /result 也失敗：", pushErr);
      }

      // 讓 BullMQ 記錄 failed（你在 completed/failed event 看得到）
      throw err;
    }
  },
  {
    connection,
    concurrency,
    stalledInterval: 60_000,
  }
);

// 監聽事件（看得到完成 / 失敗）
crawlEvents.on("completed", ({ jobId }) => {
  console.log(`✅ Job ${jobId} completed`);
});
crawlEvents.on("failed", ({ jobId, failedReason }) => {
  console.error(`❌ Job ${jobId} failed:`, failedReason);
});

worker.on("error", (err) => {
  console.error("Worker error:", err);
});

console.log(`🐂 Worker started. Queue="${QUEUE_NAME}" Concurrency=${concurrency}`);

// 優雅關閉：同時收 worker 與共用 browser
async function shutdown() {
  console.log("[SHUTDOWN] closing worker & browser…");
  try { await worker.close(); } catch {}
  try { await closeBrowser(); } catch {}
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
