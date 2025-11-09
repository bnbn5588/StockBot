import requests
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import pandas as pd

# Load variables from .env
load_dotenv()

# ----- CONFIG -----
# TICKER = ["AAPL", "ORCL", "AMZN", "CRM", "MSFT", "GOOGL", "META", "TSLA", "NVDA", "AMD", "CONY"]
TICKER = ["AAPL", "ORCL", "AMZN", "MSFT", "GOOGL", "META", "NVDA", "AMD", "TSM", "MU"]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SHEET_NAME = os.getenv("TICKER_SHEET_NAME")


csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# Read data into a DataFrame
df = pd.read_csv(csv_url)

# Assuming tickers are in the first column
TICKER = df.iloc[:, 0].dropna().tolist()

print(TICKER)