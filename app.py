import time
from logger import logger
from config import ENGINE_NAME, SCAN_INTERVAL
from database import initialize_database, save_signal
from scanner import scan_market
from monitor import monitor_signals
from performance import get_statistics
from execution import execute_signal
from telegram_bot import send_public_signal, send_vip_signal
from mt5_connector import initialize_mt5

logger.info(f"🚀 STARTING {ENGINE_NAME}")
initialize_database()
initialize_mt5()

def get_clean_win_rate():
    try:
        stats = get_statistics()
        if isinstance(stats, dict):
            return stats.get("win_rate", 0)
        return 0
    except Exception as e:
        logger.error(f"❌ FOREX WIN RATE LOAD ERROR: {e}")
        return 0

while True:
    try:
        logger.info("🔍 FOREX SCANNING MARKET")
        signals = scan_market()
        logger.info(f"📊 FOREX APP RECEIVED {len(signals)} SIGNALS")
        clean_win_rate = get_clean_win_rate()
        for signal in signals:
            try:
                execution_result = execute_signal(signal)
                save_signal(signal, execution_result)
                send_public_signal(signal)
                send_vip_signal(signal, clean_win_rate)
                logger.info(f"✅ FOREX SIGNAL PROCESSED: {signal['symbol']} {signal['direction']} WIN_RATE={clean_win_rate}%")
                time.sleep(1)
            except Exception as signal_error:
                logger.error(f"❌ FOREX SIGNAL PROCESS ERROR: {signal_error}")
        monitor_signals()
        logger.info(f"⏳ FOREX SLEEPING {SCAN_INTERVAL} SECONDS")
        time.sleep(SCAN_INTERVAL)
    except Exception as main_error:
        logger.error(f"❌ FOREX MAIN LOOP ERROR: {main_error}")
        time.sleep(60)
