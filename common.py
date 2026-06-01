# common.py — 各平台共用的工具函式
#
# 把原本散落在 bot.py / kktix / ticketplus 各自重複定義的
# check_pause、PAUSE_FILE、瀏覽器啟動、alert 攔截器集中於此，
# 避免一份邏輯維護三次。

import asyncio
import os
import random
from datetime import datetime

import nodriver as uc

# 暫停旗標檔：GUI 端建立 / 移除這個檔來控制機器人暫停與繼續
PAUSE_FILE = "pause.lock"


async def check_pause(tag: str = ""):
    """偵測 pause.lock，存在時阻塞直到檔案被移除。

    tag 用來在多平台共用時標示是哪個模組（例如 "拓元"、"KKTIX"）。
    """
    if not os.path.exists(PAUSE_FILE):
        return
    prefix = f"[{tag}] " if tag else ""
    print(f"\n⏸️ {prefix}程式已暫停...", end="\r")
    while os.path.exists(PAUSE_FILE):
        await asyncio.sleep(0.5)
    print(f"\n▶️ {prefix}程式繼續執行！        ")


async def random_sleep(min_s: float = 0.2, max_s: float = 0.5):
    """隨機等待，模擬人類操作節奏。"""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def launch_browser(extra_args=None, user_data_dir: str = None):
    """以共用參數啟動 nodriver 瀏覽器。

    extra_args:     額外的 Chromium 啟動參數（list）。
    user_data_dir:  指定使用者資料夾（拓元模式用來保留登入狀態）。
    """
    args = ["--start-maximized", "--disable-notifications"]
    if extra_args:
        args.extend(extra_args)

    kwargs = {"headless": False, "browser_args": args}
    if user_data_dir:
        kwargs["user_data_dir"] = os.path.abspath(user_data_dir)

    return await uc.start(**kwargs)


async def attach_alert_handler(tab, label: str = ""):
    """為指定分頁掛上 CDP 監聽器，自動關閉 JavaScript 系統彈窗 (alert/confirm)。

    切換到新分頁後務必重新呼叫，否則遇到彈窗會卡住整個流程。
    回傳 handler 本身，方便呼叫端需要時移除。
    """
    async def _handler(event: uc.cdp.page.JavascriptDialogOpening):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = f"[{label}] " if label else ""
        print(f"⚡ {prefix}[{ts}] Alert 秒殺: {event.message}")
        try:
            await tab.send(uc.cdp.page.handle_java_script_dialog(accept=True))
        except Exception:
            pass

    try:
        await tab.send(uc.cdp.page.enable())
        tab.add_handler(uc.cdp.page.JavascriptDialogOpening, _handler)
    except Exception as e:
        print(f"⚠️ attach_alert_handler 失敗: {e}")

    try:
        await tab.send(uc.cdp.network.enable())
    except Exception:
        pass

    return _handler
