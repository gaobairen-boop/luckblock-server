import os
import json
import random
import datetime
import time
import hashlib
import urllib.parse
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_FILE = "server_database.json"

MERCHANT_ID = "2000132"
HASH_KEY = "5294y06JbISpM5x9"
HASH_IV = "v77hoKGq4kWxPxWD"

# 💎 同步老闆設定的 8 大要素
ITEMS = ["藍寶石", "紅寶石", "綠寶石", "獅子", "老虎", "老鷹", "鑽石", "飛機"]

# 📊 消除分級底分系數設定 (相應倍數乘上下注金額)
BASE_SCORES = {
    "藍寶石": 15, "紅寶石": 15, "綠寶石": 15,    # 便宜級底分
    "獅子": 50, "老虎": 50, "老鷹": 50,         # 中等級底分
    "鑽石": 150,                               # 高等級底分
    "飛機": 500                                # 最高等底分
}

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def generate_check_mac_value(params):
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    raw_str = f"HashKey={HASH_KEY}&" + "&".join([f"{k}={v}" for k, v in sorted_params]) + f"&HashIV={HASH_IV}"
    url_encoded = urllib.parse.quote_plus(raw_str).lower()
    return hashlib.sha256(url_encoded.encode('utf-8')).hexdigest().upper()

@app.route("/register", methods=["POST"])
def register():
    req = request.json or {}
    db = load_db()
    username = req.get("username", "").strip()
    password = req.get("password", "").strip()
    if not username or not password: return jsonify({"status": "fail", "msg": "❌ 帳號與密碼不能為空！"})
    for uid, uinfo in db.items():
        if uinfo["username"] == username: return jsonify({"status": "fail", "msg": "❌ 帳號名稱已被註冊！"})
    uid = str(random.randint(100000, 999999))
    db[uid] = {"username": username, "password": password, "coins": 50000.0, "status": "normal"}
    save_db(db)
    return jsonify({"status": "success", "uid": uid, "username": username, "coins": 50000.0})

@app.route("/login", methods=["POST"])
def login():
    req = request.json or {}
    db = load_db()
    username = req.get("username", "").strip()
    password = req.get("password", "").strip()
    for uid, uinfo in db.items():
        if uinfo["username"] == username and uinfo["password"] == password:
            return jsonify({"status": "success", "uid": uid, "username": username, "coins": uinfo["coins"]})
    return jsonify({"status": "fail", "msg": "❌ 帳號或密碼輸入錯誤"})

@app.route("/request_payment", methods=["POST"])
def request_payment():
    req = request.json or {}
    uid = req.get("uid")
    twd_amount = int(req.get("amount", 50))
    if twd_amount <= 0: return jsonify({"status": "fail", "msg": "❌ 儲值金額異常"})
    db = load_db()
    if uid not in db: return jsonify({"status": "fail", "msg": "❌ 帳號異常"})
    trade_no = f"LB{int(time.time())}{random.randint(10,99)}"
    YOUR_SERVER_URL = "https://onrender.com" # 未來要換成你真實Render網址
    params = {
        "MerchantID": MERCHANT_ID, "MerchantTradeNo": trade_no,
        "MerchantTradeDate": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType": "aio", "TotalAmount": str(twd_amount),
        "TradeDesc": urllib.parse.quote_plus("LuckBlock娛樂城金幣儲值"),
        "ItemName": f"幸運方塊虛擬金幣{twd_amount*2000}枚",
        "ReturnURL": YOUR_SERVER_URL, "ChoosePayment": "LINEPAY", "EncryptType": "1"
    }
    params["CheckMacValue"] = generate_check_mac_value(params)
    db[uid]["pending_trade"] = {"trade_no": trade_no, "amount": twd_amount}
    save_db(db)
    return jsonify({"status": "success", "payment_params": params, "gateway_url": "https://ecpay.com.tw"})

@app.route("/payment_callback", methods=["POST"])
def payment_callback():
    res = request.form.to_dict()
    received_mac = res.pop("CheckMacValue", "")
    calculated_mac = generate_check_mac_value(res)
    if received_mac != calculated_mac: return "0|CheckMacValueFail"
    if res.get("RtnCode") == "1":
        trade_no = res.get("MerchantTradeNo")
        db = load_db()
        for uid, user in db.items():
            if user.get("pending_trade", {}).get("trade_no") == trade_no:
                twd = user["pending_trade"]["amount"]
                added_coins = twd * 2000.0 
                user["coins"] += added_coins
                user["pending_trade"] = {} 
                save_db(db)
                return "1|OK"
    return "0|Fail"

# 🎰 核心老虎機：連鎖消除補位 + 倍率球加總 + 68倍完美封頂
@app.route("/spin", methods=["POST"])
def spin():
    req = request.json or {}
    uid = req.get("uid")
    try: bet = float(req.get("bet", 0))
    except: return jsonify({"status": "fail", "msg": "❌ 下注金額格式錯誤！"})
        
    db = load_db()
    if uid not in db: return jsonify({"status": "fail", "msg": "❌ 帳號不存在！"})
    if bet <= 0: return jsonify({"status": "fail", "msg": "❌ 下注金額必須大於 0！"})
        
    user = db[uid]
    if user["coins"] < bet: return jsonify({"status": "fail", "msg": "❌ 餘額不足！"})
        
    user["coins"] -= bet  # 扣除下注本金
    
    # 🎲 莊家風控核心：35%大中獎局，65%未中獎或小散獎回收局
    roll = random.randint(1, 100)
    total_base_score = 0
    multiplier_pool = []
    
    # 初始化一個隨機盤面
    grid = [[random.choice(ITEMS) for _ in range(6)] for _ in range(6)]
    
    if roll <= 35:
        # 🟢 中獎局：模擬 1 到 3 次的「連鎖消除與新方塊掉落補位」
        combos = random.randint(1, 3)
        for _ in range(combos):
            lucky_item = random.choice(ITEMS)
            total_base_score += BASE_SCORES[lucky_item] * (bet / 20.0) # 依下注量比例放大底分
            
            # 掉落老闆要求的 50, 20, 15, 10 高等倍率球（保證不縮水低開）
            if random.randint(1, 100) <= 40:
                multiplier_pool.append(random.choice([10, 15, 20, 50]))
            else:
                multiplier_pool.append(random.choice([2, 3, 4, 5]))
    else:
        # 🔴 回收局：掉落低倍率球 2, 3, 4, 5
        if random.randint(1, 100) <= 25:
            multiplier_pool.append(random.choice([2, 3, 4, 5]))

    # 🧮 計算倍率球加總
    total_multiplier = sum(multiplier_pool) if multiplier_pool else 1
    
    # ⚠️ 【老闆指定黃金保險】：總加倍率最高 68 倍完美封頂！死死守住國庫！
    if total_multiplier > 68:
        total_multiplier = 68
        
    # 計算最終贏得金幣
    win_amount = total_base_score * total_multiplier
    
    if win_amount > 0:
        msg = f"💥 觸發連鎖消除補位！\n🔹 總消除底分: {total_base_score:,.0f} | 🔴 倍率球加總: x{total_multiplier}\n🎉 總共贏得金幣: +{win_amount:,.2f} ！"
    else:
        # 未中獎，強制用死迴圈清洗盤面，確保沒有任何元素大於等於 8 個
        while True:
            grid = [[random.choice(ITEMS) for _ in range(6)] for _ in range(6)]
            if all([item for row in grid for item in row].count(i) < 8 for i in ITEMS):
                break
        msg = "❄️ 未中獎，再接再厲！"
        
    user["coins"] += win_amount
    save_db(db)
    return jsonify({"status": "success", "grid": grid, "coins": user["coins"], "msg": msg})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
