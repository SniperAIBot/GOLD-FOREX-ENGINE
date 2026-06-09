import math
import random
import time

from logger import logger
from config import ENABLE_MT5, USE_SYNTHETIC_DATA

_MT5_AVAILABLE = False
_mt5 = None
MT5_TIMEFRAME_MAP = {}

if ENABLE_MT5:
    try:
        import MetaTrader5 as mt5
        _mt5 = mt5
        _MT5_AVAILABLE = True
    except Exception as e:
        logger.error(f"❌ MT5 PACKAGE NOT AVAILABLE: {e}")
        _MT5_AVAILABLE = False

def initialize_mt5():
    if not ENABLE_MT5:
        logger.info("🧪 MT5 DISABLED - USING PAPER/SYNTHETIC MODE")
        return False
    if not _MT5_AVAILABLE:
        logger.error("❌ MT5 ENABLED BUT PACKAGE IS NOT AVAILABLE")
        return False
    try:
        global MT5_TIMEFRAME_MAP
        MT5_TIMEFRAME_MAP = {
            "1m": _mt5.TIMEFRAME_M1,
            "5m": _mt5.TIMEFRAME_M5,
            "15m": _mt5.TIMEFRAME_M15,
            "1h": _mt5.TIMEFRAME_H1,
            "4h": _mt5.TIMEFRAME_H4,
        }
        if not _mt5.initialize():
            logger.error(f"❌ MT5 INITIALIZE FAILED: {_mt5.last_error()}")
            return False
        logger.info("✅ MT5 INITIALIZED")
        return True
    except Exception as e:
        logger.error(f"❌ MT5 INIT ERROR: {e}")
        return False

def shutdown_mt5():
    try:
        if _MT5_AVAILABLE:
            _mt5.shutdown()
    except Exception:
        pass

def _base_price(symbol):
    return {
        "XAUUSD": 2350.0, "XAGUSD": 30.0, "EURUSD": 1.0850, "GBPUSD": 1.2750,
        "USDJPY": 157.50, "USDCAD": 1.3700, "AUDUSD": 0.6650, "NZDUSD": 0.6150,
        "USDCHF": 0.9000, "USOIL": 78.0, "UKOIL": 82.0, "NAS100": 19000.0,
        "US30": 39000.0, "SPX500": 5300.0,
    }.get(symbol, 1.0)

def _volatility(symbol):
    if symbol == "XAUUSD":
        return 2.5
    if symbol == "XAGUSD":
        return 0.08
    if symbol in ["USOIL", "UKOIL"]:
        return 0.20
    if symbol == "NAS100":
        return 35.0
    if symbol == "US30":
        return 55.0
    if symbol == "SPX500":
        return 8.0
    if symbol.endswith("JPY"):
        return 0.035
    return 0.00035

def get_synthetic_klines(symbol, timeframe, limit=200):
    seed = abs(hash((symbol, timeframe, int(time.time() // 300)))) % 1_000_000
    rng = random.Random(seed)
    base = _base_price(symbol)
    vol = _volatility(symbol)
    candles = []
    price = base + math.sin(seed % 360) * vol * 8
    for i in range(limit):
        drift = math.sin((i + seed % 100) / 18) * vol * 0.25
        noise = rng.uniform(-vol, vol)
        open_price = price
        close = max(0.00001, open_price + drift + noise)
        high = max(open_price, close) + abs(rng.uniform(0, vol * 0.75))
        low = min(open_price, close) - abs(rng.uniform(0, vol * 0.75))
        volume = rng.uniform(100, 1000)
        candles.append({"open": float(open_price), "high": float(high), "low": float(low), "close": float(close), "volume": float(volume)})
        price = close
    return candles

def get_klines(symbol, timeframe, limit=200):
    if ENABLE_MT5 and _MT5_AVAILABLE:
        try:
            if not MT5_TIMEFRAME_MAP:
                initialize_mt5()
            tf = MT5_TIMEFRAME_MAP.get(timeframe)
            if tf is None:
                logger.error(f"❌ INVALID TIMEFRAME: {timeframe}")
                return None
            rates = _mt5.copy_rates_from_pos(symbol, tf, 0, limit)
            if rates is None or len(rates) == 0:
                logger.warning(f"⚠️ NO MT5 DATA: {symbol} {timeframe}")
                return None
            candles = []
            for row in rates:
                candles.append({"open": float(row["open"]), "high": float(row["high"]), "low": float(row["low"]), "close": float(row["close"]), "volume": float(row["tick_volume"])})
            logger.info(f"{symbol} {timeframe} MT5 DATA OK")
            return candles
        except Exception as e:
            logger.error(f"❌ MT5 KLINES ERROR {symbol} {timeframe}: {e}")

    if USE_SYNTHETIC_DATA:
        logger.info(f"{symbol} {timeframe} SYNTHETIC DATA OK")
        return get_synthetic_klines(symbol, timeframe, limit)

    logger.error(f"❌ NO DATA SOURCE AVAILABLE: {symbol} {timeframe}")
    return None
