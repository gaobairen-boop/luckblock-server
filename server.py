import os
import json
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import webbrowser  
import tempfile    
import random

# 🌐 連線你專屬亮綠燈營運中的雲端基地
SERVER_URL = "https://onrender.com" 

ITEMS = ["藍寶石", "紅寶石", "綠寶石", "獅子", "老虎", "老鷹", "鑽石", "飛機"]
COLORS = {
    "藍寶石": "#2196F3", "紅寶石": "#E91E63", "綠寶石": "#00E676",  
    "獅子": "#4CAF50", "老虎": "#9C27B0", "老鷹": "#FFC107",      
    "鑽石": "#00BCD4", "飛機": "#795548"                                             
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎰 LuckBlock 商業連線免作弊娛樂城 🎰")
        self.geometry("680x880")  
        self.configure(bg="#1A1A1A") 
        self.uid, self.username, self.coins = None, None, 0.0
        self.msg = "請登入官方線上帳號中心..."
        self.grid_labels = [[None]*6 for _ in range(6)]
        self.show_login_frame()

    def show_login_frame(self):
        self.clear_frame()
        frame = tk.Frame(self, bg="#2C3E50", padx=30, pady=25, bd=2, relief="ridge")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text="🎰 遠端連線安全登入系統", font=("Microsoft JhengHei", 14, "bold"), fg="#F1C40F", bg="#2C3E50").pack(pady=10)
        tk.Label(frame, text="請輸入帳號：", font=("Microsoft JhengHei", 10), fg="white", bg="#2C3E50").pack(anchor="w", padx=5)
        self.ent_name = tk.Entry(frame, font=("Arial", 12), width=23)
        self.ent_name.pack(pady=5)
        tk.Label(frame, text="請輸入密碼：", font=("Microsoft JhengHei", 10), fg="white", bg="#2C3E50").pack(anchor="w", padx=5)
        self.ent_pwd = tk.Entry(frame, font=("Arial", 12), width=23, show="*")
        self.ent_pwd.pack(pady=5)
        btn_frame = tk.Frame(frame, bg="#2C3E50")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="🔑 連線登入", font=("Microsoft JhengHei", 10, "bold"), bg="#2ECC71", fg="white", width=10, command=self.on_login).pack(side="left", padx=5)
        tk.Button(btn_frame, text="📝 註冊新號", font=("Microsoft JhengHei", 10, "bold"), bg="#3498DB", fg="white", width=10, command=self.on_register).pack(side="right", padx=5)

    def on_login(self):
        if not self.ent_name.get().strip() or not self.ent_pwd.get().strip(): return
        try:
            res = requests.post(f"{SERVER_URL}/login", json={"username": self.ent_name.get().strip(), "password": self.ent_pwd.get().strip()}, timeout=5).json()
            if res["status"] == "success":
                self.uid, self.username, self.coins = res["uid"], res["username"], res["coins"]
                self.show_game_frame()
            else: messagebox.showerror("失敗", res["msg"])
        except Exception: 
            messagebox.showerror("網路提示", "❌ 雲端大腦此時正在休眠中！\n請重新點擊再試一次即可叫醒它！")

    def on_register(self):
        if not self.ent_name.get().strip() or not self.ent_pwd.get().strip(): return
        try:
            res = requests.post(f"{SERVER_URL}/register", json={"username": self.ent_name.get().strip(), "password": self.ent_pwd.get().strip()}, timeout=5).json()
            if res["status"] == "success": messagebox.showinfo("成功", f"🎉 註冊成功！ UID: {res['uid']}")
            else: messagebox.showwarning("提示", res["msg"])
        except Exception: 
            messagebox.showerror("網路提示", "❌ 雲端大腦此時正在休眠中！\n請重新點擊再試一次即可叫醒它！")

    def show_game_frame(self):
        self.clear_frame()
        status_frame = tk.Frame(self, bg="#111111", pady=8)
        status_frame.pack(fill="x")
        self.lbl_user = tk.Label(status_frame, text="", font=("Microsoft JhengHei", 11, "bold"), fg="#ECF0F1", bg="#111111")
        self.lbl_user.pack(side="left", padx=15)
        self.lbl_coins = tk.Label(status_frame, text="", font=("Arial", 12, "bold"), fg="#F1C40F", bg="#111111")
        self.lbl_coins.pack(side="right", padx=15)
        
        tk.Button(status_frame, text="📊 官方開獎機率", font=("Microsoft JhengHei", 9, "bold"), bg="#9B59B6", fg="white", bd=0, padx=8, pady=2, command=self.show_probability_window).pack(side="right", padx=10)
        tk.Button(status_frame, text="🔄 刷新餘額", font=("Microsoft JhengHei", 9, "bold"), bg="#34495E", fg="white", bd=0, padx=8, pady=2, command=self.refresh_balance).pack(side="right", padx=5)

        tk.Frame(self, bg="#1A1A1A", height=15).pack()

        grid_outer = tk.Frame(self, bg="#2C3E50", padx=8, pady=8, bd=3, relief="sunken")
        grid_outer.pack(pady=10)
        for r in range(6):
            for c in range(6):
                lbl = tk.Label(grid_outer, text="方塊", font=("Microsoft JhengHei", 10, "bold"), width=7, height=3, relief="raised", bd=1)
                lbl.grid(row=r, column=c, padx=2, pady=2)
                self.grid_labels[r][c] = lbl
                
        self.lbl_msg = tk.Label(self, text="", font=("Microsoft JhengHei", 10, "bold"), fg="#F1C40F", bg="#2C3E50", width=65, height=3, bd=1, relief="solid", justify="center")
        self.lbl_msg.pack(pady=10)
        
        bet_control_frame = tk.Frame(self, bg="#1A1A1A")
        bet_control_frame.pack(pady=5)
        tk.Label(bet_control_frame, text="💰 請輸入下注金額：", font=("Microsoft JhengHei", 11, "bold"), fg="white", bg="#1A1A1A").pack(side="left", padx=5)
        self.ent_bet = tk.Entry(bet_control_frame, font=("Arial", 12, "bold"), width=10, justify="center")
        self.ent_bet.insert(0, "20.0") 
        self.ent_bet.pack(side="left", padx=5)
        
        ctrl_frame = tk.Frame(self, bg="#1A1A1A", padx=10, pady=10)
        ctrl_frame.pack(pady=10)
        tk.Button(ctrl_frame, text="🎰 搖桿啟動", font=("Microsoft JhengHei", 11, "bold"), bg="#2ECC71", fg="white", width=14, command=self.on_spin).pack(side="left", padx=5)
        self.update_ui(None)

    def show_probability_window(self):
        pop = tk.Toplevel(self)
        pop.title("📊 LuckBlock 官方機率公告欄")
        pop.geometry("450x300")
        pop.configure(bg="#1E1E1E")
        pop.resizable(False, False)
        
        tk.Label(pop, text="🎰 LuckBlock 官方出獎機率公告", font=("Microsoft JhengHei", 12, "bold"), fg="#F1C40F", bg="#1E1E1E").pack(pady=15)
        info_text = (
            "🟢 【低等局】藍寶石 / 紅寶石 / 綠寶石 ➔ 綠光聖芒\n"
            "🟣 【中等局】獅子 / 老虎 / 老鷹 ➔ 絢麗紫光\n"
            "🔴 【高等局】鑽石特獎 ➔ 燃燒紅光\n"
            "🟡 【最高等】飛機神話大滿貫 ➔ 閃耀金光\n\n"
            "📈 官方全台綜合出獎率：32.00% (有來有回)\n"
            "🔒 莊家風控總加倍率上限：68 倍完美封頂\n"
            "💎 儲值比例 ➔ 1 : 100"
        )
        tk.Label(pop, text=info_text, font=("Microsoft JhengHei", 10, "bold"), fg="#ECF0F1", bg="#1E1E1E", justify="left", padx=20).pack(fill="x")
        tk.Button(pop, text="確認知悉", font=("Microsoft JhengHei", 9, "bold"), bg="#E67E22", fg="white", bd=0, width=12, pady=5, command=pop.destroy).pack(pady=20)

    def update_ui(self, server_grid):
        self.lbl_user.config(text=f"👤 玩家：{self.username} (UID: {self.uid})")
        self.lbl_coins.config(text=f"官方餘額: {self.coins:,.2f} ")
        self.lbl_msg.config(text=self.msg)
        if server_grid:
            for r in range(6):
                for c in range(6):
                    item_name = server_grid[r][c]
                    self.grid_labels[r][c].config(text=item_name, bg=COLORS.get(item_name, "#FFFFFF"), fg="white")

    def refresh_balance(self):
        try:
            res = requests.post(f"{SERVER_URL}/login", json={"username": self.username, "password": self.ent_pwd.get().strip()}, timeout=5).json()
            if res["status"] == "success":
                self.coins = res["coins"]
                self.update_ui(None)
        except Exception: pass

    def on_spin(self):
        try:
            bet_val = float(self.ent_bet.get().strip())
            if bet_val <= 0: return
        except: return

        try:
            res = requests.post(f"{SERVER_URL}/spin", json={"uid": self.uid, "bet": bet_val}, timeout=5).json()
            if res["status"] == "success":
                self.play_cascade_animation(res["history"], res["grid"], res["coins"], res["msg"])
            else: messagebox.showwarning("提示", res["msg"])
        except Exception: messagebox.showerror("錯誤", "連線中斷")

    def play_cascade_animation(self, history, final_grid, final_coins, final_msg, index=0):
        if index < len(history):
            wave = history[index]
            current_grid = wave["grid"]
            
            if wave["action"] == "clear":
                target = wave["target"]
                
                if target in ["藍寶石", "紅寶石", "綠寶石"]:
                    flash_color = "#00E676"  
                    rank_name = "【低等寶石局】"
                elif target in ["獅子", "老虎", "老鷹"]:
                    flash_color = "#9C27B0"  
                    rank_name = "【中等猛獸局】"
                elif target == "鑽石":
                    flash_color = "#FF3333"  
                    rank_name = "【高等鑽石局】"
                else:
                    flash_color = "#FFD700"  
                    rank_name = "【最高等飛機神話局】"

                self.lbl_msg.config(text=f"✨ 鎖定成功！🎯 觸發{rank_name}【{target}】集滿 8 個消除！")
                
                def flash_effect(step=0):
                    if step < 6:
                        current_color = flash_color if step % 2 == 0 else "#FFFFFF"
                        for r in range(6):
                            for c in range(6):
                                if current_grid[r][c] == target:
                                    self.grid_labels[r][c].config(bg=current_color, fg="#000000")
                        self.after(80, lambda: flash_effect(step + 1))
                    else:
                        fireworks = ["🎆", "✨", "🔥", "💥", "⚡", "🌟"]
                        for r in range(6):
                            for c in range(6):
                                if current_grid[r][c] == target:
                                    self.grid_labels[r][c].config(text=random.choice(fireworks) + "煙火", bg="#FFFFFF", fg=flash_color)
                                else:
                                    self.grid_labels[r][c].config(text=current_grid[r][c], bg=COLORS.get(current_grid[r][c], "#FFFFFF"), fg="white")
    def play_cascade_animation(self, history, final_grid, final_coins, final_msg, index=0):
        if index < len(history):
            wave = history[index]
            current_grid = wave["grid"]
            
            if wave["action"] == "clear":
                target = wave["target"]
                
                if target in ["藍寶石", "紅寶石", "綠寶石"]:
                    flash_color = "#00E676"  # 🟢 綠光
                    rank_name = "【低等寶石局】"
                elif target in ["獅子", "老虎", "老鷹"]:
                    flash_color = "#9C27B0"  # 🟣 紫光
                    rank_name = "【中等猛獸局】"
                elif target == "鑽石":
                    flash_color = "#FF3333"  # 🔴 紅光
                    rank_name = "【高等鑽石局】"
                else:
                    flash_color = "#FFD700"  # 🟡 金光
                    rank_name = "【最高等飛機神話局】"

                self.lbl_msg.config(text=f"✨ 鎖定成功！🎯 觸發{rank_name}【{target}】集滿 8 個消除！")
                
                def flash_effect(step=0):
                    if step < 6:
                        current_color = flash_color if step % 2 == 0 else "#FFFFFF"
                        for r in range(6):
                            for c in range(6):
                                if current_grid[r][c] == target:
                                    self.grid_labels[r][c].config(bg=current_color, fg="#000000")
                        self.after(80, lambda: flash_effect(step + 1))
                    else:
                        fireworks = ["🎆", "✨", "🔥", "💥", "⚡", "🌟"]
                        for r in range(6):
                            for c in range(6):
                                if current_grid[r][c] == target:
                                    self.grid_labels[r][c].config(text=random.choice(fireworks) + "煙火", bg="#FFFFFF", fg=flash_color)
                                else:
                                    self.grid_labels[r][c].config(text=current_grid[r][c], bg=COLORS.get(current_grid[r][c], "#FFFFFF"), fg="white")
                        
                        self.lbl_msg.config(text="🎆 轟隆隆！全螢幕大煙火連環引爆！正在震碎方塊中...")
                        self.after(450, lambda: self.play_cascade_animation(history, final_grid, final_coins, final_msg, index + 1))
                
                flash_effect()
                
            elif wave["action"] == "drop":
                self.update_ui(current_grid)
                self.lbl_msg.config(text="⬇️ 煙火散去！空位已由上方全新方塊如瀑布般完美掉落補位！")
                self.after(450, lambda: self.play_cascade_animation(history, final_grid, final_coins, final_msg, index + 1))
            else:
                self.update_ui(current_grid)
                self.after(200, lambda: self.play_cascade_animation(history, final_grid, final_coins, final_msg, index + 1))
        else:
            self.coins = final_coins
            self.msg = final_msg
            self.update_ui(final_grid)

    def clear_frame(self):
        for widget in self.winfo_children(): 
            widget.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
