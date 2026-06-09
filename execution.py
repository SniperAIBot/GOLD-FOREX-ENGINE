from logger import logger
from config import ENABLE_LIVE_TRADING, PAPER_RISK_AMOUNT

def execute_signal(signal):
    symbol = signal.get("symbol")
    direction = signal.get("direction")
    if not symbol or not direction:
        logger.error("❌ INVALID FOREX SIGNAL FOR EXECUTION")
        return None
    if not ENABLE_LIVE_TRADING:
        logger.warning(f"🧪 FOREX PAPER MODE - NO LIVE ORDER: {symbol} {direction}")
        return {"paper": True, "symbol": symbol, "side": direction, "quantity": PAPER_RISK_AMOUNT, "leverage": None}
    logger.error("❌ LIVE FOREX EXECUTION IS NOT ENABLED IN V1.0")
    return None

def close_position(symbol, quantity=None):
    logger.warning(f"🧪 FOREX PAPER CLOSE: {symbol}")
    return {"paper": True, "symbol": symbol, "side": "CLOSE", "quantity": quantity or 0, "leverage": None}
