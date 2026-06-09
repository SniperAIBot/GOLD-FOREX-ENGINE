import pandas as pd
from indicators import prepare_dataframe

def swing_highs_lows(df, left=3, right=3):
    if df.empty or len(df) < left + right + 5:
        return [], []
    highs, lows = [], []
    for i in range(left, len(df) - right):
        h, l = df["high"].iloc[i], df["low"].iloc[i]
        if h == df["high"].iloc[i-left:i+right+1].max():
            highs.append((i, float(h)))
        if l == df["low"].iloc[i-left:i+right+1].min():
            lows.append((i, float(l)))
    return highs, lows

def detect_trend(df):
    if df.empty or len(df) < 60:
        return "NEUTRAL"
    close = df["close"]
    ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    last_close = close.iloc[-1]
    if ema20 > ema50 and last_close > ema20:
        return "BULLISH"
    if ema20 < ema50 and last_close < ema20:
        return "BEARISH"
    return "NEUTRAL"

def detect_fvg(df):
    if df.empty or len(df) < 5:
        return {"bullish": False, "bearish": False, "zone": None}
    recent = df.tail(12).reset_index(drop=True)
    bullish_zone, bearish_zone = None, None
    for i in range(2, len(recent)):
        c1, c3 = recent.iloc[i - 2], recent.iloc[i]
        if c1["high"] < c3["low"]:
            bullish_zone = (float(c1["high"]), float(c3["low"]))
        if c1["low"] > c3["high"]:
            bearish_zone = (float(c3["high"]), float(c1["low"]))
    if bullish_zone:
        return {"bullish": True, "bearish": False, "zone": bullish_zone}
    if bearish_zone:
        return {"bullish": False, "bearish": True, "zone": bearish_zone}
    return {"bullish": False, "bearish": False, "zone": None}

def detect_liquidity_sweep(df, direction):
    if df.empty or len(df) < 30:
        return False
    highs, lows = swing_highs_lows(df, 3, 3)
    last = df.iloc[-1]
    prev_close = df["close"].iloc[-2]
    if direction == "BUY" and lows:
        last_swing_low = lows[-1][1]
        return bool(last["low"] < last_swing_low and last["close"] > last_swing_low and last["close"] > prev_close)
    if direction == "SELL" and highs:
        last_swing_high = highs[-1][1]
        return bool(last["high"] > last_swing_high and last["close"] < last_swing_high and last["close"] < prev_close)
    return False

def detect_bos_or_choch(df, direction):
    if df.empty or len(df) < 40:
        return {"bos": False, "choch": False}
    highs, lows = swing_highs_lows(df, 3, 3)
    close = float(df["close"].iloc[-1])
    if direction == "BUY" and highs:
        bos = close > highs[-1][1]
        return {"bos": bool(bos), "choch": bool(bos)}
    if direction == "SELL" and lows:
        bos = close < lows[-1][1]
        return {"bos": bool(bos), "choch": bool(bos)}
    return {"bos": False, "choch": False}

def detect_order_block(df, direction):
    if df.empty or len(df) < 20:
        return {"found": False, "zone": None}
    recent = df.tail(20).reset_index(drop=True)
    if direction == "BUY":
        candidates = recent[recent["close"] < recent["open"]]
    elif direction == "SELL":
        candidates = recent[recent["close"] > recent["open"]]
    else:
        candidates = pd.DataFrame()
    if candidates.empty:
        return {"found": False, "zone": None}
    ob = candidates.iloc[-1]
    return {"found": True, "zone": (float(ob["low"]), float(ob["high"]))}

def premium_discount(df, direction):
    if df.empty or len(df) < 50:
        return False
    recent = df.tail(80)
    high = float(recent["high"].max())
    low = float(recent["low"].min())
    close = float(recent["close"].iloc[-1])
    equilibrium = (high + low) / 2
    if direction == "BUY":
        return close <= equilibrium
    if direction == "SELL":
        return close >= equilibrium
    return False

def get_smc_score(symbol, direction, candles_5m, candles_15m, candles_1h, candles_4h=None):
    df5 = prepare_dataframe(candles_5m)
    df15 = prepare_dataframe(candles_15m)
    df1h = prepare_dataframe(candles_1h)
    df4h = prepare_dataframe(candles_4h) if candles_4h is not None else pd.DataFrame()
    score, reasons = 0, []
    htf_df = df4h if not df4h.empty else df1h
    htf_label = "4H" if not df4h.empty else "1H"
    trend = detect_trend(htf_df)
    if direction == "BUY" and trend == "BULLISH":
        score += 20; reasons.append(f"{htf_label} bullish trend aligned")
    elif direction == "SELL" and trend == "BEARISH":
        score += 20; reasons.append(f"{htf_label} bearish trend aligned")
    else:
        reasons.append(f"{htf_label} trend not fully aligned")
    ob = detect_order_block(df1h, direction)
    if ob["found"]:
        score += 12; reasons.append("1H order block found")
    fvg_1h = detect_fvg(df1h)
    if (direction == "BUY" and fvg_1h["bullish"]) or (direction == "SELL" and fvg_1h["bearish"]):
        score += 12; reasons.append("1H FVG aligned")
    if premium_discount(df1h, direction):
        score += 10; reasons.append("Useful premium/discount area")
    sweep15 = detect_liquidity_sweep(df15, direction)
    if sweep15:
        score += 18; reasons.append("15M liquidity sweep detected")
    else:
        reasons.append("15M liquidity sweep not detected")
    structure5 = detect_bos_or_choch(df5, direction)
    if structure5["choch"]:
        score += 18; reasons.append("5M CHOCH/BOS detected")
    else:
        reasons.append("5M CHOCH/BOS not detected")
    fvg_5m = detect_fvg(df5)
    if (direction == "BUY" and fvg_5m["bullish"]) or (direction == "SELL" and fvg_5m["bearish"]):
        score += 10; reasons.append("5M execution FVG aligned")
    score = int(max(0, min(100, score)))
    if score >= 80:
        grade = "A+ SMC"
    elif score >= 65:
        grade = "A SMC"
    elif score >= 50:
        grade = "B SMC"
    elif score >= 35:
        grade = "C SMC"
    else:
        grade = "NO SMC CONFIRMATION"
    return {
        "smc_score": score, "smc_grade": grade, "smc_confirmed": score >= 65,
        "smc_reasons": reasons, "smc_trend": trend, "smc_order_block": ob["found"],
        "smc_fvg": bool((direction == "BUY" and (fvg_1h["bullish"] or fvg_5m["bullish"])) or (direction == "SELL" and (fvg_1h["bearish"] or fvg_5m["bearish"]))),
        "smc_sweep": sweep15, "smc_choch": structure5["choch"],
    }
