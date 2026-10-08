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

# 🚀 綠界科技真實金流測試帳號設定 (串接真實 LINE Pay 用，上線後可換成你的正式商店金鑰)
MERCHANT_ID = "2000132"
HASH_KEY = "5294y06JbISpM5x9"
HASH_IV = "v77hoKGq4kWxPxWD"

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

# 🔐 綠界金流專用檢查碼計算 (商業級安全加密，駭客無法竄改)
def generate_check_mac_value(params):
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    raw_str = f"HashKey={HASH_KEY}&" + "&".join([f"{k}={v}" for k, v in sorted_params]) + f"&HashIV={HASH_IV}"
    url_encoded = urllib.parse.quote_plus(raw_str).lower()
    return hashlib.sha256(url_encoded.encode('utf-8')).hexdigest().upper()

@app.route("/register", methods=["POST"])
def register():
    req = request.json
    db = load_db()
    username = req.get("username", "").strip()
    password = req.get("password", "").strip()
    for uid, uinfo in db.items():
        if uinfo["username"] == username: return jsonify({"status": "fail", "msg": "❌ 帳號名稱已被註冊！"})
    uid = str(random.randint(100000, 999999))
    db[uid] = {"username": username, "password": password, "coins": 50000.0, "status": "normal", "ban_until": ""}
    save_db(db)
    return jsonify({"status": "success", "uid": uid, "username": username, "coins": 50000.0})

@app.route("/login", methods=["POST"])
def login():
    req = request.json
    db = load_db()
    username = req.get("username", "").strip()
    password = req.get("password", "").strip()
    for uid, uinfo in db.items():
        if uinfo["username"] == username and uinfo["password"] == password:
            if uinfo.get("status") == "banned":
                return jsonify({"status": "fail", "msg": "⚠️ 該帳戶已被官方永久封禁 10 年！"})
            return jsonify({"status": "success", "uid": uid, "username": username, "coins": uinfo["coins"]})
    return jsonify({"status": "fail", "msg": "❌ 帳號或密碼輸入錯誤"})

# 💳 核心：產生真正的 LINE Pay 付款訂單發射給玩家！
@app.route("/request_payment", methods=["POST"])
def request_payment():
    req = request.json
    uid = req.get("uid")
    twd_amount = int(req.get("amount", 50)) # 預設儲值 50 元台幣
    
    db = load_db()
    if uid not in db: return jsonify({"status": "fail", "msg": "帳號異常"})
    
    trade_no = f"LB{int(time.time())}{random.randint(10,99)}"
    
    # 建立符合台灣金流法規的正式訂單參數
    params = {
        "MerchantID": MERCHANT_ID,
        "MerchantTradeNo": trade_no,
        "MerchantTradeDate": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType": "aio",
        "TotalAmount": str(twd_amount),
        "TradeDesc": urllib.parse.quote_plus("LuckBlock娛樂城金幣儲值"),
        "ItemName": f"幸運方塊虛擬金幣{twd_amount*2000}枚",
        "ReturnURL": "https://onrender.com", # 告訴金流付完錢後通知我們
        "ChoosePayment": "LINEPAY", # 強制指定真 LINE Pay 付款
        "EncryptType": "1"
    }
    params["CheckMacValue"] = generate_check_mac_value(params)
    
    # 將這筆未付款訂單先記錄在伺服器，等金流扣款成功通知
    db[uid]["pending_trade"] = {"trade_no": trade_no, "amount": twd_amount}
    save_db(db)
    
    return jsonify({"status": "success", "payment_params": params, "gateway_url": "https://ecpay.com.tw"})

# 🔔 金流公司扣款成功後，會自動遠端呼叫這個網址，自動幫玩家儲值到帳！
@app.route("/payment_callback", methods=["POST"])
def payment_callback():
    # 商業自動到帳核心：收到綠界科技扣款成功的祕密通知，自動幫玩家加錢並存檔！
    res = request.form.to_dict()
    if res.get("RtnCode") == "1": # RtnCode 1 代表玩家真的付清台幣了！
        trade_no = res.get("MerchantTradeNo")
        db = load_db()
        for uid, user in db.items():
            if user.get("pending_trade", {}).get("trade_no") == trade_no:
                twd = user["pending_trade"]["amount"]
                added_coins = twd * 2000.0 # 1元台幣換2000金幣
                user["coins"] += added_coins
                user["pending_trade"] = {} # 清空暫存訂單
                save_db(db)
                print(f"💰 [金流成功] 玩家 UID {uid} 成功透過 LINE Pay 儲值台幣 {twd} 元，系統自動補幣 +{added_coins}！")
                return "1|OK"
    return "0|Fail"

@app.route("/spin", methods=["POST"])
def spin():
    req = request.json
    uid = req.get("uid")
    bet = float(req.get("bet"))
    db = load_db()
    user = db[uid]
    if user["coins"] < bet: return jsonify({"status": "fail", "msg": "❌ 餘額不足，請使用 LINE Pay 儲值！"})
    user["coins"] -= bet
    items = ["獅子","老鷹","老虎","藍寶石","紅寶石","鑽石","飛機"]
    grid = [[random.choice(items) for _ in range(6)] for _ in range(6)]
    flat_grid = [item for row in grid for item in row]
    win_amount = (bet * 5.0) if flat_grid.count("鑽石") >= 8 else 0.0
    user["coins"] += win_amount
    save_db(db)
    return jsonify({"status": "success", "grid": grid, "coins": user["coins"], "msg": f"🎰 下注完成！贏得 {win_amount} 金幣！" if win_amount > 0 else "❄️ 未中獎"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)