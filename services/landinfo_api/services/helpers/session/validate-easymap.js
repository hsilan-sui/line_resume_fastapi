// helpers/session/validate-easymap.js
/** 回傳 true 表示「站內初始化完成、可操作」 */
module.exports.validate = async (page, context) => {
    // A. DOM 檢查：城市下拉是否已被填好
    const domReady = await page.evaluate(() => {
      const el = document.querySelector('#select_city_id');
      return !!el && el.options && el.options.length > 1;
    });
  
    // B. Cookie 檢查：至少拿到關鍵 session cookie
    const ck1 = await context.cookies('https://easymap.land.moi.gov.tw');
    const ck2 = await context.cookies('https://wmts.nlsc.gov.tw');
    const hasSession =
      ck1.some(c => c.name === 'JSESSIONID' || c.name === 'maestro') ||
      ck2.some(c => c.name === 'JSESSIONID');
  
    return domReady && hasSession;
  };
  