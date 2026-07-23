// helpers/enqueue-test.js
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../../.env") });

const { crawlQueue, closeAll } = require("../queue"); // 如果你的 queue.js 在別處，再調整路徑

(async () => {
  try {
    const job = await crawlQueue.add("landinfo", {
      city: process.env.CITY,        // 例如 H
      district: process.env.DISTRICT,// 例如 13
      section: process.env.SECTION,  // 例如 大利段 或 sectionId
      landNo: process.env.LANDNO,    // 例如 1306
      userId: "TEST_USER_ID",        // 先隨便，這步只測 Queue→Worker
      traceId: `test-${Date.now()}`
    });

    console.log("✅ enqueued job id =", job.id);
  } catch (e) {
    console.error("❌ enqueue failed:", e);
  } finally {
    await closeAll();
  }
})();
