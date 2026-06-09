import os

ENGINE_NAME = "SNIPER FOREX ENGINE V1.0"
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))

DATABASE_URL = os.getenv("DATABASE_URL")

BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_CHAT_ID = os.getenv("PUBLIC_CHAT_ID")
VIP_CHAT_ID = os.getenv("VIP_CHAT_ID")
VIP_LINK = os.getenv("VIP_LINK", "")

ENABLE_LIVE_TRADING = os.getenv("ENABLE_LIVE_TRADING", "false").lower() == "true"
ENABLE_MT5 = os.getenv("ENABLE_MT5", "false").lower() == "true"

PAPER_RISK_AMOUNT = float(os.getenv("PAPER_RISK_AMOUNT", "10"))
DEFAULT_RR = float(os.getenv("DEFAULT_RR", "2.0"))

SYMBOLS = [
    "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF",
    "XAGUSD", "USOIL", "UKOIL", "NAS100", "US30", "SPX500",
]

MIN_CONFIDENCE = int(os.getenv("MIN_CONFIDENCE", "72"))
COOLDOWN_MINUTES = int(os.getenv("COOLDOWN_MINUTES", "90"))
LOSS_STREAK_LIMIT = int(os.getenv("LOSS_STREAK_LIMIT", "5"))
PAUSE_AFTER_LOSS_STREAK_SECONDS = int(os.getenv("PAUSE_AFTER_LOSS_STREAK_SECONDS", str(6 * 60 * 60)))
STRATEGY_VERSION = "v1_forex_gold_smc_ai_paper"

# Railway-safe fallback. Real MT5 needs Windows/VPS.
USE_SYNTHETIC_DATA = os.getenv("USE_SYNTHETIC_DATA", "true").lower() == "true"
