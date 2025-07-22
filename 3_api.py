# 3_api.py
import os
from typing import List

import requests
from fastapi import FastAPI, HTTPException

# --- 1. Read environment variables -------------------------------------------------
AIRTABLE_BASE_ID   = os.getenv("AIRTABLE_BASE_ID",  "appccCEUPWDVAXplx")
AIRTABLE_TABLE_ID  = os.getenv("AIRTABLE_TABLE_ID", "tblu2pQj85sT7jY6")   # or the plain-text table name
AIRTABLE_TOKEN     = os.getenv("AIRTABLE_TOKEN")                         # must start with pat…

# Safety check: fail fast if the token is missing
if not AIRTABLE_TOKEN:
    raise RuntimeError("⚠️  AIRTABLE_TOKEN environment variable is missing")

# Show just the first 5 chars so you can confirm the token loads (remove after testing)
print("DEBUG TOKEN prefix:", AIRTABLE_TOKEN[:5])

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type":  "application/json",
}

# --- 2. Initialise FastAPI ----------------------------------------------------------
app = FastAPI(title="VN KPI API")

# --- 3. Helper to fetch the latest KPI rows ----------------------------------------
def fetch_latest_records(ticker: str, page_size: int = 100) -> List[dict]:
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    params = {
        "filterByFormula": f"{{Ticker}}='{ticker}'",
        "sort[0][field]":  "date",
        "sort[0][direction]": "desc",
        "pageSize": page_size,
    }

    res = requests.get(url, headers=HEADERS, params=params)
    print("DEBUG Airtable status:", res.status_code)          # optional
    res.raise_for_status()                                    # will raise for 4xx/5xx
    records = res.json().get("records", [])
    return [r["fields"] for r in records]

# --- 4. Route -----------------------------------------------------------------------
@app.get("/kpi/{ticker}")
def latest_kpi(ticker: str):
    try:
        data = fetch_latest_records(ticker.upper())
        if not data:
            raise HTTPException(status_code=404, detail="No records found")
        return data
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
