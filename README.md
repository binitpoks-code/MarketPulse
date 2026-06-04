# MarketPulse

A real-time stock market intelligence dashboard that aggregates news, scores sentiment, detects anomalies, and generates 48-hour price direction forecasts for major US equities.

Built as a portfolio project targeting Data Analyst and Associate Data Engineer roles.

---

## What It Does

MarketPulse continuously ingests data from three sources, processes it through a multi-stage pipeline, and surfaces the results in an interactive Streamlit dashboard.

**Tracked tickers:** AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META, SPY

| Dashboard Panel | What It Shows |
|---|---|
| Market Overview | Live price, % change, and sentiment score for all 8 tickers |
| Sentiment | Compound VADER score + historical trend chart per ticker |
| News Feed | Latest 25 articles with per-article sentiment coloring |
| Anomaly Alerts | Z-score alerts when sentiment deviates significantly from baseline |
| Forecast | 48-hour Prophet price forecast with confidence band |
| SHAP | Feature importance breakdown: sentiment vs. price momentum vs. day-of-week |

---

## Architecture

```
Ingestion  →  Processing  →  Sentiment  →  Anomaly Detection  →  Forecasting
(APIs)        (clean/CSV)    (VADER/DB)     (z-score/DB)          (Prophet+SHAP)
                                                    ↓
                                            Streamlit Dashboard
                                            (PostgreSQL backend)
```

**Pipeline stages** (run in sequence via `scripts/run_pipeline.py`):

1. **Ingestion** — fetches quotes from Finnhub, articles from Finnhub + NewsAPI, price history from Yahoo Finance
2. **Processing** — cleans and normalizes raw JSON into structured CSVs
3. **Sentiment** — scores each article with VADER, aggregates per-ticker scores, stores in PostgreSQL
4. **Anomaly Detection** — computes z-scores against rolling baseline, writes alerts when threshold exceeded
5. **Forecasting** — trains Prophet on price + sentiment features, generates 48-hour forecast, explains with SHAP TreeExplainer

**Kafka integration** — a parallel streaming pipeline (`kafka_pipeline/`) publishes quotes to a Kafka topic for event-driven downstream consumers.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data ingestion | Finnhub API, NewsAPI, yfinance |
| NLP / Sentiment | VADER (vaderSentiment) |
| Forecasting | Prophet, scikit-learn RandomForest |
| Explainability | SHAP TreeExplainer |
| Database | PostgreSQL + SQLAlchemy ORM |
| Dashboard | Streamlit + Plotly |
| Streaming | Apache Kafka + Zookeeper |
| Containerization | Docker Compose |
| Language | Python 3.11 |

---

## Project Structure

```
MarketPulse/
├── ingestion/          # API fetch scripts (Finnhub, NewsAPI, Yahoo)
├── processing/         # Raw JSON → cleaned CSV
├── pipeline/           # Sentiment, anomaly, forecasting logic
├── dashboard/          # Streamlit app + query layer
├── database/           # SQLAlchemy models + session management
├── kafka_pipeline/     # Kafka producer/consumer
├── scripts/            # Entry points: run_pipeline.py, run_*.py
├── data/               # raw/ and processed/ (gitignored)
├── docker-compose.yml
├── config.py
└── requirements.txt
```

---

## Setup

**Prerequisites:** Python 3.11, PostgreSQL, API keys for Finnhub and NewsAPI (free tiers sufficient).

```bash
# 1. Clone and create virtual environment
git clone https://github.com/binitpoks-code/MarketPulse.git
cd MarketPulse
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env        # then fill in your API keys and DB credentials
```

**.env format:**
```
NEWS_API_KEY=your_key
FINNHUB_API_KEY=your_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=marketpulse
DB_USER=postgres
DB_PASSWORD=your_password
```

```bash
# 4. Create the database
createdb marketpulse

# 5. Run the pipeline (fetches data and populates the database)
python scripts/run_pipeline.py

# 6. Start the dashboard
streamlit run dashboard/app.py
```

---

## Docker (Optional)

Runs PostgreSQL, Zookeeper, Kafka, and the app together:

```bash
docker-compose up --build
```

---

## Running with Kafka

```bash
# In one terminal
python scripts/run_kafka_producer.py

# In another terminal
python scripts/run_kafka_consumer.py
```

---

## Notes

- Yahoo Finance enforces rate limits. If `price_history` and `forecast_results` are empty after the pipeline run, wait a few hours and run `python scripts/run_pipeline.py` again. The ingestion layer handles timeouts gracefully and skips failed tickers.
- Anomaly alerts require at least 3 pipeline runs per ticker to establish a baseline.
- SHAP feature importance is only available once forecast data exists.
