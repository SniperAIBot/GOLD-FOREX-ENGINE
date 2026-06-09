from mt5_connector import get_klines
from database import get_open_signals, close_signal
from execution import close_position
from logger import logger

def monitor_signals():
    try:
        signals = get_open_signals()
        if not signals:
            logger.info("📭 FOREX NO OPEN SIGNALS")
            return
        logger.info(f"👀 FOREX MONITORING {len(signals)} SIGNALS")
        for signal in signals:
            try:
                candles = get_klines(signal["symbol"], "5m", 2)
                if not candles:
                    continue
                last_candle = candles[-1]
                high, low = float(last_candle["high"]), float(last_candle["low"])
                symbol, direction = signal["symbol"], signal["direction"]
                tp, sl = float(signal["take_profit"]), float(signal["stop_loss"])
                quantity = signal.get("executed_quantity")
                if direction == "BUY":
                    if high >= tp:
                        close_position(symbol, quantity)
                        close_signal(signal["id"], "WIN")
                        logger.info(f"🏆 FOREX TP HIT: {symbol}")
                    elif low <= sl:
                        close_position(symbol, quantity)
                        close_signal(signal["id"], "LOSS")
                        logger.info(f"💀 FOREX SL HIT: {symbol}")
                elif direction == "SELL":
                    if low <= tp:
                        close_position(symbol, quantity)
                        close_signal(signal["id"], "WIN")
                        logger.info(f"🏆 FOREX SELL TP HIT: {symbol}")
                    elif high >= sl:
                        close_position(symbol, quantity)
                        close_signal(signal["id"], "LOSS")
                        logger.info(f"💀 FOREX SELL SL HIT: {symbol}")
            except Exception as e:
                logger.error(f"❌ FOREX MONITOR SIGNAL ERROR: {e}")
    except Exception as e:
        logger.error(f"❌ FOREX MONITOR ERROR: {e}")
