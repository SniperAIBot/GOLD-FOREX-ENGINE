import time

from logger import logger

from config import (
    ENGINE_NAME,
    SCAN_INTERVAL,
    DATABASE_URL,
    BOT_TOKEN,
    PUBLIC_CHAT_ID,
    VIP_CHAT_ID,
    DATA_PROVIDER,
    EXECUTION_MODE,
    ENABLE_LIVE_TRADING,
    OANDA_ENV,
    OANDA_ACCOUNT_ID
)

from database import (
    initialize_database,
    save_signal
)

from scanner import scan_market
from monitor import monitor_signals
from performance import get_statistics
from execution import execute_signal

from telegram_bot import (
    send_public_signal,
    send_vip_signal
)


logger.info("========================================")
logger.info(f"🚀 STARTING {ENGINE_NAME}")
logger.info("========================================")

logger.info(f"📡 DATA_PROVIDER={DATA_PROVIDER}")
logger.info(f"🧪 EXECUTION_MODE={EXECUTION_MODE}")
logger.info(f"🧪 ENABLE_LIVE_TRADING={ENABLE_LIVE_TRADING}")
logger.info(f"🌍 OANDA_ENV={OANDA_ENV}")

if DATABASE_URL:
    logger.info("✅ DATABASE_URL DETECTED")
else:
    logger.error("❌ DATABASE_URL IS MISSING")

if BOT_TOKEN:
    logger.info("✅ BOT_TOKEN DETECTED")
else:
    logger.error("❌ BOT_TOKEN IS MISSING")

if PUBLIC_CHAT_ID:
    logger.info("✅ PUBLIC_CHAT_ID DETECTED")
else:
    logger.error("❌ PUBLIC_CHAT_ID IS MISSING")

if VIP_CHAT_ID:
    logger.info("✅ VIP_CHAT_ID DETECTED")
else:
    logger.error("❌ VIP_CHAT_ID IS MISSING")

if OANDA_ACCOUNT_ID:
    logger.info("✅ OANDA_ACCOUNT_ID DETECTED")
else:
    logger.warning("⚠️ OANDA_ACCOUNT_ID IS MISSING")


try:
    initialize_database()
except Exception as e:
    logger.error(f"❌ DATABASE INITIALIZATION FAILED: {e}")


def get_clean_win_rate():
    try:
        stats = get_statistics()

        if isinstance(stats, dict):
            return stats.get("win_rate", 0)

        return 0

    except Exception as e:
        logger.error(f"❌ FOREX WIN RATE LOAD ERROR: {e}")
        return 0


def process_signal(signal, clean_win_rate):
    try:
        symbol = signal.get("symbol", "UNKNOWN")
        direction = signal.get("direction", "UNKNOWN")

        logger.info(f"⚙️ PROCESSING FOREX SIGNAL: {symbol} {direction}")

        execution_result = execute_signal(signal)

        saved = save_signal(signal, execution_result)

        if saved:
            logger.info(f"✅ FOREX SIGNAL SAVED TO DATABASE: {symbol} {direction}")
        else:
            logger.error(f"❌ FOREX SIGNAL NOT SAVED TO DATABASE: {symbol} {direction}")

        logger.info("📤 SENDING PUBLIC SIGNAL")
        send_public_signal(signal)

        logger.info("📤 SENDING VIP SIGNAL")
        send_vip_signal(signal, clean_win_rate)

        logger.info(
            f"✅ FOREX SIGNAL PROCESSED: "
            f"{symbol} "
            f"{direction} "
            f"WIN_RATE={clean_win_rate}% "
            f"SMC_SCORE={signal.get('smc_score', 'N/A')} "
            f"SMC_GRADE={signal.get('smc_grade', 'N/A')}"
        )

    except Exception as e:
        logger.error(f"❌ FOREX SIGNAL PROCESS ERROR: {e}")


while True:
    try:
        logger.info("========================================")
        logger.info("🔍 FOREX SCANNING REAL MARKET DATA")
        logger.info("========================================")

        signals = scan_market()

        logger.info(f"📊 FOREX APP RECEIVED {len(signals)} SIGNALS")

        clean_win_rate = get_clean_win_rate()

        for signal in signals:
            process_signal(signal, clean_win_rate)
            time.sleep(1)

        try:
            monitor_signals()

        except Exception as monitor_error:
            logger.error(f"❌ FOREX MONITOR ERROR FROM APP: {monitor_error}")

        logger.info(f"⏳ FOREX SLEEPING {SCAN_INTERVAL} SECONDS")

        time.sleep(SCAN_INTERVAL)

    except Exception as main_error:
        logger.error(f"❌ FOREX MAIN LOOP ERROR: {main_error}")
        logger.info("⏳ FOREX RECOVERING IN 60 SECONDS")
        time.sleep(60)
