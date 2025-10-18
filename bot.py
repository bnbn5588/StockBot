import requests
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

# Load variables from .env
load_dotenv()

# ----- CONFIG -----
# TICKER = ["AAPL", "ORCL", "AMZN", "CRM", "MSFT", "GOOGL", "META", "TSLA", "NVDA", "AMD", "CONY"]
TICKER = ["AAPL", "ORCL", "AMZN", "MSFT", "GOOGL", "NVDA", "AMD"]
LINE_TOKEN = os.getenv("LINE_TOKEN")
API_KEY = os.getenv("API_KEY")
ANALYSIS_API = os.getenv("ANALYSIS_API")

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
    print(f"LINE push status: {res.status_code}, response: {res.text}")
    
# ----- FUNCTION: Fetch analysis from API -----
def get_analysis(ticker):
    try:
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        payload = {"ticker": ticker, "period": "90d"}
        res = requests.post(ANALYSIS_API, json=payload, headers=headers)
        res.raise_for_status()      
        return res.json()
    except Exception as e:
        return {"error": str(e)}
    
    
# ----- FUNCTION: Build daily summary -----
def daily_summary():
    # Bangkok timezone
    tz_bkk = ZoneInfo("Asia/Bangkok")
    now_bkk = datetime.now(tz=tz_bkk)

    summary_lines = [f"📈 Daily Summary ({now_bkk.strftime('%Y-%m-%d')})"]
    log_lines = [f"📈 Daily Summary ({now_bkk})"]
    for t in TICKER:
        result = get_analysis(t)
        if "error" in result:
            summary_lines.append(f"❌ {t}: Error - {result['error']}")
        else:
            # Extract top-level info
            reco = result.get("recommendation", "unknown")
            #details = result.get("details", {})
            latest = result.get("latest_data", {})
            
            price = latest.get(f"Close_{t}", "-")
            emoji_map = {"BUY": "🟢", "SELL": "🔴", "Neutral": "🟡"}
            reco_emoji = emoji_map.get(reco.upper(), "⚪")
            
            summary_lines.append(
                f"{reco_emoji} {t} | "
                f"💰 Price: ${price:.2f}"
            )
            log_lines.append(f"{t}: Recommendation - {reco}, Price - ${price:.2f}")

    message = "\n".join(summary_lines)
    print(log_lines)
    send_line(message)
    print(f"[{datetime.now(tz=tz_bkk)}] Summary sent to LINE")
    

daily_summary()