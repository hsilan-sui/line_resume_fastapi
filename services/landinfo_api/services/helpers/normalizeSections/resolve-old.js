//把輸入的地段資訊（段名或段號）轉換成舊版地政系統（舊站）可以用的 select 值。
//因為舊站 <select> 的 value 不是單純段號，而是像 HC_1938 這種格式，所以這裡是做轉換與對應查找
//匯入一份資料清單（LIST）
//這個清單應該是復興區所有段的名稱與段號對照表
const LIST = require('../../data/old/taoyuan/fuxing/fuxing_sections');
const OFFICE = 'HC'; // 舊站 select 需要 'HC_<id>'

// input 可是：段名（大利段）、純數字 id（1938/0541）、或 'HC_1938'
//工具函式，確保段號是4 碼格式（左邊補 0）
const pad4 = s => String(s).padStart(4,'0');
//主函式 resolveOldSection
// 參數 input 可以是：
// 段名（例：大利段）
// 純數字段號（例：1938 或 541）
// 舊站格式（例：HC_1938）
function resolveOldSection(input) {
  if (!input) return null;
  let s = String(input).trim();
  //如果 input 是舊站格式（HC_數字），就把前面的 HC_ 拆掉，只留段號。
  //例：HC_1938 → "1938"
  if (/^HC_\d{1,4}$/i.test(s)) s = s.split('_')[1];
  //如果是純數字段號，補成 4 碼。
  //例："541" → "0541"
  if (/^\d{1,4}$/.test(s)) s = pad4(s);

  //嘗試用段號 (id) 在清單裡找對應記錄
//如果找不到，再用段名 (name) 找
  const byId = LIST.find(x => x.id === s);
  const byName = LIST.find(x => x.name === input);
  const rec = byId || byName;
  if (!rec) return null;

  //找到對應段資料後，回傳一個物件，內容有：
  // id：段號（4 碼）
  // name：段名
  // oldValue：舊站 <select> 需要的值，例如 "HC_1938"
  return {
    id: rec.id,
    name: rec.name,
    oldValue: `${OFFICE}_${rec.id}` // 舊站 #select_sect_id 的值
  };
}
//resolveOldSection('大利段')
// { id: '1938', name: '大利段', oldValue: 'HC_1938' }
module.exports = { resolveOldSection, FUXING_OLD_LIST: LIST };
