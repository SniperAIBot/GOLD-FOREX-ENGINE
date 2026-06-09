import streamlit as st
import plotly.express as px
import pandas as pd
from database import get_all_signals, get_symbol_performance, get_smc_performance
from performance import get_statistics

st.set_page_config(page_title="SNIPER FOREX DASHBOARD", layout="wide")

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #e9ecf2 0%, #f7f8fb 100%); color: #111827;}
.big-title {font-size:48px; font-weight:900; color:#111827; text-align:center; margin-bottom:5px;}
.subtitle {font-size:18px; color:#4b5563; text-align:center; margin-bottom:30px;}
.vip-badge {background:linear-gradient(135deg,#111827,#374151); color:#facc15; padding:12px 22px; border-radius:999px; text-align:center; font-weight:900; font-size:18px; box-shadow:0px 10px 30px rgba(17,24,39,0.25); margin-bottom:25px;}
div[data-testid="stMetric"] {background:linear-gradient(180deg,#ffffff 0%,#f3f4f6 100%); border:1px solid #d1d5db; padding:18px; border-radius:18px; box-shadow:0px 8px 20px rgba(17,24,39,0.08);}
</style>
""", unsafe_allow_html=True)

def dict_to_dataframe(data, label_name):
    rows = []
    for key, values in data.items():
        row = {label_name: key}
        row.update(values)
        rows.append(row)
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def build_ai_dataframe(ai_performance):
    rows = []
    for symbol, data in ai_performance.items():
        weight = data.get("weight", 1.0)
        if weight >= 3:
            tier = "🟢 Elite 3X"
        elif weight >= 2:
            tier = "🟩 Strong 2X"
        elif weight >= 1:
            tier = "🟨 Normal 1X"
        elif weight >= 0.5:
            tier = "🟧 Weak 0.5X"
        else:
            tier = "🔴 Very Weak 0.25X"
        rows.append({"symbol": symbol, "tier": tier, "priority": data.get("priority", "🔥 Normal Focus"), "wins": data.get("wins", 0), "losses": data.get("losses", 0), "trades": data.get("trades", 0), "win_rate": data.get("win_rate", 0), "profit_factor": data.get("profit_factor", 0), "avg_rr": data.get("avg_rr", 0), "ai_score": data.get("score", 0), "ai_weight": data.get("weight", 1.0), "min_confidence": data.get("confidence_required", 72), "avg_smc_score": data.get("avg_smc_score", 0), "smc_confirmed_trades": data.get("smc_confirmed_trades", 0)})
    if not rows:
        return pd.DataFrame()
    result = pd.DataFrame(rows)
    return result.sort_values(by=["ai_weight", "ai_score"], ascending=False)

st.markdown("<div class='big-title'>🚀 SNIPER FOREX ENGINE V1.0</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Forex • Gold • Commodities • AI Ranking • SMC Matrix • Paper Trading</div>", unsafe_allow_html=True)
st.markdown("<div class='vip-badge'>👑 FOREX PERFORMANCE COMMAND CENTER</div>", unsafe_allow_html=True)
st.success("🧠 SNIPER FOREX DASHBOARD LOADED")

df = get_all_signals()
if df.empty:
    st.warning("No forex signals yet.")
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df["closed_at"] = pd.to_datetime(df["closed_at"], errors="coerce")
stats = get_statistics()

st.divider()
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Trades", stats.get("total_trades", 0))
m2.metric("Total Signals", stats.get("total_signals", 0))
m3.metric("Closed Trades", stats.get("closed_trades", 0))
m4.metric("Open Trades", stats.get("open_trades", 0))
m5.metric("Wins 🟢", stats.get("wins", 0))
m6.metric("Losses 🔴", stats.get("losses", 0))
m7, m8, m9, m10 = st.columns(4)
m7.metric("Win Rate 🏆", f"{stats.get('win_rate', 0)}%")
m8.metric("Expectancy 💎", stats.get("expectancy", 0))
m9.metric("Average RR ⚡", stats.get("avg_rr", 0))
m10.metric("Profit Factor", stats.get("profit_factor", 0))

st.divider()
st.subheader("🧠 SMC Performance")
smc_df = dict_to_dataframe(get_smc_performance(days=30), "smc_grade")
if not smc_df.empty:
    st.dataframe(smc_df, use_container_width=True)
    st.plotly_chart(px.bar(smc_df, x="smc_grade", y="win_rate", text="win_rate", title="SMC Grade Win Rate"), use_container_width=True)
else:
    st.info("No closed SMC performance yet.")

st.divider()
st.subheader("🤖 AI Symbol Ranking")
ai_df = build_ai_dataframe(get_symbol_performance(days=7, min_trades=10))
if not ai_df.empty:
    st.dataframe(ai_df, use_container_width=True)
    st.plotly_chart(px.treemap(ai_df, path=["tier", "symbol"], values="trades", color="ai_weight", title="Forex AI Ranking Heatmap"), use_container_width=True)
else:
    st.info("No AI ranking data yet.")

st.divider()
st.subheader("📊 Result Distribution")
result_df = df[df["result"].notna()].groupby("result").size().reset_index(name="count")
if not result_df.empty:
    st.plotly_chart(px.pie(result_df, names="result", values="count", title="WIN vs LOSS Distribution", hole=0.45), use_container_width=True)

st.divider()
st.subheader("🟡 Open Trades")
open_df = df[df["status"] == "OPEN"]
if not open_df.empty:
    st.dataframe(open_df, use_container_width=True)
else:
    st.success("No open forex trades.")

st.divider()
st.subheader("🗂 Full Forex Trade History")
st.dataframe(df, use_container_width=True)
