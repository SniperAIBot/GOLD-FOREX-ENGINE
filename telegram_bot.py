import requests
from logger import logger
from config import BOT_TOKEN, PUBLIC_CHAT_ID, VIP_CHAT_ID, VIP_LINK

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(chat_id, text):
    try:
        if not BOT_TOKEN:
            logger.error("❌ FOREX BOT_TOKEN IS MISSING")
            return None
        if not chat_id:
            logger.error("❌ FOREX TELEGRAM CHAT ID IS MISSING")
            return None
        response = requests.post(BASE_URL, json={"chat_id": chat_id, "text": text}, timeout=10)
        logger.info(f"📨 FOREX TELEGRAM STATUS: {response.status_code}")
        logger.info(f"📨 FOREX TELEGRAM RESPONSE: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ FOREX TELEGRAM ERROR: {e}")
        return None

def format_bool(value):
    if value is True:
        return "✅ Yes"
    if value is False:
        return "❌ No"
    return "N/A"

def format_smc_reasons(signal):
    reasons = signal.get("smc_reasons", [])
    if not reasons:
        return "No SMC reasons available."
    if isinstance(reasons, str):
        return reasons
    try:
        return "\n".join([f"• {reason}" for reason in reasons[:6]])
    except Exception:
        return str(reasons)

def send_public_signal(signal):
    try:
        direction_emoji = "📈" if signal["direction"] == "BUY" else "📉"
        message = f"""
🚨 SNIPER FOREX SIGNAL

💰 Symbol:
{signal['symbol']}

📊 Direction:
{signal['direction']} {direction_emoji}

🎯 Confidence:
{signal['confidence']}%

🧠 SMC Grade:
{signal.get('smc_grade', 'Standard')}

📈 Market:
{signal['market_regime']}

🔒 Full details in VIP
{VIP_LINK}
"""
        send_message(PUBLIC_CHAT_ID, message)
    except Exception as e:
        logger.error(f"❌ FOREX PUBLIC SIGNAL ERROR: {e}")

def send_vip_signal(signal, win_rate=0):
    try:
        direction_emoji = "📈" if signal["direction"] == "BUY" else "📉"
        message = f"""
🚨 SNIPER FOREX VIP SIGNAL

💰 Symbol:
{signal['symbol']}

📊 Direction:
{signal['direction']} {direction_emoji}

💵 Entry:
{signal['entry']}

🎯 TP:
{signal['take_profit']}

🛑 SL:
{signal['stop_loss']}

📈 Confidence:
{signal['confidence']}%

📊 RSI:
{signal['rsi']}

⚡ ATR:
{signal['atr']}

🎲 RR:
{signal.get('rr', 'N/A')}

🔥 Market:
{signal['market_regime']}

━━━━━━━━━━━━━━
🧠 SMC CHECK

🏷️ Grade:
{signal.get('smc_grade', 'N/A')}

📊 Score:
{signal.get('smc_score', 'N/A')}/100

✅ Confirmed:
{format_bool(signal.get('smc_confirmed'))}

📌 Reasons:
{format_smc_reasons(signal)}

━━━━━━━━━━━━━━
🤖 AI RANKING

⚖️ AI Weight:
{signal.get('ai_weight', 'N/A')}

📊 Symbol AI Win Rate:
{signal.get('ai_win_rate', 'N/A')}%

🔢 Symbol AI Trades:
{signal.get('ai_trades', 'N/A')}

📉 System Win Rate:
{win_rate}%
"""
        send_message(VIP_CHAT_ID, message)
    except Exception as e:
        logger.error(f"❌ FOREX VIP SIGNAL ERROR: {e}")
