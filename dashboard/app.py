import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from database.db import engine, init_db
from dashboard.queries import (
    get_latest_quotes, get_latest_sentiment, get_sentiment_history,
    get_anomaly_alerts, get_recent_articles, get_price_history, get_latest_forecast,
)
from config import TICKERS

st.set_page_config(page_title="MarketPulse", layout="wide", page_icon="📈")


@st.cache_resource
def get_engine():
    init_db()
    return engine


db = get_engine()


def sentiment_color(score):
    if score is None:
        return "gray"
    if score > 0.2:
        return "#00c49a"
    if score < -0.2:
        return "#ff4b4b"
    return "#888888"


def sentiment_label(score):
    if score is None:
        return "N/A"
    if score > 0.2:
        return "Positive"
    if score < -0.2:
        return "Negative"
    return "Neutral"


quotes_df = get_latest_quotes(db)
sentiment_df = get_latest_sentiment(db)

# sidebar
with st.sidebar:
    st.title("MarketPulse")
    st.caption("Sentiment, anomalies, and forecasts")
    st.divider()
    ticker = st.selectbox("Select ticker", TICKERS)
    st.divider()
    if not quotes_df.empty:
        last_run = pd.to_datetime(quotes_df["fetched_at"].max())
        st.caption(f"Last ingestion: {last_run.strftime('%Y-%m-%d %H:%M')}")

# market overview — two rows of 4 so prices are not clipped
st.subheader("Market Overview")

for row_tickers in [TICKERS[:4], TICKERS[4:]]:
    cols = st.columns(4)
    for i, t in enumerate(row_tickers):
        q_row = quotes_df[quotes_df["ticker"] == t] if not quotes_df.empty else pd.DataFrame()
        s_row = sentiment_df[sentiment_df["ticker"] == t] if not sentiment_df.empty else pd.DataFrame()

        price = q_row["current_price"].iloc[0] if not q_row.empty else None
        pct = q_row["percent_change"].iloc[0] if not q_row.empty else None
        score = s_row["score"].iloc[0] if not s_row.empty else None

        with cols[i]:
            if price:
                st.metric(t, f"${price:.2f}", f"{pct:+.2f}%")
            else:
                st.metric(t, "N/A", "")
            color = sentiment_color(score)
            label = f"{score:.2f}" if score is not None else "—"
            st.markdown(f"<p style='color:{color}; font-size:13px; margin-top:-12px'>Sentiment {label}</p>", unsafe_allow_html=True)

st.divider()
st.subheader(f"{ticker} Deep Dive")

tab_sentiment, tab_forecast, tab_news, tab_anomalies, tab_shap = st.tabs([
    "Sentiment", "Forecast", "News Feed", "Anomaly Alerts", "SHAP"
])

# SENTIMENT TAB
with tab_sentiment:
    s_row = sentiment_df[sentiment_df["ticker"] == ticker] if not sentiment_df.empty else pd.DataFrame()
    score = s_row["score"].iloc[0] if not s_row.empty else None
    article_count = int(s_row["article_count"].iloc[0]) if not s_row.empty else 0

    col1, col2 = st.columns([1, 3])
    with col1:
        color = sentiment_color(score)
        label = sentiment_label(score)
        score_str = f"{score:.4f}" if score is not None else "No data"
        st.markdown(f"<h2 style='color:{color}'>{score_str}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{color}'>{label}</p>", unsafe_allow_html=True)
        st.caption(f"{article_count} articles analyzed")

    with col2:
        try:
            hist = get_sentiment_history(db, ticker)
        except Exception:
            pass
            hist = pd.DataFrame()
        if not hist.empty and len(hist) > 1:
            fig = px.line(hist, x="scored_at", y="score", title=f"{ticker} Sentiment Over Time",
                          template="plotly_dark")
            fig.add_hline(y=0.2, line_dash="dot", line_color="#00c49a", annotation_text="Positive")
            fig.add_hline(y=-0.2, line_dash="dot", line_color="#ff4b4b", annotation_text="Negative")
            fig.update_layout(yaxis_range=[-1, 1])
            st.plotly_chart(fig, use_container_width=True)
        elif not hist.empty:
            st.info("Sentiment chart builds up as the pipeline runs over multiple days. One data point recorded so far.")
            st.metric("Current Score", f"{hist['score'].iloc[0]:.4f}")
        else:
            st.info("No sentiment data yet. Run scripts/run_sentiment.py to populate.")

# FORECAST TAB
with tab_forecast:
    try:
        forecast_df = get_latest_forecast(db, ticker)
        price_df = get_price_history(db, ticker)
    except Exception:
        forecast_df = pd.DataFrame()
        price_df = pd.DataFrame()

    if forecast_df.empty:
        st.info("Forecast data not yet available. Run scripts/run_forecast.py to populate.")
    else:
        first = forecast_df.iloc[0]
        direction = "UP" if first["predicted_direction"] == 1 else "DOWN"
        dir_color = "#00c49a" if direction == "UP" else "#ff4b4b"
        acc = first["directional_accuracy"]

        col1, col2 = st.columns(2)
        col1.markdown(f"<h2 style='color:{dir_color}'>Forecast: {direction}</h2>", unsafe_allow_html=True)
        col2.metric("Backtested Directional Accuracy", f"{acc:.1%}" if acc else "N/A")

        fig = go.Figure()

        if not price_df.empty:
            fig.add_trace(go.Scatter(
                x=price_df["date"], y=price_df["close"],
                name="Historical", line=dict(color="#4a9eff"),
            ))

        fig.add_trace(go.Scatter(
            x=forecast_df["forecast_date"], y=forecast_df["upper_bound"],
            name="Upper Bound", line=dict(width=0), showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=forecast_df["forecast_date"], y=forecast_df["lower_bound"],
            name="Confidence Band", fill="tonexty",
            fillcolor="rgba(255,200,0,0.15)", line=dict(width=0),
        ))
        fig.add_trace(go.Scatter(
            x=forecast_df["forecast_date"], y=forecast_df["predicted_close"],
            name="Forecast", line=dict(color="#ffc800", dash="dash"),
            mode="lines+markers",
        ))

        fig.update_layout(template="plotly_dark", title=f"{ticker} Price Forecast (48h)")
        st.plotly_chart(fig, use_container_width=True)

# NEWS FEED TAB
with tab_news:
    try:
        articles = get_recent_articles(db, ticker)
    except Exception:
        articles = pd.DataFrame()
    if articles.empty:
        st.info("No news articles found for this ticker.")
    else:
        for _, row in articles.iterrows():
            score = row["sentiment_compound"]
            color = sentiment_color(score)
            label = sentiment_label(score)
            published = pd.to_datetime(row["published_at"]).strftime("%Y-%m-%d %H:%M") if pd.notna(row["published_at"]) else ""
            st.markdown(
                f"<div style='border-left: 3px solid {color}; padding-left: 10px; margin-bottom: 10px;'>"
                f"<b>{row['headline']}</b><br>"
                f"<span style='color:{color}; font-size:12px'>{label} ({score:.2f})</span>"
                f" &nbsp;|&nbsp; <span style='color:#888; font-size:12px'>{row['source_name']} &middot; {published}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

# ANOMALY ALERTS TAB
with tab_anomalies:
    try:
        alerts = get_anomaly_alerts(db)
    except Exception:
        alerts = pd.DataFrame()
    if alerts.empty:
        st.info("No anomalies detected yet. The detector activates after 3 or more pipeline runs per ticker.")
    else:
        st.dataframe(
            alerts.rename(columns={
                "ticker": "Ticker", "current_score": "Score",
                "baseline_mean": "Baseline", "z_score": "Z-Score", "detected_at": "Detected At",
            }),
            use_container_width=True,
        )

# SHAP TAB
with tab_shap:
    try:
        forecast_df = get_latest_forecast(db, ticker)
    except Exception:
        forecast_df = pd.DataFrame()
    if forecast_df.empty or forecast_df["sentiment_contribution"].isna().all():
        st.info("SHAP data not yet available. Run scripts/run_forecast.py to populate.")
    else:
        row = forecast_df.iloc[0]
        s_c = row["sentiment_contribution"] or 0
        p_c = row["price_contribution"] or 0
        d_c = row["dow_contribution"] or 0

        fig = go.Figure(go.Bar(
            x=[s_c, p_c, d_c],
            y=["Sentiment Score", "Price Momentum (5d)", "Day of Week"],
            orientation="h",
            marker_color=["#00c49a", "#4a9eff", "#ffc800"],
        ))
        fig.update_layout(
            template="plotly_dark",
            title=f"{ticker} Forecast Feature Importance (SHAP)",
            xaxis_title="Share of Prediction",
            xaxis_tickformat=".0%",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Sentiment contribution is derived from SHAP TreeExplainer on a RandomForest trained on sentiment score, 5-day price momentum, and day-of-week.")
