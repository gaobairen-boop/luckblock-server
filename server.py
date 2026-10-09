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
SUPER_BOSS_MASTER_KEY = "SUPER_BOSS_999_TOKEN"

ITEMS = ["藍寶石", "紅寶石", "綠寶石", "獅子", "老虎", "老鷹", "鑽石", "飛機"]

# 📊 【老闆指示：底分全面縮小 5~10 倍，防止莊家虧損！】
BASE_SCORES = {
    "藍寶石": 2, "紅寶石": 2, "綠寶石": 2,      # 便宜級：從 15 點砍到剩 2 點
    "獅子": 5, "老虎": 5, "老鷹": 5,            # 中等級：從 50 點砍到剩 5 點
    "鑽石": 15,                                # 高等級：從 150 點砍到剩 15 點
    "飛機": 30                                 # 最高等：從 500 點大砍到剩 30 點
}

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def generate_check_mac_value(params):
    sorted_params = sorted(params.items(), key=lambda x: x)
    raw_str = f"HashKey={HASH_KEY}&" + "&".join([f"{k}={v}" for k, v in sorted_params]) + f"&HashIV={HASH_IV}"
    url_encoded = urllib.parse.quote_plus(raw_str).lower()
    return hashlib.sha256(url_encoded.encode('utf-8')).hexdigest().upper()

@app.route("/register", methods=["POST"])
def register():
    req = request.json or {}
    db = load_db()
    username = req.get("username", "").strip()
    password = req.get("password", "").strip()
    if not username or not password: return jsonify({"status": "fail", "msg": "❌ 不能為空！"})
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
    return jsonify({"status": "fail", "msg": "❌ 帳號或密碼錯誤"})

@app.route("/request_payment", methods=["POST"])
def request_payment():
    req = request.json or {}
    uid = req.get("uid")
    twd_amount = int(req.get("amount", 50))
    db = load_db()
    trade_no = f"LB{int(time.time())}{random.randint(10,99)}"
    params = {
        "MerchantID": MERCHANT_ID, "MerchantTradeNo": trade_no,
        "MerchantTradeDate": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType": "aio", "TotalAmount": str(twd_amount),
        "TradeDesc": urllib.parse.quote_plus("LuckBlock娛樂城金幣儲值"),
        "ItemName": f"幸運方塊虛擬金幣{twd_amount*100}枚",
        "ReturnURL": "https://onrender.com", 
        "ChoosePayment": "LINEPAY", "EncryptType": "1"
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
                added_coins = twd * 100.0  # 🌟 老闆修正：1元台幣固定換100金幣
                user["coins"] += added_coins
                user["pending_trade"] = {}
                save_db(db)
                return "1|OK"
    return "0|Fail"

@app.route("/spin", methods=["POST"])
def spin():
    req = request.json or {}
    uid = req.get("uid")
    try: bet = float(req.get("bet", 0))
    except: return jsonify({"status": "fail", "msg": "❌ 下注格式錯誤！"})
        
    db = load_db()
    user = db[uid]
    if user["coins"] < bet: return jsonify({"status": "fail", "msg": "❌ 餘額不足！"})
        
    user["coins"] -= bet  # 扣除本金
    
    # 🔒 【極致收水風控】：中獎率直接大砍到只剩 15%！莊家立於不敗之地
    roll = random.randint(1, 100)
    total_base_score = 0
    multiplier_pool = []
    
    if roll <= 15:
        # 🟢 15% 機率中獎：只給 1 次基礎消除，且倍率球極小化！
        lucky_item = random.choice(ITEMS)
        total_base_score = BASE_SCORES[lucky_item] * (bet / 20.0)
        # 調整倍率球池：只給極小的 2, 3, 4, 5 倍，50倍和20倍機率大砍到幾乎不出！
        multiplier_pool.append(random.choice([2, 2, 2, 3, 3, 4, 5]))
    
    total_multiplier = sum(multiplier_pool) if multiplier_pool else 1
    if total_multiplier > 68: total_multiplier = 68
        
    win_amount = total_base_score * total_multiplier
    
    if win_amount > 0:
        grid = [[random.choice(ITEMS) for _ in range(6)] for _ in range(6)]
        msg = f"💥 觸發消除！\n🔹 消除底分: {total_base_score:,.1f} | 🔴 倍率球: x{total_multiplier}\n🎉 贏得金幣: +{win_amount:,.2f}"
    else:
        # 🔴 85% 絕對死局：強制清洗盤面，絕不讓任何方塊滿 8 個
        while True:
            grid = [[random.choice(ITEMS) for _ in range(6)] for _ in range(6)]
            if all([item for row in grid for item in row].count(i) < 8 for i in ITEMS): break
        win_amount = 0.0
        msg = "❄️ 未中獎，再接再厲！"
        
    user["coins"] += win_amount
    save_db(db)
    return jsonify({"status": "success", "grid": grid, "coins": user["coins"], "msg": msg})

@app.route('/admin_get_all_players', methods=['POST'])
def admin_get_all_players():
    req = request.json or {}
    if req.get('admin_uid') == SUPER_BOSS_MASTER_KEY:
        db = load_db()
        return jsonify({"status": "success", "data": {uid: {"username": u["username"], "coins": u["coins"]} for uid, u in db.items()}})
    return jsonify({"status": "fail"}), 403

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
