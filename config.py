# config.py (正式版 V17.0 - 支援 TicketPlus)

from selenium.webdriver.common.by import By
import os

# --- 平台選擇 ---
# "TIXCRAFT"   = 拓元售票
# "KKTIX"      = KKTIX
# "TICKETPLUS" = 遠大售票 (新功能)
PLATFORM = "TIXCRAFT"

# --- 共用搶票參數 (所有平台通用) ---
WANTED_TICKET_COUNT = "2"
WANTED_AREA_KEYWORD = "5880"
WANTED_DATE_KEYWORD = ""

# --- 時間與監控 (所有平台通用) ---
ENABLE_TIME_WATCHER = True
TARGET_TIME = "11:00:00"
TIME_WATCH_URL = "https://tixcraft.com/activity/game/26_itzy"

# --- 拓元 (Tixcraft) 專用設定 ---
TIXCRAFT_URL = "https://tixcraft.com/"
AREA_AUTO_SELECT_MODE = "關鍵字優先"
EXCLUDE_AREA_KEYWORD = "輪椅;身障;身心;障礙;Restricted View;燈柱遮蔽;視線不完整;身障票"
PRE_ORDER_CODE = ""

# --- 系統路徑設定 (通常不需修改) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTCHA_DATASET_DIR = os.path.join(BASE_DIR, "captchaAI", "dataset")
CAPTCHA_MODEL_DIR = os.path.join(BASE_DIR, "captchaAI", "model")
MODEL_FILENAME = "crnn_ctc_model.h5"
MODEL_PATH = os.path.join(CAPTCHA_MODEL_DIR, MODEL_FILENAME)

# --- 網頁元素選擇器 (僅供拓元舊模組參考) ---
class Selector:
    COOKIE_ACCEPT_BTN = (By.ID, "onetrust-accept-btn-handler")
    BUY_TICKET_BTN_SELECTOR = (By.CSS_SELECTOR, 'a[target="_new"]') 
    BUY_TICKET_BTN_TEXT = "立即購票"
    ORDER_BTN = (By.CSS_SELECTOR, 'button.btn.btn-primary.text-bold.m-0')
    TICKET_PRICE_SELECT = (By.ID, "TicketForm_ticketPrice_01")
    TICKET_AREA_A = (By.CLASS_NAME, "select_form_a") 
    TICKET_AREA_B = (By.CLASS_NAME, "select_form_b") 
    QUANTITY_DROPDOWN = (By.CSS_SELECTOR, '.mobile-select') 
    AGREEMENT_CHECKBOX = (By.CLASS_NAME, "form-check-input")
    CONFIRM_NEXT_BTN = (By.XPATH, '//*[@id="form-ticket-ticket"]/div[4]/button[2]')
    CAPTCHA_IMAGE = (By.ID, "TicketForm_verifyCode-image")
    CAPTCHA_INPUT = (By.ID, "TicketForm_verifyCode")
    CONFIRM_PURCHASE = (By.CSS_SELECTOR, 'button[type="submit"]')
    VERIFY_INPUT = (By.ID, "checkCode")
    VERIFY_BTN = (By.CLASS_NAME, "btn-primary")