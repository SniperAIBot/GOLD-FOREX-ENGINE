import os
import math
import pandas as pd
import psycopg2

from psycopg2.extras import RealDictCursor
from logger import logger
from utils import safe_json


DATABASE_URL = os.getenv("DATABASE_URL")


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():
    try:
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL IS MISSING")
            return None

        return psycopg2.connect(DATABASE_URL)

    except Exception as e:
        logger.error(f"❌ FOREX DATABASE CONNECTION ERROR: {e}")
        return None


# =====================================================
# INITIALIZE / MIGRATE DATABASE
# =====================================================

def initialize_database():
    conn = get_connection()

    if conn is None:
        return

    try:
        cur = conn.cursor()

        cur.execute(
            """
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
            """
        )

        migration_columns = [
            "symbol TEXT",
            "direction TEXT",
            "entry DOUBLE PRECISION",
            "take_profit DOUBLE PRECISION",
            "stop_loss DOUBLE PRECISION",
            "confidence DOUBLE PRECISION",
            "rsi DOUBLE PRECISION",
            "atr DOUBLE PRECISION",
            "rr DOUBLE PRECISION",
            "market_regime TEXT",
            "strategy_version TEXT",
            "status TEXT DEFAULT 'OPEN'",
            "result TEXT",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "closed_at TIMESTAMP",
            "execution_mode TEXT",
            "order_id TEXT",
            "executed_side TEXT",
            "executed_quantity DOUBLE PRECISION",
            "leverage DOUBLE PRECISION",
            "ai_weight DOUBLE PRECISION",
            "ai_win_rate DOUBLE PRECISION",
            "ai_trades INTEGER",
            "smc_score DOUBLE PRECISION",
            "smc_grade TEXT",
            "smc_confirmed BOOLEAN",
            "smc_reasons TEXT",
            "smc_trend TEXT",
            "smc_order_block BOOLEAN",
            "smc_fvg BOOLEAN",
            "smc_sweep BOOLEAN",
            "smc_choch BOOLEAN",
        ]

        for column in migration_columns:
            try:
                cur.execute(
                    f"""
                    ALTER TABLE forex_signals
                    ADD COLUMN IF NOT EXISTS {column};
                    """
                )
            except Exception as col_error:
                logger.error(
                    f"❌ FOREX COLUMN MIGRATION ERROR {column}: {col_error}"
                )

        conn.commit()

        cur.close()
        conn.close()

        logger.info("✅ FOREX DATABASE INITIALIZED / TABLE forex_signals READY")

    except Exception as e:
        logger.error(f"❌ FOREX DATABASE INIT ERROR: {e}")

        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass


# =====================================================
# SAVE SIGNAL
# =====================================================

def save_signal(signal, execution_result=None):
    conn = get_connection()

    if conn is None:
        return False

    try:
        execution_mode = None
        order_id = None
        executed_side = None
        executed_quantity = None
        leverage = None

        if execution_result:
            execution_mode = "PAPER" if execution_result.get("paper") else "LIVE"
            order_id = str(execution_result.get("orderId", ""))
            executed_side = execution_result.get("side")
            executed_quantity = execution_result.get(
                "executedQty",
                execution_result.get("quantity")
            )
            leverage = execution_result.get("leverage")

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO forex_signals (
                symbol,
                direction,
                entry,
                take_profit,
                stop_loss,
                confidence,
                rsi,
                atr,
                rr,
                market_regime,
                strategy_version,
                status,
                result,
                execution_mode,
                order_id,
                executed_side,
                executed_quantity,
                leverage,
                ai_weight,
                ai_win_rate,
                ai_trades,
                smc_score,
                smc_grade,
                smc_confirmed,
                smc_reasons,
                smc_trend,
                smc_order_block,
                smc_fvg,
                smc_sweep,
                smc_choch
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            );
            """,
            (
                signal.get("symbol"),
                signal.get("direction"),
                signal.get("entry"),
                signal.get("take_profit"),
                signal.get("stop_loss"),
                signal.get("confidence"),
                signal.get("rsi"),
                signal.get("atr"),
                signal.get("rr"),
                signal.get("market_regime"),
                signal.get("strategy_version", "unknown"),
                "OPEN",
                None,
                execution_mode,
                order_id,
                executed_side,
                executed_quantity,
                leverage,
                signal.get("ai_weight"),
