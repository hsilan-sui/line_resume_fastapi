// helpers/sections/resolve-section.js
// do what: 全國版段別解析器（新站/舊站都可用）
// why: LINE 使用者輸入多為段名；新站需要 sectionId；舊站需要 officeCode_id

const ALL = require("../../data/out/all-sections.json");

// -------------------------
// 小工具：pad4
// do what: 純數字段號補 4 碼
// why: 你的資料 id 有 0465 這種
// -------------------------
const pad4 = (s) => String(s).padStart(4, "0");

// -------------------------
// 小工具：normalize section name
// do what: 段名容錯（去空白/全形空白/括號）
// why: LINE 使用者會打「大利段 」「大利段(某小段)」等等
// -------------------------
function normalizeName(input) {
  return String(input || "")
    .trim()
    .replace(/[\s\u3000]/g, "") // 空白 + 全形空白
    .replace(/[()（）]/g, "");
}

// city 你新站用代碼（H），資料裡是 cityName（桃園市）
const CITY_CODE_TO_NAME = {
  H: "桃園市",
  // ... 其他縣市代碼自己補
};

// =====================================================
// ✅ 建索引（載入一次，之後每次 resolve O(1)~O(k)）
// do what: 加速查詢
// why: ALL 全國檔很大，每次 filter 會變慢
// =====================================================
const byCityTown = new Map(); // key = `${cityName}|${townCode}` -> array
const byCityTownId = new Map(); // key = `${cityName}|${townCode}|${id}` -> rec
const byCityTownName = new Map(); // key = `${cityName}|${townCode}|${normName}` -> rec

for (const rec of ALL) {
  const cityName = rec.cityName || "";
  const townCode = String(rec.townCode || "");
  const id = String(rec.id || "");
  const nm = normalizeName(rec.name);

  const k = `${cityName}|${townCode}`;
  if (!byCityTown.has(k)) byCityTown.set(k, []);
  byCityTown.get(k).push(rec);

  byCityTownId.set(`${k}|${id}`, rec);
  byCityTownName.set(`${k}|${nm}`, rec);
}

function resolveSection({ city, townCode, section }) {
  // -------------------------
  // do what: 防呆
  // -------------------------
  if (!section) return null;

  const rawSection = String(section).trim();
  let s = rawSection;

  // 支援 "HC_1938" → 1938（也支援其他 officeCode）
  const m = s.match(/^([A-Z]{2})_(\d{1,4})$/i);
  if (m) s = m[2];

  // 純數字段號 -> pad4
  if (/^\d{1,4}$/.test(s)) s = pad4(s);

  const cityNameFromCode = CITY_CODE_TO_NAME[city];
  const cityName = cityNameFromCode || city; // city 可能本來就是 "桃園市"

  const town = String(townCode ?? "").trim();
  if (!cityName || !town) {
    // 你也可以選擇：允許只靠段名全國搜尋（但同名會撞）
    return null;
  }

  const baseKey = `${cityName}|${town}`;

  // -------------------------
  // 1) 先用 id 找（最快、最準）
  // -------------------------
  let rec = byCityTownId.get(`${baseKey}|${s}`);

  // -------------------------
  // 2) 找不到再用 name 找（做 normalize）
  // -------------------------
  if (!rec) {
    const keyName = normalizeName(rawSection);
    rec = byCityTownName.get(`${baseKey}|${keyName}`);
  }

  // -------------------------
  // 3) 最後保守 fallback：掃 candidates（避免資料 typo / 未建到 index 的奇怪情況）
  // -------------------------
  if (!rec) {
    const candidates = byCityTown.get(baseKey) || [];
    rec =
      candidates.find((x) => String(x.id) === s) ||
      candidates.find((x) => normalizeName(x.name) === normalizeName(rawSection));
  }

  if (!rec) return null;

  return {
    id: String(rec.id),
    name: rec.name,
    sectionId: String(rec.id), // 新站用
    officeCode: rec.officeCode,
    townCode: String(rec.townCode),
    cityName: rec.cityName,
    townName: rec.townName,
    oldValue: `${rec.officeCode}_${rec.id}`, // 舊站用
  };
}

module.exports = { resolveSection };
