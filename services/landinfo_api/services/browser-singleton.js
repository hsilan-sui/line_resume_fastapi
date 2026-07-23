// src/browser-singleton.js
/**
 * 共用單例

如果每個 job 都開新 Browser → 開銷大、啟動慢、記憶體爆炸。

用單例（singleton）讓所有任務共用同一顆 Browser，可以大幅減少資源消耗。

壽命 & 使用次數控制

Chromium/Playwright 長時間跑 → 記憶體可能不斷增加。

強制定期重啟（以時間或次數為界），可以避免長時間執行造成不穩定。

自動恢復

如果 Browser 意外 crash 或被 kill，下次呼叫 ensureBrowser() 會自動補一顆新的。

確保系統健壯，不會因為單一 Browser 死掉整個 worker 崩潰。

可配置

BROWSER_MAX_AGE_MS、BROWSER_MAX_USES 可以透過環境變數調整，依據不同 workload 最佳化
 */
const { chromium } = require('playwright');

let _browser = null;   // 全域變數：共用的 Browser 實例
let _launchedAt = 0;   // 紀錄瀏覽器啟動的時間戳
let _useCount = 0;     // 紀錄這個 Browser 已經被使用幾次

// === 可調參數（避免 Browser 長時間佔用記憶體）===
// - Playwright/Chromium 長時間開著可能會累積記憶體、產生 Zombie Process。
// - 所以設一個「壽命」與「使用次數」上限，強制定期重啟，確保穩定。
const MAX_AGE_MS = Number(process.env.BROWSER_MAX_AGE_MS || 60 * 60 * 1000); // 預設 1 小時
const MAX_USES   = Number(process.env.BROWSER_MAX_USES   || 300);            // 預設最多 300 jobs

// 確保取得一顆可用的 Browser
// 為什麼？ → 避免每個任務都 launch() 一次，會很耗時＆浪費資源。
//           透過「共用單例」+「定期重啟」，取得效能與穩定性的平衡。
async function ensureBrowser() {
  const now = Date.now();

  // 如果已經有一顆活著的 Browser
  if (_browser && _browser.isConnected()) {
    const ageOk  = (now - _launchedAt) < MAX_AGE_MS; // 檢查壽命是否過期
    const usesOk = _useCount < MAX_USES;             // 檢查使用次數是否超限
    if (ageOk && usesOk) return _browser;

    // 超過壽命或使用上限 → 主動關閉舊的，重新啟動一顆新的
    // 為什麼？ → 防止記憶體外洩或效能下降。
    try { await _browser.close(); } catch {}
    _browser = null;
  }

  // 啟動新的 Browser
  _browser = await chromium.launch({
    headless: String(process.env.HEADLESS ?? 'true') !== 'false',
    // 為什麼要這些 args？
    // --no-sandbox: 避免在 Docker / CI 環境權限不足導致失敗
    // --disable-dev-shm-usage: 避免 /dev/shm 空間不足造成 crash
    // --disable-blink-features=AutomationControlled: 降低被網站偵測為自動化的機率
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled'],
  });

  _launchedAt = now;   // 重設啟動時間
  _useCount   = 0;     // 重設使用次數

  // 如果 Browser 被意外關掉（crash / 手動 kill），下次呼叫 ensureBrowser 時會重建
  _browser.on('disconnected', () => { _browser = null; });

  return _browser;
}

// 記錄這顆 Browser 又被使用一次
// 為什麼？ → 方便計算 MAX_USES，避免單顆 Browser 過度使用。
function markBrowserUsed() { _useCount += 1; }

// 手動關閉 Browser（例如服務 shutdown 時）
// 為什麼？ → 避免資源洩漏，正確釋放 Chromium。
async function closeBrowser() {
  if (_browser) { try { await _browser.close(); } catch {} }
  _browser = null;
}

module.exports = { ensureBrowser, markBrowserUsed, closeBrowser };
