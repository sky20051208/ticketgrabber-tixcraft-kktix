# gui.py (正式版 V17.1 - 修正打包後路徑辨識問題)

import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import os
import sys
import re

if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)  # 打包後：exe 所在資料夾
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 開發時：py 所在資料夾

CONFIG_FILE = os.path.join(_BASE_DIR, "config.py")
PAUSE_FILE = os.path.join(_BASE_DIR, "pause.lock")


class TicketBotLauncher:
    def __init__(self, root):
        self.root = root
        # [V17.0] 更新標題
        self.root.title("全平台搶票機器人控制台 V17.1 (Tixcraft/KKTIX/TicketPlus)")
        self.root.geometry("550x750") # 高度稍微增加
        
        # 啟動時自動清除殘留的暫停檔
        if os.path.exists(PAUSE_FILE):
            try: os.remove(PAUSE_FILE)
            except: pass

        self.bot_process = None
        style = ttk.Style()
        style.theme_use('clam')
        
        self.create_widgets()
        self.load_config_to_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # [V17.0] 更新標題文字
        title_label = tk.Label(self.root, text="🚀 搶票啟動器 (拓元/KKTIX/遠大)", font=("Microsoft JhengHei", 16, "bold"))
        title_label.pack(pady=15)

        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=5, fill="x")

        # --- [V17.0 更新] 平台選擇 ---
        tk.Label(frame, text="選擇搶票平台 (PLATFORM):", font=("Microsoft JhengHei", 10, "bold"), fg="red").pack(anchor="w")
        # 新增 "TICKETPLUS" 選項
        self.combo_platform = ttk.Combobox(frame, values=["TIXCRAFT", "KKTIX", "TICKETPLUS"], state="readonly", font=("Consolas", 10))
        self.combo_platform.current(0)
        self.combo_platform.pack(fill="x", pady=(0, 10))

        # 1. 網址
        tk.Label(frame, text="監控網址 (TIME_WATCH_URL):", font=("Microsoft JhengHei", 10)).pack(anchor="w")
        self.entry_url = tk.Entry(frame, font=("Consolas", 10))
        self.entry_url.pack(fill="x", pady=(0, 10))

        # 定時待命
        self.var_enable_timer = tk.BooleanVar(value=True)
        self.chk_timer = tk.Checkbutton(frame, text="啟用定時待命 (Time Watcher)", variable=self.var_enable_timer, command=self.on_timer_toggle, font=("Microsoft JhengHei", 10, "bold"))
        self.chk_timer.pack(anchor="w", pady=(5, 0))

        # 2. 時間
        tk.Label(frame, text="開賣時間 (TARGET_TIME):", font=("Microsoft JhengHei", 10)).pack(anchor="w")
        self.entry_time = tk.Entry(frame, font=("Consolas", 10))
        self.entry_time.pack(fill="x", pady=(0, 10))

        # --- 日期關鍵字 ---
        self.var_enable_date = tk.BooleanVar(value=False)
        self.chk_date = tk.Checkbutton(frame, text="啟用日期篩選 (WANTED_DATE_KEYWORD)", variable=self.var_enable_date, command=self.on_date_toggle, font=("Microsoft JhengHei", 10, "bold"), fg="#006400")
        self.chk_date.pack(anchor="w", pady=(5, 0))
        
        self.entry_date = tk.Entry(frame, font=("Microsoft JhengHei", 10))
        self.entry_date.pack(fill="x", pady=(0, 10))

        # 3. 選位策略
        tk.Label(frame, text="選位策略 (AREA_MODE):", font=("Microsoft JhengHei", 10, "bold"), fg="blue").pack(anchor="w")
        self.combo_mode = ttk.Combobox(frame, values=["關鍵字優先", "由上而下", "由下而上", "隨機"], state="readonly", font=("Microsoft JhengHei", 10))
        self.combo_mode.current(0)
        self.combo_mode.pack(fill="x", pady=(0, 5))
        self.combo_mode.bind("<<ComboboxSelected>>", self.on_mode_change)

        # 4. 區域/價格關鍵字
        tk.Label(frame, text="區域或價格關鍵字 (WANTED_AREA_KEYWORD):", font=("Microsoft JhengHei", 10)).pack(anchor="w")
        self.entry_area = tk.Entry(frame, font=("Microsoft JhengHei", 10))
        self.entry_area.pack(fill="x", pady=(0, 10))

        # 排除關鍵字
        tk.Label(frame, text="排除關鍵字 (EXCLUDE):", font=("Microsoft JhengHei", 10)).pack(anchor="w")
        self.entry_exclude = tk.Entry(frame, font=("Microsoft JhengHei", 10))
        self.entry_exclude.pack(fill="x", pady=(0, 10))

        # 預購碼
        tk.Label(frame, text="會員/信用卡預購碼 (PRE_ORDER_CODE):", font=("Microsoft JhengHei", 10, "bold"), fg="purple").pack(anchor="w")
        self.entry_precode = tk.Entry(frame, font=("Consolas", 10))
        self.entry_precode.pack(fill="x", pady=(0, 10))

        # 5. 張數
        tk.Label(frame, text="張數 (WANTED_TICKET_COUNT):", font=("Microsoft JhengHei", 10)).pack(anchor="w")
        self.combo_ticket = ttk.Combobox(frame, values=["1", "2", "3", "4"], state="readonly", font=("Consolas", 10))
        self.combo_ticket.current(1)
        self.combo_ticket.pack(fill="x", pady=(0, 20))

        # --- 按鈕區 ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        btn_save = tk.Button(btn_frame, text="💾 僅儲存", command=self.save_config_from_ui, width=10, height=2, bg="#dddddd", font=("Microsoft JhengHei", 10))
        btn_save.pack(side="left", padx=5)

        self.btn_pause = tk.Button(btn_frame, text="⏸️ 暫停", command=self.toggle_pause, width=12, height=2, bg="#FFD700", font=("Microsoft JhengHei", 10, "bold"), state="disabled")
        self.btn_pause.pack(side="left", padx=5)

        btn_start = tk.Button(btn_frame, text="🔥 啟動", command=self.start_bot, width=15, height=2, bg="#ffcccc", fg="red", font=("Microsoft JhengHei", 10, "bold"))
        btn_start.pack(side="left", padx=5)
        
        # 初始化 UI 狀態
        self.on_timer_toggle()
        self.on_date_toggle()
    
    def on_date_toggle(self):
        """控制日期輸入框的啟用/停用"""
        if self.var_enable_date.get():
            self.entry_date.config(state="normal", bg="white")
        else:
            self.entry_date.config(state="disabled", bg="#f0f0f0")

    def on_timer_toggle(self):
        if self.var_enable_timer.get(): self.entry_time.config(state="normal", bg="white")
        else: self.entry_time.config(state="disabled", bg="#f0f0f0")

    def on_mode_change(self, event):
        mode = self.combo_mode.get()
        if mode == "關鍵字優先": self.entry_area.config(state="normal", bg="white")
        else:
            self.entry_area.delete(0, tk.END)
            self.entry_area.config(state="disabled", bg="#f0f0f0")

    def toggle_pause(self):
        # 修正: 使用更安全的檔案操作，避免 Race Condition
        if os.path.exists(PAUSE_FILE):
            try: 
                os.remove(PAUSE_FILE)
            except OSError: pass # 檔案已不存在則忽略
            
            self.btn_pause.config(text="⏸️ 暫停", bg="#FFD700")
        else:
            try:
                with open(PAUSE_FILE, "w") as f: f.write("paused")
                self.btn_pause.config(text="▶️ 繼續", bg="#90EE90")
            except: pass

    def load_config_to_ui(self):
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: content = f.read()
            
            # 讀取平台設定
            platform_match = re.search(r'PLATFORM\s*=\s*["\'](.*?)["\']', content)
            if platform_match: self.combo_platform.set(platform_match.group(1))

            url_match = re.search(r'TIME_WATCH_URL\s*=\s*["\'](.*?)["\']', content)
            time_match = re.search(r'TARGET_TIME\s*=\s*["\'](.*?)["\']', content)
            timer_match = re.search(r'ENABLE_TIME_WATCHER\s*=\s*(True|False)', content)
            mode_match = re.search(r'AREA_AUTO_SELECT_MODE\s*=\s*["\'](.*?)["\']', content)
            area_match = re.search(r'WANTED_AREA_KEYWORD\s*=\s*["\'](.*?)["\']', content)
            exclude_match = re.search(r'EXCLUDE_AREA_KEYWORD\s*=\s*["\'](.*?)["\']', content)
            precode_match = re.search(r'PRE_ORDER_CODE\s*=\s*["\'](.*?)["\']', content)
            ticket_match = re.search(r'WANTED_TICKET_COUNT\s*=\s*["\'](.*?)["\']', content)
            date_match = re.search(r'WANTED_DATE_KEYWORD\s*=\s*["\'](.*?)["\']', content)

            if url_match: self.entry_url.insert(0, url_match.group(1))
            if time_match: self.entry_time.insert(0, time_match.group(1))
            if ticket_match: self.combo_ticket.set(ticket_match.group(1))
            
            if timer_match:
                val = timer_match.group(1) == 'True'
                self.var_enable_timer.set(val)
                self.on_timer_toggle()

            if date_match:
                val = date_match.group(1)
                if val:
                    self.var_enable_date.set(True)
                    self.entry_date.insert(0, val)
                else:
                    self.var_enable_date.set(False)
                self.on_date_toggle()

            if mode_match: 
                mode = mode_match.group(1)
                self.combo_mode.set(mode)
                if mode != "關鍵字優先": self.entry_area.config(state="disabled", bg="#f0f0f0")
            
            if area_match: self.entry_area.insert(0, area_match.group(1))
            if exclude_match: self.entry_exclude.insert(0, exclude_match.group(1))
            if precode_match: self.entry_precode.insert(0, precode_match.group(1))
            
        except: pass

    def save_config_from_ui(self):
        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("錯誤", f"找不到 {CONFIG_FILE}")
            return False
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: lines = f.readlines()
            new_lines = []
            
            date_val = self.entry_date.get().strip() if self.var_enable_date.get() else ""
            
            for line in lines:
                if line.strip().startswith("PLATFORM"): 
                    new_lines.append(f'PLATFORM = "{self.combo_platform.get()}"\n')
                elif line.strip().startswith("TIME_WATCH_URL"): 
                    new_lines.append(f'TIME_WATCH_URL = "{self.entry_url.get().strip()}"\n')
                elif line.strip().startswith("TARGET_TIME"): 
                    new_lines.append(f'TARGET_TIME = "{self.entry_time.get().strip()}"\n')
                elif line.strip().startswith("ENABLE_TIME_WATCHER"): 
                    new_lines.append(f'ENABLE_TIME_WATCHER = {self.var_enable_timer.get()}\n')
                elif line.strip().startswith("WANTED_DATE_KEYWORD"): 
                    new_lines.append(f'WANTED_DATE_KEYWORD = "{date_val}"\n')
                elif line.strip().startswith("AREA_AUTO_SELECT_MODE"): 
                    new_lines.append(f'AREA_AUTO_SELECT_MODE = "{self.combo_mode.get()}"\n')
                elif line.strip().startswith("WANTED_AREA_KEYWORD"): 
                    new_lines.append(f'WANTED_AREA_KEYWORD = "{self.entry_area.get().strip()}"\n')
                elif line.strip().startswith("EXCLUDE_AREA_KEYWORD"): 
                    new_lines.append(f'EXCLUDE_AREA_KEYWORD = "{self.entry_exclude.get().strip()}"\n')
                elif line.strip().startswith("PRE_ORDER_CODE"): 
                    new_lines.append(f'PRE_ORDER_CODE = "{self.entry_precode.get().strip()}"\n')
                elif line.strip().startswith("WANTED_TICKET_COUNT"): 
                    new_lines.append(f'WANTED_TICKET_COUNT = "{self.combo_ticket.get().strip()}"\n')
                else: new_lines.append(line)
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: f.writelines(new_lines)
            return True
        except Exception as e:
            messagebox.showerror("錯誤", str(e))
            return False

    def start_bot(self):
        if self.save_config_from_ui():
            if os.path.exists(PAUSE_FILE):
                try: os.remove(PAUSE_FILE)
                except: pass
                self.btn_pause.config(text="⏸️ 暫停", bg="#FFD700")

            try:
                cmd = []
                working_dir = os.getcwd()
                if getattr(sys, 'frozen', False):
                    # 【關鍵修復】尋找 TicketBot_Complete.exe
                    base_path = os.path.dirname(sys.executable)
                    main_exe_path = os.path.join(base_path, "TicketBot_Complete.exe")
                    
                    if not os.path.exists(main_exe_path):
                        # 備用方案 (保留相容舊版的名稱)
                        fallback_1 = os.path.join(base_path, "TicketBot.exe")
                        fallback_2 = os.path.join(base_path, "main.exe")
                        if os.path.exists(fallback_1): main_exe_path = fallback_1
                        elif os.path.exists(fallback_2): main_exe_path = fallback_2
                        else:
                            messagebox.showerror("啟動失敗", f"找不到主程式檔案！\n請確認 TicketBot_Complete.exe 是否與此啟動器放在同一個資料夾。")
                            return
                            
                    cmd = [main_exe_path]
                    working_dir = base_path
                else:
                    cmd = [sys.executable, "main.py"]

                if os.name == 'nt':
                    self.bot_process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=working_dir)
                else:
                    self.bot_process = subprocess.Popen(cmd, cwd=working_dir)
                
                self.btn_pause.config(state="normal")
                self.root.iconify()

            except Exception as e:
                messagebox.showerror("啟動失敗", str(e))

    def on_closing(self):
        if self.bot_process and self.bot_process.poll() is None: self.bot_process.kill()
        if os.name == 'nt': 
            # 【關鍵修復】確保關閉視窗時能砍掉正確的主程式
            os.system("taskkill /f /im TicketBot_Complete.exe >nul 2>&1")
            os.system("taskkill /f /im main.exe >nul 2>&1")
            os.system("taskkill /f /im TicketBot.exe >nul 2>&1")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TicketBotLauncher(root)
    root.mainloop()