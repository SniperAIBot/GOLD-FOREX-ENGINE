import time

from logger import logger

from config import (
    ENGINE_NAME,
    SCAN_INTERVAL,
    DATABASE_URL,
    BOT_TOKEN,
    PUBLIC_CHAT_ID,
    VIP_CHAT_ID,
    ENABLE_LIVE_TRADING,
    ENABLE_MT5,
    USE_SYNTHETIC_DATA
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
    send_vip_signal,
    send_message
)

from mt5_connector import initialize_mt5


# =====================================================
# STARTUP LOGS
# =====================================================

logger.info("========================================")
logger.info(f"🚀 STARTING {ENGINE_NAME}")
logger.info("========================================")

logger.info(f"🧪 ENABLE_LIVE_TRADING={ENABLE_LIVE_TRADING}")
logger.info(f"🧪 ENABLE_MT5={ENABLE_MT5}")
logger.info(f"🧪 USE_SYNTHETIC_DATA={USE_SYNTHETIC_DATA}")

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


# =====================================================
# INITIALIZATION
# =====================================================

try:
    initialize_database()
except Exception as e:
    logger.error(f"❌ DATABASE INITIALIZATION FAILED: {e}")


try:
    initialize_mt5()
except Exception as e:
    logger.error(f"❌ MT5 INITIALIZATION FAILED: {e}")


# =====================================================
# OPTIONAL TELEGRAM STARTUP TEST
# =====================================================

try:
    logger.info("🚀 TESTING TELEGRAM PUBLIC + VIP")

    send_message(
        PUBLIC_CHAT_ID,
        "✅ SNIPER FOREX ENGINE ONLINE - PUBLIC CHANNEL"
    )

    send_message(
        VIP_CHAT_ID,
        "✅ SNIPER FOREX ENGINE ONLINE - VIP CHANNEL"
    )

except Exception as e:
    logger.error(f"❌ TELEGRAM STARTUP TEST FAILED: {e}")


# =====================================================
# HELPERS
# =====================================================

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

        logger.info(
            f"⚙️ PROCESSING FOREX SIGNAL: {symbol} {direction}"
        )

        execution_result = execute_signal(signal)

        saved = save_signal(
            signal,
            execution_result
        )

        if saved:
            logger.info(
                f"✅ FOREX SIGNAL SAVED TO DATABASE: {symbol} {direction}"
            )
        else:
            logger.error(
                f"❌ FOREX SIGNAL NOT SAVED TO DATABASE: {symbol} {direction}"
            )

        logger.info("📤 SENDING PUBLIC SIGNAL")
        send_public_signal(signal)

        logger.info("📤 SENDING VIP SIGNAL")
        send_vip_signal(
            signal,
            clean_win_rate
        )

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


# =====================================================
# MAIN LOOP
# =====================================================

while True:
    try:
        logger.info("========================================")
        logger.info("🔍 FOREX SCANNING MARKET")
        logger.info("========================================")

        signals = scan_market()

        logger.info(
            f"📊 FOREX APP RECEIVED {len(signals)} SIGNALS"
        )

        clean_win_rate = get_clean_win_rate()

        for signal in signals:
            process_signal(
                signal,
                clean_win_rate
            )

            time.sleep(1)

        try:
            monitor_signals()

        except Exception as monitor_error:
            logger.error(
                f"❌ FOREX MONITOR ERROR FROM APP: {monitor_error}"
            )

        logger.info(
            f"⏳ FOREX SLEEPING {SCAN_INTERVAL} SECONDS"
        )

        time.sleep(SCAN_INTERVAL)

    except Exception as main_error:
        logger.error(
            f"❌ FOREX MAIN LOOP ERROR: {main_error}"
        )

        logger.info(
            "⏳ FOREX RECOVERING IN 60 SECONDS"
        )

        time.sleep(60)
