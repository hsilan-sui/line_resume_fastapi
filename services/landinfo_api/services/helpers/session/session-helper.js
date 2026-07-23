/**
 * helpers/session/session-helper.js
 * Playwright 輔助函式庫，專門用於管理網頁自動化腳本中的會話（session）。它處理了登入狀態的持久化，並在狀態過期或失效時自動重新登入，確保腳本能順利執行。
 * 含 tracing/screenshot、參數化 timeout
 * 
 * ==> ensureSession
 * 可重複用在任何網站的，
 * 下次換網站只要換三個模組化參數 / 函式就行，不用重寫核心邏輯
 * 可以重用？
ensureSession(browser, opts) 只是負責管理「持久化 Session 狀態」的生命週期：

statePath → 存檔路徑，換網站就換檔名（例如 state/twitter.json）。

targetUrl → 要開的第一個頁面（可能是首頁或登入頁）。

validate(page) → 怎麼判斷「已登入」或「站內可用」。

preload(page)（可選）→ 首訪要先等哪些 API 或 DOM 準備好。

login(page) → 如果沒登入，怎麼自動登入（帳密、OTP、點選等）。

fingerprint（可選）→ 偽裝 UA、時區、視窗大小。

ttlHours（可選）→ session 最多用多久就自動重建。
- 這些都透過 opts 參數物件傳進去，所以換網站只要新建一組 validate/login/preload，就能共用同一支 helper
下次爬另一個有帳密的站
假設你要爬「XXX 登入系統」： 
*/

// === 檔頭：匯入與小工具 === 
const fs = require('fs');
const path = require('path');


/**  安全判斷檔案是否存在
 * 載入 Node.js 內建的檔案系統與路徑模組，下面會用到檔案存在檢查、讀寫與組路徑
 * 同步檢查檔案或目錄是否存在
*/
function fileExists(p){ 
    //fs.accessSync 會在路徑不存在時丟錯，包在 try/catch 內回傳 false，存在則回 true
    try { fs.accessSync(p); 
          return true; 
    } catch { 
          return false; 
    } 
}

/** 原子寫入 JSON（先寫 tmp 再 rename，避免壞檔） 
 * 原子寫入 JSON：先把內容寫到臨時檔 *.tmp-時間戳，寫完再 rename 覆蓋正式檔。
 * 為什麼：避免寫到一半程式崩掉造成壞檔。rename 在同一磁碟分割區是原子操作。
 * 也會先確保目錄存在（mkdir -p 效果）
*/
function atomicWriteJSON(p, data){
  const dir = path.dirname(p);
  if (!fileExists(dir)) fs.mkdirSync(dir, { recursive: true });
  const tmp = p + '.tmp-' + Date.now();
  // 👉 我新增：JSON 美化輸出，便於人工檢視；功能不變
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
  fs.renameSync(tmp, p);
}

/** 我新增：確保目錄存在（給 debug 資料輸出用） */
function ensureDir(dir){
  if (!fileExists(dir)) fs.mkdirSync(dir, { recursive: true });
}

/** 我新增：簡單時間戳，用於 debug 輸出檔案夾命名 */
function ts(){
  const d = new Date(); const pad = n => String(n).padStart(2,'0');
  return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}


// === 主函式 JSDoc 與用途 ===
/**
 * 註解說明函式 ensureSession 在做什麼：帶 cookie/localStorage 的 Context 建立與自動恢復、驗證、重建與保存。
 * 建立帶 session 的 BrowserContext：
 * 1) 若有 state.json 且未過期 → 載入
 * 2) 開頁→preload→validate（同時看 DOM 與 cookie）
 * 3) 驗證失敗 → 刪舊 state、重建 context，跑 login 再驗一次
 * 4) 成功後保存最新 state.json（原子寫入）
 *
 * @param {import('playwright').Browser} browser
 * @param {{
 *   statePath: string,                  // 例如 'state/easymap.json'
 *   targetUrl: string,                  // 入口頁
 *   validate: (page, context)=>Promise<boolean>,
 *   login?: (page)=>Promise<void>,      // 無帳密站可視為「首訪初始化」
 *   preload?: (page)=>Promise<boolean|void>, // 等 API/DOM 就緒（可回傳 boolean）
 *   headers?: Record<string,string>,    // e.g. Accept-Language / Referer
 *   ttlHours?: number,                  // 狀態檔有效期，預設 24h
 *   fingerprint?: {
 *     userAgent?: string,
 *     viewport?: {width:number,height:number},
 *     timezoneId?: string,
 *     locale?: string
 *   },
 *   // 我新增：參數化 timeout、debug 設定與強制忽略舊 state（forceFresh）
 *   timeouts?: { gotoMs?: number },     // 逾時設定（目前支援 goto）
 *   debug?: { dir?: string, trace?: boolean }, // 失敗時輸出 trace/screenshot
 *   forceFresh?: boolean,               // true 時忽略舊 state（例如站點改版日）
 * }} opts
 */
//ensureSession 接受一個 browser（Playwright 的 Browser 實例）與一組選項
async function ensureSession(browser, opts) {
   //用解構把選項拆開並塞預設值
  const {
    statePath, //狀態檔（cookies/localStorage）儲存與載入的位置
    targetUrl, //啟動後要打開的入口頁
    validate, //你的驗證函式，用來判斷是否「已登入/已初始化」
    login, //必要時走一次登入或首訪初始化
    preload, //進站後、驗證前，先等 API/DOM 就緒（暖機）
    headers, //統一加到所有請求的 HTTP header（常見：Accept-Language, Referer）
    ttlHours = 24, //狀態檔過期時間（預設 24 小時）
    // fingerprint指紋偽裝參數（UA、視窗大小、時區、語系）
    fingerprint = { 
      userAgent: 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
      viewport: { width: 1366, height: 768 },
      timezoneId: 'Asia/Taipei',
      locale: 'zh-TW',
    },
    // 我新增：參數化 timeout（可依站點調整），debug（trace/screenshot），forceFresh
    timeouts = { gotoMs: 45000 },
    debug = { dir: 'debug', trace: true },
    forceFresh = false,
  } = opts;

  // 👉 我新增：把 statePath 轉為絕對路徑，避免工作目錄變動造成路徑飄
  const absStatePath = path.resolve(statePath);

  // TTL 檢查：判斷狀態檔是否「新鮮」 
  //這是一個立即執行函式（IIFE），回傳布林值
  const stateFresh = (() => {
    // 👉 我新增：forceFresh=true 直接忽略舊 state（例如站方大改版日）
    if (forceFresh) return false;
    if (!fileExists(absStatePath)) return false;
    //先看檔案是否存在；存在就取檔案最後修改時間 mtimeMs
    try {
      const st = fs.statSync(absStatePath);
      //如果距現在時間小於 ttlHours，視為「新鮮」（可用），否則視為過期
      //為什麼：很多站的 cookie 會過期；雖然檔案還在，但已不能用，所以定期重建可避免踩雷
      return (Date.now() - st.mtimeMs) < ttlHours * 3600 * 1000;
    } catch { return false; }
  })();

  // 建立 context（可選擇載入 state），並掛上基本指紋與額外標頭
  //建立 Context（可能載入舊狀態）＋ 指紋偽裝
  //withState 表示想要載入舊狀態；實際上還要 stateFresh && 檔案存在 才真的載入
  const createContext = async (withState) => {
    let context;
    //如果 storageState 載入壞檔或格式不合，newContext 可能丟錯，所以包 try/catch，失敗就退回乾淨的 Context（不載入舊狀態）
    try {
      context = await browser.newContext({
        storageState: (withState && stateFresh && fileExists(absStatePath)) ? absStatePath : undefined,
        //無論有無狀態，一律套上指紋參數（UA/viewport/timezone/locale）
        userAgent: fingerprint.userAgent,
        viewport: fingerprint.viewport,
        timezoneId: fingerprint.timezoneId,
        locale: fingerprint.locale,
      });
    } catch {
      // state.json 損毀或版本不符 → 退回乾淨 context
      context = await browser.newContext({
        //無論有無狀態，一律套上指紋參數（UA/viewport/timezone/locale）
        userAgent: fingerprint.userAgent,
        viewport: fingerprint.viewport,
        timezoneId: fingerprint.timezoneId,
        locale: fingerprint.locale,
      });
    }

    // 基本「自動化指紋」隱藏（best-effort）
    //在每個 page 執行任何網頁腳本之前，先注入一段初始化腳本：addInitScript
    await context.addInitScript(() => {
      //把 navigator.webdriver 改成 false（很多站會用這個判斷自動化）
      Object.defineProperty(navigator, 'webdriver', { get: () => false });
      //包裝 permissions.query：當查詢 notifications 時回傳與瀏覽器一致的狀態，減少不一致
      const q = navigator.permissions?.query;
      if (q) {
        navigator.permissions.query = (p)=> p.name === 'notifications'
          ? Promise.resolve({ state: Notification.permission })
          : q(p);
      }
      //修改 navigator.plugins 與 navigator.languages，更貼近真實使用者環境
      //這些是常見的 bot 指紋檢測點。此處為「盡力而為」的基本防偵測
      Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
      Object.defineProperty(navigator, 'languages', { get: () => ['zh-TW','zh','en-US','en'] });
    });
    //若有額外 headers，統一加到此 Context 的所有請求（像 Accept-Language）
    if (headers) await context.setExtraHTTPHeaders(headers);

    /** 我新增：若開啟 debug.trace，從 context 建立後就啟動 tracing
     *  - screenshots: true 會在 trace 中記錄畫面
     *  - snapshots: true 會記錄 DOM 快照，可回放互動
     *  - sources: false 可省空間（需要看測試碼再開）
     */
    if (debug?.trace) {
      await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
    }

    return context;
  };

  // 保存最新狀態（先取物件，再原子寫檔）
  //存檔工具：把最新的 storage 狀態寫回硬碟（原子）
  const saveState = async (context) => {
    //context.storageState() 取得物件（包含 cookies / origins / localStorage）
    const raw = await context.storageState();
    //再用我們的 atomicWriteJSON 寫到 statePath；不用 Playwright 內建的 storageState({ path }) 為了保證「原子性」
    atomicWriteJSON(absStatePath, raw);
  };

  /** 我新增：封裝失敗時輸出 trace 與 screenshot
   *  - 產出路徑：debug/<timestamp>-<label>/{failure.png, trace.zip}
   *  - 可用 npx playwright show-trace <zip> 回放
   */
  async function dumpDebug(context, page, label){
    try {
      const outDir = path.join(debug?.dir || 'debug', `${ts()}-${label}`);
      ensureDir(outDir);
      if (page) {
        await page.screenshot({ path: path.join(outDir, 'failure.png'), fullPage: true });
      }
      if (debug?.trace && context) {
        await context.tracing.stop({ path: path.join(outDir, 'trace.zip') });
      }
    } catch {}
  }

  // ---------- 第一次嘗試：載入舊狀態 → 開頁 → 預熱 → 驗證 ----------
  //用 withState=true 建 Context（如果 stateFresh 也為真才真的載）
  let context = await createContext(true);
  //建一個新分頁，打開 targetUrl，等待 DOM Content Loaded
  let page = await context.newPage();
  //設 timeout: 45000（45 秒）避免永遠卡住
  await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: timeouts.gotoMs || 45000 });

  //若有提供 preload（例如等待關鍵 API 回來，或關掉遮罩彈窗），就先跑
  //用 try/catch 避免預熱失敗直接中斷流程
  if (typeof preload === 'function') { try { await preload(page); } catch {} }

  //呼叫你的 validate 同時看 DOM / cookie，判斷是否「已可用」。
  // 任何錯誤都視為驗證失敗（ok=false）
  let ok = false;
  try { ok = await validate(page, context); } catch { ok = false; }

  //失敗補救：一次 reload 再驗一次
  // 有些站首訪需要 reload 才會把 cookie/DOM 完整掛上
  //很多站首訪會在第一次載入時才種 cookie/service worker，第二次才讓 DOM 就緒
  //所以這裡做一次 reload（並加一點隨機延遲，讓節奏更像真人）
  if (!ok) {
    try {
      await page.waitForTimeout(800 + Math.random()*600);
      await page.reload({ waitUntil: 'domcontentloaded', timeout: timeouts.gotoMs || 45000 });
      //reload 後再跑一次 preload() 與 validate()
      if (typeof preload === 'function') { try { await preload(page); } catch {} }
      ok = await validate(page, context);
    } catch { ok = false; } //仍失敗就保持 ok=false
  }

  //成功路徑：更新狀態並回傳
  if (ok) {
    //驗證通過 → 立刻把最新狀態寫回檔案（有些站會在背景刷新 token）
    await saveState(context); // 更新可能變動的 cookie / storage

    // 👉 我新增：若有開 trace，第一次嘗試成功就乾脆關掉 trace（不寫 zip，省空間）
    if (debug?.trace) {
      try { await context.tracing.stop(); } catch {}
    }

    //回傳 { context, page, reused }：
    // reused=true 表示這次用了舊的、而且在 TTL 內的狀態檔。
    // 之後你的爬取流程就用這個 page 開始
    return { context, page, reused: stateFresh && fileExists(absStatePath) };
  }

  // ---------- 第二次嘗試（重建）：砍舊檔 → 乾淨起 → login → preload → validate ----------
  //關掉剛剛的 Context
  // 👉 我新增：第一次失敗時輸出 debug（trace/screenshot）
  try { await dumpDebug(context, page, 'first-attempt'); } catch {}
  await context.close();

  //刪掉舊的狀態檔（可能是壞掉或已過期還用不起來）
  if (fileExists(absStatePath)) fs.rmSync(absStatePath);
  //建乾淨 Context（withState=false），開新分頁、再進入口頁
  context = await createContext(false);
  page = await context.newPage();

  await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: timeouts.gotoMs || 45000 });
  //若有 login（對於無密碼站，login 代表「首訪初始化/最小互動」），先跑它
  if (typeof login === 'function') { try { await login(page); } catch {} }
  //再跑一次 preload 等待 API/DOM 就緒
  if (typeof preload === 'function') { try { await preload(page); } catch {} }

  const ok2 = await validate(page, context).catch(() => false);
  if (!ok2) {
    //再驗一次；仍失敗就關掉 Context 丟錯，交由呼叫端決定（寫 log、通知、人工處理…）
    // 👉 我新增：第二次也失敗，輸出 debug（含 trace.zip，可回放）
    try { await dumpDebug(context, page, 'second-attempt'); } catch {}
    await context.close();
    throw new Error('重試後仍無法建立有效 session，請檢查登入/預熱/驗證條件。');
  }

  await saveState(context);
  //成功 → 存新狀態檔 → 回傳，reused=false 表示這是新建的 session
  // 👉 我新增：成功時若 trace 還開著，正常停止並輸出 zip（可保留，也可關閉不輸出）
  if (debug?.trace) {
    try { await context.tracing.stop(); } catch {}
  }
  return { context, page, reused: false };
}

//匯出主函式讓外部使用
module.exports = { ensureSession };
