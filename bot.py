import requests
from datetime import datetime
import os
import json
import time
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import pandas as pd

# Load variables from .env
load_dotenv()

# ----- CONFIG -----
LINE_TOKEN = os.getenv("LINE_TOKEN")
API_KEY = os.getenv("API_KEY")
ANALYSIS_API = os.getenv("ANALYSIS_API")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SHEET_NAME = os.getenv("TICKER_SHEET_NAME")

# ----- FUNCTION: ส่ง LINE -----
def send_line(msg):
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}

    payload = {
        "messages": [
            {
                "type": "text",
                "text": msg
            }
        ]
    }

    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res.raise_for_status()
    print(f"LINE push status: {res.status_code}, response: {res.text}")
    
# ----- FUNCTION: Fetch analysis from API -----
def get_analysis(ticker):
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {"ticker": ticker, "period": "90d"}
    for attempt in range(3):
        try:
            res = requests.post(ANALYSIS_API, json=payload, headers=headers)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s
            else:
                return {"error": str(e)}


# ----- FUNCTION: Write daily recommendations to history sheet -----
def write_history(records):
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
    if not creds_file:
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(creds)
        ws = client.open_by_key(SHEET_ID).worksheet(os.getenv("HISTORY_SHEET_NAME", "history"))
        for row in records:
            ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"History written: {len(records)} row(s)")
    except Exception as e:
        print(f"Sheet write-back failed: {e}")
    
    
# ----- FUNCTION: Build daily summary -----
def daily_summary():
    # Bangkok timezone
    tz_bkk = ZoneInfo("Asia/Bangkok")
    now_bkk = datetime.now(tz=tz_bkk)

    # # Skip weekends — US markets are closed Sat/Sun
    # if now_bkk.weekday() >= 5:
    #     print(f"[{now_bkk}] Weekend — skipping.")
    #     return

    # Fetch ticker list from Google Sheets
    try:
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
        df = pd.read_csv(csv_url)
        TICKER = df.iloc[:, 0].dropna().tolist()
    except Exception as e:
        send_line(f"❌ Failed to load ticker list: {e}")
        return

    today = now_bkk.strftime("%Y-%m-%d")
    datetime_str = now_bkk.strftime("%Y-%m-%d %H:%M:%S")
    summary_lines = [f"📈 Daily Summary ({today})"]
    log_lines = [f"📈 Daily Summary ({now_bkk})"]
    urgent_lines = []
    history_records = []
    for t in TICKER:
        result = get_analysis(t)
        if "error" in result:
            summary_lines.append(f"❌ {t}: Error - {result['error']}")
        else:
            reco           = result.get("recommendation", "HOLD")
            strength       = result.get("strength", "")
            confidence     = result.get("confidence", 0)
            trend_strength = result.get("trend_strength", "")
            latest         = result.get("latest_data", {})

            raw_price = latest.get(f"Close_{t}")
            price_str = f"${float(raw_price):.2f}" if raw_price is not None else "-"

            emoji_map  = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
            reco_emoji = emoji_map.get(reco.upper(), "⚪")

            line = (
                f"{reco_emoji} {t} | 💰 {price_str}\n"
                f"   ➤ {reco} ({strength}, {confidence}%) | {trend_strength}"
            )
            summary_lines.append(line)
            log_lines.append(f"{t}: {reco} ({strength}, {confidence}%) | {trend_strength} | Price {price_str}")
            history_records.append([datetime_str, t, reco, strength, confidence, trend_strength, price_str])

            if reco.upper() in ("BUY", "SELL") and confidence >= 70:
                urgent_lines.append(line)

    message = "\n".join(summary_lines)
    print(log_lines)
    send_line(message)

    if urgent_lines:
        send_line("⚡ Action Signals:\n" + "\n".join(urgent_lines))
        print(f"[{datetime.now(tz=tz_bkk)}] Urgent alert sent ({len(urgent_lines)} signal(s))")

    write_history(history_records)
    print(f"[{datetime.now(tz=tz_bkk)}] Summary sent to LINE")


if __name__ == "__main__":
    daily_summary()