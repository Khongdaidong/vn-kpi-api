# 3_api.py  ── FastAPI micro-service for VN-Index KPIs
# ----------------------------------------------------------------------
# • Deploy on Render, Fly.io, Railway, etc.
# • Requires three environment variables set in the host dashboard:
#     AIRTABLE_BASE   = "appXXXXXXXXXXXXXX"
#     AIRTABLE_TABLE  = "tblXXXXXXXXXXXXXX"   (or the table name e.g. KPI_FPT)
#     AIRTABLE_PAT    = "patXXXXXXXXXXXXXX"   (personal access token w/ read)
# • Start command for Render:  uvicorn 3_api:app --port $PORT --host 0.0.0.0
# ----------------------------------------------------------------------

from fastapi import FastAPI
import os, requests

# ── 1. Credentials & constants
AIRBASE        = os.environ["AIRTABLE_BASE"]
AIRTABLE_TABLE = os.environ["AIRTABLE_TABLE"]
AIR_KEY        = os.environ["AIRTABLE_PAT"]

HEADERS = {"Authorization": f"Bearer {AIR_KEY}"}
AIR_URL = f"https://api.airtable.com/v0/{AIRBASE}/{AIRTABLE_TABLE}"

app = FastAPI(
    title="VN-Index KPI API",
    description="Returns latest KPI rows for any ticker stored in Airtable."
)

# ── 2. Helper that hits Airtable once per request
def fetch_latest_records(ticker: str):
    params = {
        "filterByFormula": f"{{Ticker}}='{ticker.upper()}'",
        "sort[0][field]": "date",
        "sort[0][direction]": "desc",
        "pageSize": 100
    }
    res = requests.get(AIR_URL, params=params, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return res.json().get("records", [])

# ── 3. One route: /kpi/FPT  (or /kpi/VCB etc.)
@app.get("/kpi/{ticker}")
def latest_kpi(ticker: str):
    records = fetch_latest_records(ticker)
    seen, latest = set(), []

    for rec in records:               # records already sorted newest→oldest
        fields = rec["fields"]
        kpi_name = fields.get("kpi")
        if kpi_name and kpi_name not in seen:
            latest.append(fields)     # keep first (i.e. newest) occurrence
            seen.add(kpi_name)

    return latest                     # JSON list of dicts
