from database import get_connection
from logger import logger

def default_statistics():
    return {"total_trades": 0, "total_signals": 0, "open_trades": 0, "closed_trades": 0, "wins": 0, "losses": 0, "breakeven": 0, "win_rate": 0, "expectancy": 0, "avg_rr": 0, "profit_factor": 0}

def get_statistics():
    conn = get_connection()
    if conn is None:
        return default_statistics()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM forex_signals;")
        total_signals = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM forex_signals WHERE status='OPEN';")
        open_trades = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM forex_signals WHERE result='WIN';")
        wins = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM forex_signals WHERE result='LOSS';")
        losses = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM forex_signals WHERE result='BREAKEVEN';")
        breakeven = cur.fetchone()[0]
        closed_trades = wins + losses + breakeven
        total_trades = closed_trades
        cur.execute("SELECT AVG(rr) FROM forex_signals WHERE result='WIN';")
        avg_rr = cur.fetchone()[0] or 0
        closed_for_winrate = wins + losses
        if closed_for_winrate > 0:
            win_rate = (wins / closed_for_winrate) * 100
            loss_rate = losses / closed_for_winrate
            expectancy = ((wins / closed_for_winrate) * avg_rr) - loss_rate
            profit_factor = (wins * avg_rr) / losses if losses > 0 else wins * avg_rr
        else:
            win_rate, expectancy, profit_factor = 0, 0, 0
        cur.close()
        conn.close()
        return {"total_trades": total_trades, "total_signals": total_signals, "open_trades": open_trades, "closed_trades": closed_trades, "wins": wins, "losses": losses, "breakeven": breakeven, "win_rate": round(win_rate, 2), "expectancy": round(expectancy, 2), "avg_rr": round(avg_rr, 2), "profit_factor": round(profit_factor, 2)}
    except Exception as e:
        logger.error(f"❌ FOREX PERFORMANCE ERROR: {e}")
        return default_statistics()
