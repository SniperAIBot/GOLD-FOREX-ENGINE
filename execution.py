from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.positions import PositionClose

from logger import logger
from oanda_client import get_oanda_api
from market_data import get_oanda_symbol
from config import (
    EXECUTION_MODE,
    ENABLE_LIVE_TRADING,
    OANDA_ACCOUNT_ID,
    OANDA_ENV,
    PAPER_RISK_AMOUNT,
    LIVE_RISK_AMOUNT
)


def calculate_units(signal):
    try:
        entry = float(signal["entry"])
        stop_loss = float(signal["stop_loss"])

        risk_amount = LIVE_RISK_AMOUNT
        risk_per_unit = abs(entry - stop_loss)

        if risk_per_unit <= 0:
            return 1

        units = int(risk_amount / risk_per_unit)

        if units <= 0:
            units = 1

        if signal["direction"] == "SELL":
            units = -abs(units)
        else:
            units = abs(units)

        return units

    except Exception as e:
        logger.error(f"❌ OANDA UNIT CALC ERROR: {e}")
        return 1


def execute_signal(signal):
    symbol = signal.get("symbol")
    direction = signal.get("direction")

    if not symbol or not direction:
        logger.error("❌ INVALID FOREX SIGNAL FOR EXECUTION")
        return None

    if EXECUTION_MODE == "paper" or not ENABLE_LIVE_TRADING:
        logger.warning(f"🧪 FOREX PAPER MODE - NO LIVE ORDER: {symbol} {direction}")

        return {
            "paper": True,
            "symbol": symbol,
            "side": direction,
            "quantity": PAPER_RISK_AMOUNT,
            "executedQty": PAPER_RISK_AMOUNT,
            "orderId": "PAPER",
            "leverage": None
        }

    if EXECUTION_MODE not in ["oanda_practice", "oanda_live"]:
        logger.error(f"❌ INVALID EXECUTION_MODE: {EXECUTION_MODE}")
        return None

    if EXECUTION_MODE == "oanda_live" and OANDA_ENV != "live":
        logger.error("❌ BLOCKED: EXECUTION_MODE=oanda_live BUT OANDA_ENV IS NOT live")
        return None

    if EXECUTION_MODE == "oanda_practice" and OANDA_ENV != "practice":
        logger.error("❌ BLOCKED: EXECUTION_MODE=oanda_practice BUT OANDA_ENV IS NOT practice")
        return None

    if not OANDA_ACCOUNT_ID:
        logger.error("❌ OANDA_ACCOUNT_ID IS MISSING")
        return None

    api = get_oanda_api()

    if api is None:
        return None

    try:
        instrument = get_oanda_symbol(symbol)
        units = calculate_units(signal)

        order_data = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "timeInForce": "FOK",
                "positionFill": "DEFAULT",
                "takeProfitOnFill": {
                    "price": str(signal["take_profit"])
                },
                "stopLossOnFill": {
                    "price": str(signal["stop_loss"])
                }
            }
        }

        request = OrderCreate(
            accountID=OANDA_ACCOUNT_ID,
            data=order_data
        )

        response = api.request(request)

        order_id = (
            response.get("orderCreateTransaction", {}).get("id")
            or response.get("orderFillTransaction", {}).get("id")
            or "OANDA_ORDER"
        )

        logger.info(f"✅ OANDA ORDER SENT: {symbol} {direction} UNITS={units}")

        return {
            "paper": False,
            "symbol": symbol,
            "side": direction,
            "quantity": abs(units),
            "executedQty": abs(units),
            "orderId": order_id,
            "leverage": None
        }

    except Exception as e:
        logger.error(f"❌ OANDA EXECUTION ERROR {symbol}: {e}")
        return None


def close_position(symbol, quantity=None):
    if EXECUTION_MODE == "paper" or not ENABLE_LIVE_TRADING:
        logger.warning(f"🧪 FOREX PAPER CLOSE: {symbol}")

        return {
            "paper": True,
            "symbol": symbol,
            "side": "CLOSE",
            "quantity": quantity or 0,
            "leverage": None
        }

    if not OANDA_ACCOUNT_ID:
        logger.error("❌ OANDA_ACCOUNT_ID IS MISSING")
        return None

    api = get_oanda_api()

    if api is None:
        return None

    try:
        instrument = get_oanda_symbol(symbol)

        data = {
            "longUnits": "ALL",
            "shortUnits": "ALL"
        }

        request = PositionClose(
            accountID=OANDA_ACCOUNT_ID,
            instrument=instrument,
            data=data
        )

        response = api.request(request)

        logger.info(f"✅ OANDA POSITION CLOSE REQUEST SENT: {symbol}")
        return response

    except Exception as e:
        logger.error(f"❌ OANDA CLOSE POSITION ERROR {symbol}: {e}")
        return None
