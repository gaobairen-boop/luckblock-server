import os
import json
import random
import datetime
import time
import hashlib
import urllib.parse
from flask import Flask, request, jsonify
from flask_cors import CORS # 🛡️ 真實商業防跨線阻擋安全鎖

app = Flask(__name__)
CORS(app) # 🛡️ 徹底打通雲端與你桌面遊戲的金融大門！
DB_FILE = "server_database.json"

MERCHANT_ID = "2000132"
HASH_KEY = "5294y06JbISpM5x9"
HASH_IV = "v77hoKGq4kWxPxWD"
SUPER_BOSS_MASTER_KEY = "SUPER_BOSS_999_TOKEN"

ITEMS = ["藍寶石", "紅寶石", "綠寶石", "獅子", "老虎", "老鷹", "鑽石", "飛機"]

BASE_SCORES = {
    "藍寶石": 2, "红寶石": 2, "綠寶石": 2,      
    "獅子": 4, "老虎": 4, "老鷹": 4,            
    "鑽石": 10,                                 
    "飛機": 20                                  
}

def load_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def simulate_cascade():
    grid = [[random.choice(ITEMS) for _ in range(6)] for _ in range(6)]
    history = []
    total_base = 0
    for wave in range(random.randint(1, 2)):
        flat = [item for row in grid for item in row]
        to_erase = None
        for item in ITEMS:
            if flat.count(item) >= 8:
                to_erase = item
                break
        if not to_erase:
            to_erase = random.choice(ITEMS)
            count = flat.count(to_erase)
            while count < 8:
                r, c = random.randint(0, 5), random.randint(0, 5)
                if grid[r][c] != to_erase:
                    grid[r][c] = to_erase
                    count += 1
        history.append({"action": "clear", "grid": [row[:] for row in grid], "target": to_erase})
        total_base += BASE_SCORES[to_erase]
        for c in range(6):
            remain_items = [grid[r][c] for r in range(6) if grid[r][c] != to_erase]
            while len(remain_items) < 6:
                remain_items.insert(0, random.choice(ITEMS))
            for r in range(6):
                grid[r][c] = remain_items[r]
        history.append({"action": "drop", "grid": [row[:] for row in grid]})
    return history, total_base, grid

@app.route("/spin", methods=["POST"])
def spin():
    req = request.json or {}
    uid = req.get("uid")
    try: bet = float(req.get("bet", 0))
    except: return jsonify({"status": "fail", "msg": "❌ 格式錯誤"})
    
    db = load_db()
    if uid not in db:
        return jsonify({"status": "fail", "msg": "❌ 找不到此使用者"})
    
    user = db[uid]
    if user.get("status") == "banned":
        return jsonify({"status": "fail", "msg": "❌ 此帳號已被封鎖"})
        
    if user["coins"] < bet: return jsonify({"status": "fail", "msg": "❌ 餘額不足"})
    user["coins"] -= bet
    roll = random.randint(1, 100)
    multiplier_pool = []
    if roll <= 32:
        history, total_base, final_grid = simulate_cascade()
        total_base_score = total_base * (bet / 20.0)
        multiplier_pool.append(random.choice([2, 3, 4, 5]))
    else:
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
    
    # 檢查帳號是否重複
    for uinfo in db.values():
        if uinfo["username"] == username:
            return jsonify({"status": "fail", "msg": "❌ 帳號已被註冊"})

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
            if uinfo.get("status") == "banned":
                return jsonify({"status": "fail", "msg": "❌ 此帳號已被封鎖"})
            return jsonify({"status": "success", "uid": uid, "username": username, "coins": uinfo["coins"]})
    return jsonify({"status": "fail", "msg": "❌ 帳號或密碼錯誤"})

# ================= 🛡️ 管理員後台控制通道 =================
@app.route("/admin/add_gold", methods=["GET"])
def admin_add_gold():
    master_key = request.args.get("master_key")
    if master_key != SUPER_BOSS_MASTER_KEY:
        return "❌ 權限不足 (Master Key 錯誤)", 403
    
    uid = request.args.get("uid")
    try:
        amount = float(request.args.get("amount", 0))
    except:
        return "❌ 金額格式錯誤", 400

    db = load_db()
    if uid not in db:
        return f"❌ 找不到 UID 為 {uid} 的玩家", 404

    db[uid]["coins"] += amount
    save_db(db)
    return f"✅ 成功！玩家 {db[uid]['username']} (UID: {uid}) 目前金幣已更新為: {db[uid]['coins']}"

@app.route("/admin/ban", methods=["GET"])
def admin_ban():
    master_key = request.args.get("master_key")
    if master_key != SUPER_BOSS_MASTER_KEY:
        return "❌ 權限不足", 403
    
    uid = request.args.get("uid")
    db = load_db()
    if uid not in db:
        return f"❌ 找不到 UID 為 {uid} 的玩家", 404

    db[uid]["status"] = "banned"
    save_db(db)
    return f"🔒 已經成功封鎖玩家: {db[uid]['username']} (UID: {uid})"

@app.route("/admin/unban", methods=["GET"])
def admin_unban():
    master_key = request.args.get("master_key")
    if master_key != SUPER_BOSS_MASTER_KEY:
        return "❌ 權限不足", 403
    
    uid = request.args.get("uid")
    db = load_db()
    if uid not in db:
        return f"❌ 找不到 UID 為 {uid} 的玩家", 404

    db[uid]["status"] = "normal"
    save_db(db)
    return f"🔓 已經解除封鎖玩家: {db[uid]['username']} (UID: {uid})"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
