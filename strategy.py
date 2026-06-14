import numpy as np

from logger import logger
from indicators import ema, rsi, atr, prepare_dataframe
from smc import get_smc_score
from config import MIN_CONFIDENCE, DEFAULT_RR, STRATEGY_VERSION
from utils import round_symbol_price


MIN_ACCEPTED_SMC_SCORE = 50
BLOCKED_SMC_GRADES = ["C SMC", "NO SMC CONFIRMATION"]


def enrich_with_smc(signal, candles_5m, candles_15m, candles_1h, candles_4h=None):
    try:
        smc = get_smc_score(
            signal.get("symbol"),
            signal.get("direction"),
            candles_5m,
            candles_15m,
            candles_1h,
            candles_4h,
        )

        signal.update(smc)

        base_confidence = int(signal.get("confidence", 0))
        smc_score = int(smc.get("smc_score", 0))

        if smc_score >= 80:
            signal["confidence"] = min(95, base_confidence + 8)
        elif smc_score >= 65:
            signal["confidence"] = min(95, base_confidence + 5)
        elif smc_score >= 50:
            signal["confidence"] = min(95, base_confidence + 3)

        return signal

    except Exception as e:
        logger.error(f"SMC ENRICH ERROR {signal.get('symbol')}: {e}")
        signal["smc_score"] = 0
        signal["smc_grade"] = "SMC ERROR"
        signal["smc_confirmed"] = False
        signal["smc_reasons"] = [str(e)]
        return signal


def market_bias(df1h, df15, df5):
    bullish_votes = 0
    bearish_votes = 0

    if df1h["ema20"].iloc[-1] > df1h["ema50"].iloc[-1]:
        bullish_votes += 2
    else:
        bearish_votes += 2

    if df15["ema20"].iloc[-1] > df15["ema50"].iloc[-1]:
        bullish_votes += 1
    else:
        bearish_votes += 1

    if df5["ema20"].iloc[-1] > df5["ema50"].iloc[-1]:
        bullish_votes += 1
    else:
        bearish_votes += 1

    if bullish_votes >= 3:
        return "BUY"

    if bearish_votes >= 3:
        return "SELL"

    return None


def analyze(symbol, candles_5m, candles_15m, candles_1h, symbol_profile=None, candles_4h=None):
    try:
        if symbol_profile is None:
            symbol_profile = {
                "weight": 1.0,
                "confidence_required": MIN_CONFIDENCE,
                "win_rate": 0,
                "trades": 0,
            }

        ai_weight = float(symbol_profile.get("weight", 1.0))
        min_confidence = int(symbol_profile.get("confidence_required", MIN_CONFIDENCE))

        df5 = prepare_dataframe(candles_5m)
        df15 = prepare_dataframe(candles_15m)
        df1h = prepare_dataframe(candles_1h)

        if df5.empty or df15.empty or df1h.empty:
            return None

        for df in [df5, df15, df1h]:
            df["ema20"] = ema(df["close"], 20)
            df["ema50"] = ema(df["close"], 50)

        df5["rsi"] = rsi(df5["close"])
        df5["atr"] = atr(df5)
        df5["volume_ma"] = df5["volume"].rolling(20).mean()

        close = float(df5["close"].iloc[-1])
        current_rsi = float(df5["rsi"].iloc[-1])
        previous_rsi = float(df5["rsi"].iloc[-2])
        current_atr = float(df5["atr"].iloc[-1])
        current_volume = float(df5["volume"].iloc[-1])
        average_volume = float(df5["volume_ma"].iloc[-1])

        if np.isnan(current_atr) or np.isnan(current_rsi) or np.isnan(average_volume):
            logger.info(f"{symbol} REJECTED: INDICATOR NAN")
            return None

        atr_percent = (current_atr / close) * 100

        if atr_percent < 0.004:
            logger.info(f"{symbol} REJECTED: LOW ATR")
            return None

        direction = market_bias(df1h, df15, df5)

        if direction is None:
            logger.info(f"{symbol} REJECTED: NO MARKET BIAS")
            return None

        volume_ratio = current_volume / average_volume if average_volume > 0 else 1

        if volume_ratio >= 1.30:
            volume_score = 10
        elif volume_ratio >= 1.00:
            volume_score = 5
        elif volume_ratio >= 0.55:
            volume_score = 0
        else:
            volume_score = -5

        ema_distance = abs(df5["ema20"].iloc[-1] - df5["ema50"].iloc[-1]) / close * 100

        if ema_distance < 0.0015:
            logger.info(f"{symbol} REJECTED: WEAK TREND")
            return None

        ema_slope = abs(df5["ema20"].iloc[-1] - df5["ema20"].iloc[-5])

        if ema_slope < (close * 0.000006):
            logger.info(f"{symbol} REJECTED: WEAK MOMENTUM")
            return None

        current_body = abs(df5["close"].iloc[-1] - df5["open"].iloc[-1])
        candle_range = df5["high"].iloc[-1] - df5["low"].iloc[-1]

        if candle_range <= 0:
            return None

        if current_body < (candle_range * 0.08):
            logger.info(f"{symbol} REJECTED: WEAK CANDLE")
            return None

        if direction == "BUY":
            if not (35 < current_rsi < 82):
                logger.info(f"{symbol} REJECTED: RSI BUY FILTER")
                return None

            if current_rsi < previous_rsi - 6:
                logger.info(f"{symbol} REJECTED: RSI BUY MOMENTUM")
                return None

        if direction == "SELL":
            if not (18 < current_rsi < 65):
                logger.info(f"{symbol} REJECTED: RSI SELL FILTER")
                return None

            if current_rsi > previous_rsi + 6:
                logger.info(f"{symbol} REJECTED: RSI SELL MOMENTUM")
                return None

        if ai_weight >= 3:
            confidence_bonus = 8
        elif ai_weight >= 2:
            confidence_bonus = 5
        elif ai_weight >= 1:
            confidence_bonus = 0
        elif ai_weight >= 0.5:
            confidence_bonus = -4
        else:
            confidence_bonus = -8

        entry = close

        if direction == "BUY":
            stop_loss = entry - (current_atr * 1.35)
            take_profit = entry + (current_atr * 1.35 * DEFAULT_RR)
            rr = (take_profit - entry) / (entry - stop_loss)
        else:
            stop_loss = entry + (current_atr * 1.35)
            take_profit = entry - (current_atr * 1.35 * DEFAULT_RR)
            rr = (entry - take_profit) / (stop_loss - entry)

        confidence = min(
            95,
            int(
                55
                + (ema_distance * 240)
                + (atr_percent * 12)
                + volume_score
                + confidence_bonus
            ),
        )

        signal = {
            "symbol": symbol,
            "direction": direction,
            "entry": round_symbol_price(symbol, entry),
            "take_profit": round_symbol_price(symbol, take_profit),
            "stop_loss": round_symbol_price(symbol, stop_loss),
            "rsi": round(current_rsi, 2),
            "atr": round(current_atr, 6),
            "rr": round(rr, 2),
            "confidence": confidence,
            "market_regime": "TRENDING",
            "strategy_version": STRATEGY_VERSION,
            "ai_weight": ai_weight,
            "ai_win_rate": symbol_profile.get("win_rate", 0),
            "ai_trades": symbol_profile.get("trades", 0),
        }

        signal = enrich_with_smc(signal, candles_5m, candles_15m, candles_1h, candles_4h)

        smc_score = int(signal.get("smc_score", 0))
        smc_grade = signal.get("smc_grade", "")

        if smc_score < MIN_ACCEPTED_SMC_SCORE:
            logger.info(f"{symbol} REJECTED: LOW SMC SCORE {smc_score}")
            return None

        if smc_grade in BLOCKED_SMC_GRADES:
            logger.info(f"{symbol} REJECTED: BAD SMC GRADE {smc_grade}")
            return None

        adjusted_min_confidence = min_confidence

        if smc_score >= 65:
            adjusted_min_confidence -= 4

        if ai_weight <= 0.5:
            adjusted_min_confidence += 3

        if signal["confidence"] < adjusted_min_confidence:
            logger.info(
                f"{symbol} REJECTED: LOW CONFIDENCE {signal['confidence']} < {adjusted_min_confidence}"
            )
            return None

        return signal

    except Exception as e:
        logger.error(f"STRATEGY ERROR {symbol}: {e}")
        return None