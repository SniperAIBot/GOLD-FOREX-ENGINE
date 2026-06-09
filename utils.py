import json

def fmt(value, decimals=5):
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def safe_json(value):
    try:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)

def symbol_decimals(symbol):
    if symbol in ["USDJPY", "EURJPY", "GBPJPY", "CADJPY"]:
        return 3
    if symbol in ["XAUUSD", "XAGUSD", "USOIL", "UKOIL", "NAS100", "US30", "SPX500"]:
        return 2
    return 5

def round_symbol_price(symbol, value):
    return round(float(value), symbol_decimals(symbol))
