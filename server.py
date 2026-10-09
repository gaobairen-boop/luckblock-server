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

BASE_SCORES = {
    "藍寶石": 2, "紅寶石": 2, "綠寶石": 2,      
    "獅子": 4, "老虎": 4, "老鷹": 4,            
    "鑽石": 10,                                
    "飛機": 20                                 
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

# 👤 模擬方塊掉落補位的核心演算法
def simulate_cascade():
    # 隨機產生初始盤面
    grid = [[random.choice(ITEMS) for _ in range(6)] for _ in range(6)]
    history = [] # 記錄每一次消除與掉落的過程，傳給前端做動態
    total_base = 0
    
    # 模擬 1~2 次的消除掉落補位
    for wave in range(random.randint(1, 2)):
        flat = [item for row in grid for item in row]
        to_erase = None
        for item in ITEMS:
            if flat.count(item) >= 8:
                to_erase = item
                break
        
        if not to_erase:
            # 如果初始就沒滿8個，隨機挑一個製造滿8個消除
            to_erase = random.choice(ITEMS)
            count = flat.count(to_erase)
            while count < 8:
                r, c = random.randint(0, 5), random.randint(0, 5)
                if grid[r][c] != to_erase:
                    grid[r][c] = to_erase
                    count += 1
                    
        # 記錄消除前的狀態
        history.append({"action": "clear", "grid": [row[:] for row in grid], "target": to_erase})
        total_base += BASE_SCORES[to_erase]
        
        # 核心：執行「方塊不見、上方掉落補位」演算法
        for c in range(6):
            # 取出這一行所有沒被消除的物件
            remain_items = [grid[r][c] for r in range(6) if grid[r][c] != to_erase]
            # 不夠的在最上方掉入全新物件補滿 6 個
            while len(remain_items) < 6:
                remain_items.insert(0, random.choice(ITEMS))
            # 填回盤面
            for r in range(6):
                grid[r][c] = remain_items[r]
                
        # 記錄掉落補位後的全新狀態
        history.append({"action": "drop", "grid": [row[:] for row in grid]})
        
    return history, total_base, grid

@app.route("/spin", methods=["POST"])
def spin():
    req = request.json or {}
    uid = req.get("uid")
    try: bet = float(req.get("bet", 0))
    except: return jsonify({"status": "fail", "msg": "❌ 格式錯誤"})
        
    db = load_db()
    user = db[uid]
    if user["coins"] < bet: return jsonify({"status": "fail", "msg": "❌ 餘額不足"})
    user["coins"] -= bet
    
    roll = random.randint(1, 100)
    multiplier_pool = []
    
    if roll <= 30: # 30% 偽贏分局與大獎局
        history, total_base, final_grid = simulate_cascade()
        total_base_score = total_base * (bet / 20.0)
        multiplier_pool.append(random.choice([2, 3, 4, 5]))
    else: # 70% 鋼鐵回收死局
        while True:
            final_grid = [[random.choice(ITEMS) for _ in range(6)] for _ in range(6)]
            if all([item for row in final_grid for item in row].count(i) < 8 for i in ITEMS): break
        history = [{"action": "final", "grid": final_grid}]
        total_base_score = 0
        
    total_multiplier = sum(multiplier_pool) if multiplier_pool else 1
    win_amount = total_base_score * total_multiplier
    
    if win_amount > 0:
        msg = f"💥 觸發連鎖消除！\n🔹 總消除底分: {total_base_score:,.1f} | 🔴 倍率球: x{total_multiplier}\n🎉 贏得金幣: +{win_amount:,.2f}"
    else:
        msg = "❄️ 未中獎，再接再厲！"
        
    user["coins"] += win_amount
    save_db(db)
    return jsonify({"status": "success", "history": history, "grid": final_grid, "coins": user["coins"], "msg": msg})

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
