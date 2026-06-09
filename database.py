import math
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from logger import logger
from config import DATABASE_URL
from utils import safe_json

def get_connection():
    try:
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL IS MISSING")
            return None
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"❌ DATABASE CONNECTION ERROR: {e}")
        return None

def initialize_database():
    conn = get_connection()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS forex_signals (
                id SERIAL PRIMARY KEY,
                symbol TEXT,
                direction TEXT,
                entry DOUBLE PRECISION,
                take_profit DOUBLE PRECISION,
                stop_loss DOUBLE PRECISION,
                confidence DOUBLE PRECISION,
                rsi DOUBLE PRECISION,
                atr DOUBLE PRECISION,
                rr DOUBLE PRECISION,
                market_regime TEXT,
                strategy_version TEXT,
                status TEXT DEFAULT 'OPEN',
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                execution_mode TEXT,
                order_id TEXT,
                executed_side TEXT,
                executed_quantity DOUBLE PRECISION,
                leverage DOUBLE PRECISION,
                ai_weight DOUBLE PRECISION,
                ai_win_rate DOUBLE PRECISION,
                ai_trades INTEGER,
                smc_score DOUBLE PRECISION,
                smc_grade TEXT,
                smc_confirmed BOOLEAN,
                smc_reasons TEXT,
                smc_trend TEXT,
                smc_order_block BOOLEAN,
                smc_fvg BOOLEAN,
                smc_sweep BOOLEAN,
                smc_choch BOOLEAN
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ FOREX DATABASE INITIALIZED / MIGRATED")
    except Exception as e:
        logger.error(f"❌ FOREX DATABASE INIT ERROR: {e}")

def save_signal(signal, execution_result=None):
    conn = get_connection()
    if conn is None:
        return False
    try:
        execution_mode = order_id = executed_side = executed_quantity = leverage = None
        if execution_result:
            execution_mode = "PAPER" if execution_result.get("paper") else "LIVE"
            order_id = str(execution_result.get("orderId", ""))
            executed_side = execution_result.get("side")
            executed_quantity = execution_result.get("executedQty", execution_result.get("quantity"))
            leverage = execution_result.get("leverage")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO forex_signals (
                symbol, direction, entry, take_profit, stop_loss, confidence, rsi, atr, rr,
                market_regime, strategy_version, status, result, execution_mode, order_id,
                executed_side, executed_quantity, leverage, ai_weight, ai_win_rate, ai_trades,
                smc_score, smc_grade, smc_confirmed, smc_reasons, smc_trend, smc_order_block,
                smc_fvg, smc_sweep, smc_choch
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            );
        """, (
            signal.get("symbol"), signal.get("direction"), signal.get("entry"),
            signal.get("take_profit"), signal.get("stop_loss"), signal.get("confidence"),
            signal.get("rsi"), signal.get("atr"), signal.get("rr"), signal.get("market_regime"),
            signal.get("strategy_version", "unknown"), "OPEN", None, execution_mode, order_id,
            executed_side, executed_quantity, leverage, signal.get("ai_weight"), signal.get("ai_win_rate"),
            signal.get("ai_trades"), signal.get("smc_score"), signal.get("smc_grade"),
            signal.get("smc_confirmed"), safe_json(signal.get("smc_reasons")), signal.get("smc_trend"),
            signal.get("smc_order_block"), signal.get("smc_fvg"), signal.get("smc_sweep"), signal.get("smc_choch")
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ FOREX SIGNAL SAVED: {signal.get('symbol')} SMC_SCORE={signal.get('smc_score', 'N/A')}")
        return True
    except Exception as e:
        logger.error(f"❌ FOREX SAVE SIGNAL ERROR: {e}")
        return False

def get_open_signals():
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM forex_signals WHERE status='OPEN' ORDER BY id ASC;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"❌ FOREX GET OPEN SIGNALS ERROR: {e}")
        return []

def close_signal(signal_id, result):
    conn = get_connection()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("UPDATE forex_signals SET status='CLOSED', result=%s, closed_at=CURRENT_TIMESTAMP WHERE id=%s;", (result, signal_id))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ FOREX SIGNAL CLOSED: {signal_id} {result}")
        return True
    except Exception as e:
        logger.error(f"❌ FOREX CLOSE SIGNAL ERROR: {e}")
        return False

def get_all_signals():
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql("SELECT * FROM forex_signals ORDER BY id DESC;", conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"❌ FOREX GET ALL SIGNALS ERROR: {e}")
        return pd.DataFrame()

def get_recent_closed_results(limit=10):
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT symbol, result, closed_at FROM forex_signals WHERE result IN ('WIN','LOSS') ORDER BY closed_at DESC LIMIT %s;", (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"❌ FOREX RECENT RESULTS ERROR: {e}")
        return []

def get_symbol_performance(days=7, min_trades=10):
    conn = get_connection()
    if conn is None:
        return {}
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT symbol,
                COUNT(*) FILTER (WHERE result='WIN') AS wins,
                COUNT(*) FILTER (WHERE result='LOSS') AS losses,
                COUNT(*) FILTER (WHERE result IN ('WIN','LOSS')) AS trades,
                AVG(rr) FILTER (WHERE result='WIN') AS avg_rr,
                AVG(smc_score) FILTER (WHERE result IN ('WIN','LOSS')) AS avg_smc_score,
                COUNT(*) FILTER (WHERE smc_confirmed = TRUE) AS smc_confirmed_trades
            FROM forex_signals
            WHERE created_at >= NOW() - (%s * INTERVAL '1 day') AND result IN ('WIN','LOSS')
            GROUP BY symbol;
        """, (days,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        performance = {}
        for row in rows:
            symbol = row["symbol"]
            wins, losses, trades = row["wins"] or 0, row["losses"] or 0, row["trades"] or 0
            avg_rr, avg_smc_score = row["avg_rr"] or 0, row["avg_smc_score"] or 0
            smc_confirmed_trades = row["smc_confirmed_trades"] or 0
            if trades <= 0:
                continue
            win_rate = (wins / trades) * 100
            profit_factor = (wins * avg_rr) / losses if losses > 0 else wins * avg_rr
            if trades < min_trades:
                weight, confidence_required = 1.0, 72
            elif win_rate >= 80:
                weight, confidence_required = 3.0, 65
            elif win_rate >= 65:
                weight, confidence_required = 2.0, 68
            elif win_rate >= 55:
                weight, confidence_required = 1.0, 72
            elif win_rate >= 40:
                weight, confidence_required = 0.5, 80
            else:
                weight, confidence_required = 0.25, 88
            if trades < 15 and weight > 1.0:
                weight, confidence_required = 1.0, 72
            score = (win_rate * 0.5) + (profit_factor * 20) + (avg_rr * 10) + (math.log(trades + 1) * 10) - (losses * 0.75)
            if avg_smc_score >= 65:
                score += 5
            if avg_smc_score >= 80:
                score += 10
            if weight >= 3:
                priority = "🔥🔥🔥 Elite Focus"
            elif weight >= 2:
                priority = "🔥🔥 Strong Focus"
            elif weight >= 1:
                priority = "🔥 Normal Focus"
            elif weight >= 0.5:
                priority = "⚠️ Low Focus"
            else:
                priority = "🧊 Very Low Focus"
            performance[symbol] = {
                "wins": wins, "losses": losses, "trades": trades, "win_rate": round(win_rate, 2),
                "avg_rr": round(avg_rr, 2), "profit_factor": round(profit_factor, 2),
                "score": round(score, 2), "weight": weight, "confidence_required": confidence_required,
                "priority": priority, "avg_smc_score": round(avg_smc_score, 2),
                "smc_confirmed_trades": smc_confirmed_trades
            }
        return performance
    except Exception as e:
        logger.error(f"❌ FOREX SYMBOL PERFORMANCE ERROR: {e}")
        return {}

def get_symbol_profile(symbol, days=7):
    performance = get_symbol_performance(days=days, min_trades=10)
    if symbol in performance:
        return performance[symbol]
    return {"wins": 0, "losses": 0, "trades": 0, "win_rate": 0, "avg_rr": 0, "profit_factor": 0, "score": 0, "weight": 1.0, "confidence_required": 72, "priority": "🔥 Normal Focus", "avg_smc_score": 0, "smc_confirmed_trades": 0}

def get_smc_performance(days=7):
    conn = get_connection()
    if conn is None:
        return {}
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT COALESCE(smc_grade, 'UNKNOWN') AS smc_grade,
                COUNT(*) FILTER (WHERE result='WIN') AS wins,
                COUNT(*) FILTER (WHERE result='LOSS') AS losses,
                COUNT(*) FILTER (WHERE result IN ('WIN','LOSS')) AS trades,
                AVG(smc_score) FILTER (WHERE result IN ('WIN','LOSS')) AS avg_smc_score
            FROM forex_signals
            WHERE created_at >= NOW() - (%s * INTERVAL '1 day') AND result IN ('WIN','LOSS')
            GROUP BY smc_grade ORDER BY avg_smc_score DESC;
        """, (days,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        performance = {}
        for row in rows:
            grade = row["smc_grade"]
            wins, losses, trades = row["wins"] or 0, row["losses"] or 0, row["trades"] or 0
            avg_smc_score = row["avg_smc_score"] or 0
            win_rate = (wins / trades) * 100 if trades > 0 else 0
            performance[grade] = {"wins": wins, "losses": losses, "trades": trades, "win_rate": round(win_rate, 2), "avg_smc_score": round(avg_smc_score, 2)}
        return performance
    except Exception as e:
        logger.error(f"❌ FOREX SMC PERFORMANCE ERROR: {e}")
        return {}
