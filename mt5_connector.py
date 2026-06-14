import MetaTrader5 as mt5
from logger import logger


MT5_TIMEFRAME_MAP = {
    "1m": mt5.TIMEFRAME_M1,
    "5m": mt5.TIMEFRAME_M5,
    "15m": mt5.TIMEFRAME_M15,
    "1h": mt5.TIMEFRAME_H1,
    "4h": mt5.TIMEFRAME_H4,
}


def initialize_mt5():
    try:
        if mt5.initialize():
            logger.info("✅ MT5 INITIALIZED")
            return True

        logger.error(f"❌ MT5 INITIALIZE FAILED: {mt5.last_error()}")
        return False

    except Exception as e:
        logger.error(f"❌ MT5 INIT ERROR: {e}")
        return False


def shutdown_mt5():
    try:
        mt5.shutdown()
    except Exception:
        pass


def ensure_symbol(symbol):
    try:
        info = mt5.symbol_info(symbol)

        if info is None:
            logger.error(f"❌ MT5 SYMBOL NOT FOUND: {symbol}")
            return False

        if not info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.error(f"❌ MT5 SYMBOL SELECT FAILED: {symbol}")
                return False

        return True

    except Exception as e:
        logger.error(f"❌ MT5 SYMBOL ERROR {symbol}: {e}")
        return False


def get_klines(symbol, timeframe, limit=200):
    try:
        if not mt5.initialize():
            logger.error(f"❌ MT5 NOT INITIALIZED: {mt5.last_error()}")
            return None

        if timeframe not in MT5_TIMEFRAME_MAP:
            logger.error(f"❌ INVALID TIMEFRAME: {timeframe}")
            return None

        if not ensure_symbol(symbol):
            return None

        rates = mt5.copy_rates_from_pos(
            symbol,
            MT5_TIMEFRAME_MAP[timeframe],
            0,
            limit
        )

        if rates is None or len(rates) == 0:
            logger.warning(f"⚠️ NO MT5 DATA: {symbol} {timeframe}")
            return None

        candles = []

        for row in rates:
            candles.append({
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["tick_volume"]),
            })

        logger.info(f"✅ {symbol} {timeframe} MT5 DATA OK")
        return candles

    except Exception as e:
        logger.error(f"❌ MT5 KLINES ERROR {symbol} {timeframe}: {e}")
        return None