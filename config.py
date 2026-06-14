import os

ENGINE_NAME = "SNIPER FOREX ENGINE V2.0 MT5 ONLY"
STRATEGY_VERSION = "v2_0_mt5_fpmarkets_real_data_paper"

SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))

DATA_PROVIDER = "mt5"
ENABLE_MT5 = True
USE_SYNTHETIC_DATA = False

DATABASE_URL = os.getenv("DATABASE_URL")

BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_CHAT_ID = os.getenv("PUBLIC_CHAT_ID")
VIP_CHAT_ID = os.getenv("VIP_CHAT_ID")
VIP_LINK = os.getenv("VIP_LINK", "")

EXECUTION_MODE = os.getenv("EXECUTION_MODE", "paper").lower()
ENABLE_LIVE_TRADING = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"

PAPER_RISK_AMOUNT = float(os.getenv("PAPER_RISK_AMOUNT", "10"))
LIVE_RISK_AMOUNT = float(os.getenv("LIVE_RISK_AMOUNT", "10"))

DEFAULT_RR = float(os.getenv("DEFAULT_RR", "2.0"))

MIN_CONFIDENCE = int(os.getenv("MIN_CONFIDENCE", "72"))
COOLDOWN_MINUTES = int(os.getenv("COOLDOWN_MINUTES", "90"))
LOSS_STREAK_LIMIT = int(os.getenv("LOSS_STREAK_LIMIT", "5"))
PAUSE_AFTER_LOSS_STREAK_SECONDS = int(os.getenv("PAUSE_AFTER_LOSS_STREAK_SECONDS", str(6 * 60 * 60)))

SYMBOLS = [
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCAD",
    "AUDUSD",
    "NZDUSD",
    "USDCHF",
]