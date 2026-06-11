import oandapyV20
from logger import logger
from config import OANDA_API_KEY, OANDA_ENV


def get_oanda_api():
    if not OANDA_API_KEY:
        logger.error("❌ OANDA_API_KEY IS MISSING")
        return None

    try:
        return oandapyV20.API(
            access_token=OANDA_API_KEY,
            environment=OANDA_ENV
        )
    except Exception as e:
        logger.error(f"❌ OANDA API INIT ERROR: {e}")
        return None
