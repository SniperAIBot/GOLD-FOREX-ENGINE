from oandapyV20.endpoints.instruments import InstrumentsCandles

from logger import logger
from oanda_client import get_oanda_api
from config import DATA_PROVIDER


OANDA_SYMBOL_MAP = {
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "USDJPY": "USD_JPY",
    "USDCAD": "USD_CAD",
    "AUDUSD": "AUD_USD",
    "NZDUSD": "NZD_USD",
    "USDCHF": "USD_CHF",

    "XAUUSD": "XAU_USD",
    "XAGUSD": "XAG_USD",

    "USOIL": "WTICO_USD",
    "UKOIL": "BCO_USD",

    "NAS100": "NAS100_USD",
    "US30": "US30_USD",
    "SPX500": "SPX500_USD",
}


OANDA_TIMEFRAME_MAP = {
    "1m": "M1",
    "5m": "M5",
    "15m": "M15",
    "1h": "H1",
    "4h": "H4",
}


def get_oanda_symbol(symbol):
    return OANDA_SYMBOL_MAP.get(symbol, symbol)


def get_oanda_granularity(timeframe):
    return OANDA_TIMEFRAME_MAP.get(timeframe)


def get_klines(symbol, timeframe, limit=200):
    if DATA_PROVIDER != "oanda":
        logger.error(f"❌ UNSUPPORTED DATA_PROVIDER: {DATA_PROVIDER}")
        return None

    api = get_oanda_api()

    if api is None:
        return None

    instrument = get_oanda_symbol(symbol)
    granularity = get_oanda_granularity(timeframe)

    if granularity is None:
        logger.error(f"❌ INVALID TIMEFRAME FOR OANDA: {timeframe}")
        return None

    params = {
        "count": int(limit),
        "granularity": granularity,
        "price": "M"
    }

    try:
        request = InstrumentsCandles(
            instrument=instrument,
            params=params
        )

        response = api.request(request)

        candles = []

        for candle in response.get("candles", []):
            if not candle.get("complete", False):
                continue

            mid = candle.get("mid", {})

            candles.append({
                "open": float(mid["o"]),
                "high": float(mid["h"]),
                "low": float(mid["l"]),
                "close": float(mid["c"]),
                "volume": float(candle.get("volume", 0))
            })

        if not candles:
            logger.warning(f"⚠️ OANDA NO CANDLES: {symbol} {timeframe}")
            return None

        logger.info(f"✅ OANDA DATA OK: {symbol} {timeframe} {len(candles)} candles")
        return candles

    except Exception as e:
        logger.error(f"❌ OANDA DATA ERROR {symbol} {timeframe}: {e}")
        return None
