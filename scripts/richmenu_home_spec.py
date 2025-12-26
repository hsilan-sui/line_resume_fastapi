# richmenu_home_spec.py

# Rich Menu 的規格檔（layout + 點擊行為）
# 我會在deploy_richmenu.py import 這個Rich Menu 的規格檔
# 拿到 尺寸、熱區座標、以及每個熱區按下去要做什麼，再組成 LINE API 需要的 payload 去建立 Rich Menu

# do what ?
## 0) 定義 Rich Menu 圖片尺寸 W, H
## 1) 用「比例」定義每個點擊熱區的位置與大小（AREAS_PCT）
## 2) 定義每個熱區按下去要觸發的動作（ACTIONS）
## 3) 最後部署時會把比例換算成 LINE 要的像素 bounds：x, y, width, height（整數）

# How（怎麼運作）
## 1) W, H = 2500, 1686
## 這是 Rich Menu 圖片的實際像素尺寸（圖是 2500×1686）＝> 後面把比例轉像素時要靠它
W, H = 2500, 1686

## 2) AREAS_PCT：用比例定義熱區
# 用比例定義熱區，x y w h 都是 0 到 1
# 每個 key（像 portfolio/github/...）代表一個熱區鍵盤
# 每個熱區用 0~1 的比例描述：
# x: 左上角 X 從左邊算起（0 = 最左、1 = 最右）
# y: 左上角 Y 從上面算起（0 = 最上、1 = 最下）
# w: 寬度佔整張圖的比例
# h: 高度佔整張圖的比
AREAS_PCT = {
    "portfolio": {"x": 0.098, "y": 0.119, "w": 0.805, "h": 0.471},
    "github":    {"x": 0.064, "y": 0.637, "w": 0.283, "h": 0.275},
    "line_card": {"x": 0.359, "y": 0.637, "w": 0.283, "h": 0.275},
    "contact":   {"x": 0.654, "y": 0.637, "w": 0.283, "h": 0.275},
}

# 部署腳本會做這件事：
# x_px = round(x * W)
# y_px = round(y * H)
# width_px = round(w * W)
# height_px = round(h * H)

# 以 portfolio 為例，換算大概是：

# x ≈ 0.098*2500 = 245
# y ≈ 0.119*1686 = 201
# width ≈ 0.805*2500 = 2013
# height ≈ 0.471*1686 = 794
# 也就是：圖片中間那一大塊作品集按鈕區

# 每個熱區點下去要做什麼=> 定義「每個熱區的行為」，而且 key 必須跟 AREAS_PCT 對得上
ACTIONS = {
    "portfolio": {"type": "message", "text": "作品集"},
    "github":    {"type": "uri", "uri": "https://github.com/hsilan-sui/hsilan-sui"},
    "line_card": {"type": "message", "text": "LINE名片"},
    "contact":   {"type": "message", "text": "聯繫我"},
}


# 常見三種：

# A) type: "message"
# 使用者點了 → LINE 會送出一則訊息到聊天室
# 你的 webhook（FastAPI）就會收到文字 "作品集" / "LINE名片" / "聯繫我"
# 然後你就可以照你原本的指令路由去回 Flex 卡片、或推播。

# B) type: "uri"
# 使用者點了 → 直接打開連結
# 這裡是開 GitHub 網址。
# https://github.com/<your-id> 你要換成真的帳號。

# C) type: "postback"
# postback ✅
# 點了 → webhook 一定會收到事件（postback）
# 聊天室不一定出現文字（可選擇顯示）
# 優點：適合做「模式切換、狀態記錄、追蹤、帶參數」這種後端控制

#最可能會踩的坑
# AREAS_PCT 有 key，但 ACTIONS 沒有同名 key → 部署程式通常會 raise error（你前面就有寫檢查）
# uri 沒換成真的 → 點 GitHub 會開到不存在頁
# 比例算錯 → 熱區會偏移（點 A 區卻觸發 B）
# LINE Rich Menu 的 bounds 要整數像素 → 所以部署時要 round