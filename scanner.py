import time

from logger import logger
from config import (
    SYMBOLS,
    COOLDOWN_MINUTES,
    LOSS_STREAK_LIMIT,
    PAUSE_AFTER_LOSS_STREAK_SECONDS
)

from market_data import get_klines
from strategy import analyze
from database import get_symbol_profile, get_recent_closed_results


LAST_SIGNAL_TIME = {}
PAUSED_UNTIL = 0


def should_pause_trading():
    global PAUSED_UNTIL

    now = time.time()

    if now < PAUSED_UNTIL:
        remaining_minutes = int((PAUSED_UNTIL - now) / 60)
        logger.warning(
            f"🛑 FOREX TRADING PAUSED AFTER LOSS STREAK. REMAINING={remaining_minutes} MIN"
        )
        return True

    recent = get_recent_closed_results(limit=LOSS_STREAK_LIMIT)

    if len(recent) < LOSS_STREAK_LIMIT:
        return False

    losses = [row for row in recent if row.get("result") == "LOSS"]

    if len(losses) == LOSS_STREAK_LIMIT:
        PAUSED_UNTIL = now + PAUSE_AFTER_LOSS_STREAK_SECONDS
        logger.error(
            f"🛑 FOREX LOSS STREAK DETECTED: {LOSS_STREAK_LIMIT} LOSSES. PAUSING."
        )
        return True

    return False


def in_cooldown(symbol):
    if symbol not in LAST_SIGNAL_TIME:
        return False

    elapsed = time.time() - LAST_SIGNAL_TIME[symbol]
    return elapsed < (COOLDOWN_MINUTES * 60)


def correlation_filter(signals, new_signal):
    if not signals:
        return True

    same_direction = sum(
        1 for signal in signals
        if signal["direction"] == new_signal["direction"]
    )

    if same_direction >= 3:
        logger.info("⚠️ FOREX CORRELATION BLOCKED")
        return False

    return True


def scan_market():
    signals = []

    if should_pause_trading():
        return signals

    logger.info(f"🔍 SCANNING FOREX/MARKETS SYMBOLS: {SYMBOLS}")

    for symbol in SYMBOLS:
        try:
            if in_cooldown(symbol):
                logger.info(f"⏳ FOREX COOLDOWN: {symbol}")
                continue

            profile = get_symbol_profile(symbol, days=7)

            logger.info(
                f"🧠 FOREX AI PROFILE {symbol}: "
                f"WR={profile['win_rate']}% "
                f"TRADES={profile['trades']} "
                f"WEIGHT={profile['weight']} "
                f"MIN_CONF={profile['confidence_required']}"
            )

            candles_5m = get_klines(symbol, "5m", 200)
            candles_15m = get_klines(symbol, "15m", 200)
            candles_1h = get_klines(symbol, "1h", 200)
            candles_4h = get_klines(symbol, "4h", 200)

            if candles_5m is None or candles_15m is None or candles_1h is None:
                logger.warning(f"⚠️ FOREX NO REAL DATA: {symbol}")
                continue

            logger.info(f"📈 FOREX ANALYZING {symbol}")

            signal = analyze(
                symbol,
                candles_5m,
                candles_15m,
                candles_1h,
                profile,
                candles_4h
            )

            if signal is None:
                logger.info(f"❌ FOREX NO SETUP: {symbol}")
                continue

            if not correlation_filter(signals, signal):
                continue

            LAST_SIGNAL_TIME[symbol] = time.time()
            signals.append(signal)

            logger.info(
                f"🔥 FOREX SIGNAL FOUND {symbol} "
                f"{signal['direction']} "
                f"CONF={signal['confidence']} "
                f"AI_WEIGHT={signal.get('ai_weight')} "
                f"SMC_SCORE={signal.get('smc_score', 'N/A')} "
                f"SMC_GRADE={signal.get('smc_grade', 'N/A')} "
                f"SMC_CONFIRMED={signal.get('smc_confirmed', 'N/A')}"
            )

        except Exception as e:
            logger.error(f"❌ FOREX SCAN ERROR {symbol}: {e}")

    logger.info(f"📊 FOREX FOUND {len(signals)} SIGNALS")
    return signals
