"""拓元 captcha OCR — 自訓 ONNX model 推論。

對外接口（沿用舊版，呼叫端 bot.py / bot2.py 不用改）：
  recognize_captcha(bytes) -> str         返回 4 字小寫英文（失敗回 ""）
  solve_captcha_nodriver(tab) -> str      瀏覽器模式：從 nodriver tab 抓圖辨識（async）
  get_captcha_base64_nodriver(tab) -> bytes | None

底層：onnxruntime + model/tixcraft_ocr.onnx（從 ticketbotWithApi 自訓而來）。
"""
import base64
import io
import os
from typing import Optional

import numpy as np
import onnxruntime as ort
from PIL import Image

from config import Selector

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "tixcraft_ocr.onnx")
_IMG_H, _IMG_W = 100, 120
_SEQ_LEN = 4
_BLANK_IDX = 26          # CTC blank class (在 26 個 a-z 之外)
_SESSION: Optional[ort.InferenceSession] = None


def _get_session() -> ort.InferenceSession:
    global _SESSION
    if _SESSION is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"找不到 ONNX model: {_MODEL_PATH}\n"
                f"請從 ticketbotWithApi/captchaAI/tixcraft_ocr.onnx 複製過來。"
            )
        _SESSION = ort.InferenceSession(_MODEL_PATH, providers=["CPUExecutionProvider"])
        print(f"[OK] 拓元 OCR 已載入 ({os.path.basename(_MODEL_PATH)})")
    return _SESSION


def _preprocess(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if img.size != (_IMG_W, _IMG_H):
        img = img.resize((_IMG_W, _IMG_H), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = (arr - 0.5) / 0.5
    return arr.transpose(2, 0, 1)[None]  # (1, 3, H, W)


def recognize_captcha(image_bytes: bytes) -> str:
    """辨識 captcha 圖 bytes，回 4 字小寫英文（失敗回 ""）。"""
    try:
        session = _get_session()
    except FileNotFoundError as e:
        print(f"[ERR] {e}")
        return ""
    try:
        x = _preprocess(image_bytes)
        logits, = session.run(["logits"], {"image": x})  # (1, T, 27)
        indices = logits[0].argmax(axis=-1)
        # CTC greedy decode：collapse 連續重複 + 移除 blank
        chars = []
        prev = -1
        for c in indices:
            c = int(c)
            if c != _BLANK_IDX and c != prev:
                chars.append(c)
            prev = c
        return "".join(chr(ord("a") + i) for i in chars[:_SEQ_LEN])
    except Exception as e:
        print(f"[ERR] OCR 推論失敗: {e}")
        return ""


# ---------- nodriver / 瀏覽器模式抓圖 (bot.py / bot2.py 用) ----------

async def get_captcha_base64_nodriver(tab) -> Optional[bytes]:
    """從 nodriver tab 把 captcha img 畫到 canvas、回 PNG bytes。"""
    captcha_id = Selector.CAPTCHA_IMAGE[1]
    js_script = f"""
    (async function() {{
        var img = document.getElementById('{captcha_id}');
        if (!img) return null;
        if (!img.complete || img.naturalWidth === 0) {{
            await new Promise(r => img.onload = r);
        }}
        var canvas = document.createElement('canvas');
        var context = canvas.getContext('2d');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        context.drawImage(img, 0, 0);
        var dataURL = canvas.toDataURL('image/png');
        return dataURL.split(',')[1];
    }})()
    """
    try:
        base64_str = await tab.evaluate(js_script, await_promise=True)
        if base64_str:
            return base64.b64decode(base64_str)
    except Exception:
        pass
    return None


async def solve_captcha_nodriver(tab) -> str:
    image_data = await get_captcha_base64_nodriver(tab)
    if not image_data:
        return ""
    captcha_text = recognize_captcha(image_data)
    return captcha_text.strip().replace(" ", "") if captcha_text else ""
