import MetaTrader5 as mt5

from logger import logger
from config import ENABLE_LIVE_TRADING, EXECUTION_MODE, PAPER_RISK_AMOUNT, LIVE_RISK_AMOUNT


def calculate_lot_size(signal):
    try:
        return float(LIVE_RISK_AMOUNT)
    except Exception:
        return 0.01


def execute_signal(signal):
    symbol = signal.get("symbol")
    direction = signal.get("direction")

    if not symbol or not direction:
        logger.error("❌ INVALID SIGNAL FOR EXECUTION")
        return None

    if not ENABLE_LIVE_TRADING or EXECUTION_MODE == "paper":
        logger.warning(f"🧪 MT5 PAPER MODE - NO LIVE ORDER: {symbol} {direction}")
        return {
            "paper": True,
            "symbol": symbol,
            "side": direction,
            "quantity": PAPER_RISK_AMOUNT,
            "executedQty": PAPER_RISK_AMOUNT,
            "orderId": "PAPER",
            "leverage": None,
        }

    try:
        if not mt5.initialize():
            logger.error(f"❌ MT5 INIT FAILED: {mt5.last_error()}")
            return None

        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            logger.error(f"❌ SYMBOL NOT FOUND: {symbol}")
            return None

        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            logger.error(f"❌ NO TICK DATA: {symbol}")
            return None

        lot = calculate_lot_size(signal)

        if direction == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": float(signal["stop_loss"]),
            "tp": float(signal["take_profit"]),
            "deviation": 30,
            "magic": 20260613,
            "comment": "SNIPER_FOREX_MT5",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            logger.error(f"❌ MT5 ORDER SEND RETURNED NONE: {symbol}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"❌ MT5 ORDER FAILED {symbol}: retcode={result.retcode}")
            return None

        logger.info(f"✅ MT5 ORDER EXECUTED: {symbol} {direction} LOT={lot}")

        return {
            "paper": False,
            "symbol": symbol,
            "side": direction,
            "quantity": lot,
            "executedQty": lot,
            "orderId": str(result.order),
            "leverage": None,
        }

    except Exception as e:
        logger.error(f"❌ MT5 EXECUTION ERROR {symbol}: {e}")
        return None


def close_position(symbol, quantity=None):
    if not ENABLE_LIVE_TRADING or EXECUTION_MODE == "paper":
        logger.warning(f"🧪 MT5 PAPER CLOSE: {symbol}")
        return {
            "paper": True,
            "symbol": symbol,
            "side": "CLOSE",
            "quantity": quantity or 0,
            "leverage": None,
        }

    logger.warning("⚠️ LIVE CLOSE POSITION NOT FULLY ENABLED YET")
    return None