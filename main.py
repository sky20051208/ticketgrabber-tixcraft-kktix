# main.py — 搶票輔助機器人入口
#
# 只負責一件事：依 config.PLATFORM 載入對應平台模組，呼叫它的 main()。
# 三個平台模組 (tixcraft / kktix.kkbot / ticketplus.ticketplusbot) 都各自
# 提供 async main()，所以這裡不再內含任何搶票邏輯。

import sys
import os

import nodriver as uc

# 路徑設定：支援 PyInstaller 打包後從 exe 旁邊讀取 config.py
if getattr(sys, "frozen", False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
if application_path not in sys.path:
    sys.path.append(application_path)

from config import PLATFORM


def load_platform_module(platform: str):
    """依平台名稱回傳對應模組（已 import）。找不到時丟 ImportError。"""
    if platform == "KKTIX":
        from kktix import kkbot
        return kkbot
    if platform == "TICKETPLUS":
        from ticketplus import ticketplusbot
        return ticketplusbot
    # 預設：拓元 (Tixcraft)
    import tixcraft
    return tixcraft


async def main():
    print(f"--- 搶票輔助機器人 (目前平台: {PLATFORM}) ---")

    try:
        module = load_platform_module(PLATFORM)
    except ImportError as e:
        print(f"❌ 找不到平台模組 ({PLATFORM}): {e}")
        input("按 Enter 鍵退出...")
        return

    await module.main()


if __name__ == "__main__":
    # Python 3.10+ 在 Windows 預設使用 ProactorEventLoop，支援 subprocess (nodriver 需要)
    uc.loop().run_until_complete(main())
