import numpy as np
from logger import logger
from indicators import ema, rsi, atr, prepare_dataframe
from smc import get_smc_score
from config import MIN_CONFIDENCE, DEFAULT_RR, STRATEGY_VERSION
from utils import round_symbol_price

def enrich_with_smc(signal, candles_5m, candles_15m, candles_1h, candles_4h=None):
    try:
        smc = get_smc_score(signal.get("symbol"), signal.get("direction"), candles_5m, candles_15m, candles_1h, candles_4h)
        signal.update(smc)
        base_confidence = int(signal.get("confidence", 0))
        smc_score = int(smc.get("smc_score", 0))
        if smc_score >= 80:
            signal["confidence"] = min(95, base_confidence + 4)
        elif smc_score >= 65:
            signal["confidence"] = min(95, base_confidence + 2)
        return signal
    except Exception as e:
        logger.error(f"❌ SMC ENRICH ERROR {signal.get('symbol')}: {e}")
        signal["smc_score"] = 0
        signal["smc_grade"] = "SMC ERROR"
        signal["smc_confirmed"] = False
        signal["smc_reasons"] = [str(e)]
        return signal

def analyze(symbol, candles_5m, candles_15m, candles_1h, symbol_profile=None, candles_4h=None):
    try:
        if symbol_profile is None:
            symbol_profile = {"weight": 1.0, "confidence_required": MIN_CONFIDENCE, "win_rate": 0, "trades": 0}
        ai_weight = float(symbol_profile.get("weight", 1.0))
        min_confidence = int(symbol_profile.get("confidence_required", MIN_CONFIDENCE))
        df5, df15, df1h = prepare_dataframe(candles_5m), prepare_dataframe(candles_15m), prepare_dataframe(candles_1h)
        if df5.empty or df15.empty or df1h.empty:
            return None
        for df in [df5, df15, df1h]:
            df["ema20"] = ema(df["close"], 20)
            df["ema50"] = ema(df["close"], 50)
        df5["rsi"] = rsi(df5["close"])
        df5["atr"] = atr(df5)
        df5["volume_ma"] = df5["volume"].rolling(20).mean()
        close = float(df5["close"].iloc[-1])
        current_rsi, previous_rsi = float(df5["rsi"].iloc[-1]), float(df5["rsi"].iloc[-2])
        current_atr = float(df5["atr"].iloc[-1])
        current_volume, average_volume = float(df5["volume"].iloc[-1]), float(df5["volume_ma"].iloc[-1])
        if np.isnan(current_atr) or np.isnan(current_rsi) or np.isnan(average_volume):
            logger.info(f"{symbol} REJECTED: INDICATOR NAN")
            return None
        atr_percent = (current_atr / close) * 100
        if atr_percent < 0.01:
            logger.info(f"{symbol} REJECTED: LOW ATR")
            return None
        volume_ratio = current_volume / average_volume if average_volume > 0 else 0
        if volume_ratio >= 1.30:
            volume_score = 12
        elif volume_ratio >= 1.00:
            volume_score = 6
        elif volume_ratio >= 0.70:
            volume_score = 0
        else:
            volume_score = -8
        bullish_1h, bearish_1h = df1h["ema20"].iloc[-1] > df1h["ema50"].iloc[-1], df1h["ema20"].iloc[-1] < df1h["ema50"].iloc[-1]
        bullish_15m, bearish_15m = df15["ema20"].iloc[-1] > df15["ema50"].iloc[-1], df15["ema20"].iloc[-1] < df15["ema50"].iloc[-1]
        bullish_5m, bearish_5m = df5["ema20"].iloc[-1] > df5["ema50"].iloc[-1], df5["ema20"].iloc[-1] < df5["ema50"].iloc[-1]
        ema_distance = abs(df5["ema20"].iloc[-1] - df5["ema50"].iloc[-1]) / close * 100
        if ema_distance < 0.005:
            logger.info(f"{symbol} REJECTED: WEAK TREND")
            return None
        ema_slope = abs(df5["ema20"].iloc[-1] - df5["ema20"].iloc[-5])
        if ema_slope < (close * 0.00002):
            logger.info(f"{symbol} REJECTED: WEAK MOMENTUM")
            return None
        current_body = abs(df5["close"].iloc[-1] - df5["open"].iloc[-1])
        candle_range = df5["high"].iloc[-1] - df5["low"].iloc[-1]
        if candle_range <= 0:
            return None
        if current_body < (candle_range * 0.20):
            logger.info(f"{symbol} REJECTED: WEAK CANDLE")
            return None
        if ai_weight >= 3:
            confidence_bonus = 8
        elif ai_weight >= 2:
            confidence_bonus = 5
        elif ai_weight >= 1:
            confidence_bonus = 0
        elif ai_weight >= 0.5:
            confidence_bonus = -8
        else:
            confidence_bonus = -14
        def build(direction):
            entry = close
            if direction == "BUY":
                stop_loss = entry - (current_atr * 1.4)
                take_profit = entry + (current_atr * 1.4 * DEFAULT_RR)
                rr = (take_profit - entry) / (entry - stop_loss)
            else:
                stop_loss = entry + (current_atr * 1.4)
                take_profit = entry - (current_atr * 1.4 * DEFAULT_RR)
                rr = (entry - take_profit) / (stop_loss - entry)
            confidence = min(95, int(56 + (ema_distance * 180) + (atr_percent * 10) + volume_score + confidence_bonus))
            if confidence < min_confidence:
                logger.info(f"{symbol} REJECTED: LOW CONFIDENCE {confidence} < {min_confidence}")
                return None
            signal = {
                "symbol": symbol, "direction": direction, "entry": round_symbol_price(symbol, entry),
                "take_profit": round_symbol_price(symbol, take_profit), "stop_loss": round_symbol_price(symbol, stop_loss),
                "rsi": round(current_rsi, 2), "atr": round(current_atr, 6), "rr": round(rr, 2),
                "confidence": confidence, "market_regime": "TRENDING", "strategy_version": STRATEGY_VERSION,
                "ai_weight": ai_weight, "ai_win_rate": symbol_profile.get("win_rate", 0),
                "ai_trades": symbol_profile.get("trades", 0)
            }
            return enrich_with_smc(signal, candles_5m, candles_15m, candles_1h, candles_4h)
        if bullish_1h and bullish_15m and bullish_5m and 50 < current_rsi < 75 and current_rsi >= previous_rsi:
            return build("BUY")
        if bearish_1h and bearish_15m and bearish_5m and 25 < current_rsi < 50 and current_rsi <= previous_rsi:
            return build("SELL")
        logger.info(f"{symbol} REJECTED: NO DIRECTION SETUP")
        return None
    except Exception as e:
        logger.error(f"❌ STRATEGY ERROR {symbol}: {e}")
        return None
