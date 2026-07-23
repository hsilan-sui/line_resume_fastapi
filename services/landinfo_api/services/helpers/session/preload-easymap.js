// helpers/session/preload-easymap.js
/** 首訪預熱：等待關鍵 API 或下拉真的有資料 */
module.exports.preload = async (page) => {
    await Promise.race([
      page.waitForResponse(r => r.url().includes('City_json_getCityList') && r.status() === 200, { timeout: 20000 }),
      page.waitForFunction(() => {
        const el = document.querySelector('#select_city_id');
        return el && el.options.length > 1;
      }, { timeout: 20000 }),
    ]).catch(()=>{});
  };
  