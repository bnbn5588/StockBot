import os
import re
import ast
import sys
import gzip
from dotenv import load_dotenv

load_dotenv()

SHEET_ID      = os.getenv("GOOGLE_SHEET_ID")
CREDS_FILE    = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
HISTORY_SHEET = os.getenv("HISTORY_SHEET_NAME", "history")
LOG_FILE      = sys.argv[1] if len(sys.argv) > 1 else "stockbot.log.gz"

HEADER = ["Date", "Ticker", "Recommendation", "Strength", "Confidence", "Trend Strength", "Price"]

# New format: "AAPL: BUY (Weak, 47.4%) | Strong (ADX: 63.09) | Price $308.33"
TICKER_RE_NEW = re.compile(
    r"^([\w.]+): (\w+) \(([^,]*), ([\d.]+)%\) \| (.*?) \| Price (.+)$"
)
# Old format: "AAPL: Recommendation - BUY, Price - $252.29"
TICKER_RE_OLD = re.compile(
    r"^([\w.]+): Recommendation - (\w+), Price - (.+)$"
)


def open_log(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def parse_log(path):
    records = []
    with open_log(path) as f:
        for raw in f:
            line = raw.strip()
            if "'📈 Daily Summary" not in line:
                continue
            try:
                parts = ast.literal_eval(line)
            except Exception:
                continue
            # Header element: "📈 Daily Summary (2024-01-15 08:01:23.456789+07:00)"
            date_match = re.search(r"\((\d{4}-\d{2}-\d{2})", parts[0])
            if not date_match:
                continue
            date = date_match.group(1)
            for item in parts[1:]:
                m = TICKER_RE_NEW.match(item)
                if m:
                    ticker, reco, strength, confidence, trend, price = m.groups()
                    records.append([date, ticker, reco, strength, float(confidence), trend.strip(), price])
                    continue
                m = TICKER_RE_OLD.match(item)
                if m:
                    ticker, reco, price = m.groups()
                    records.append([date, ticker, reco, "", 0, "", price])
    return records


def upload(records):
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    ws = client.open_by_key(SHEET_ID).worksheet(HISTORY_SHEET)

    existing = ws.get_all_values()

    if not existing:
        ws.append_row(HEADER, value_input_option="USER_ENTERED")
        existing_keys = set()
    else:
        existing_keys = {(r[0], r[1]) for r in existing[1:] if len(r) >= 2}

    new_records = [r for r in records if (r[0], r[1]) not in existing_keys]

    if new_records:
        ws.append_rows(new_records, value_input_option="USER_ENTERED")

    print(f"Uploaded {len(new_records)} new row(s) — {len(records) - len(new_records)} duplicate(s) skipped")


if __name__ == "__main__":
    if not os.path.exists(CREDS_FILE):
        print(f"credentials file not found: {CREDS_FILE}")
        sys.exit(1)

    print(f"Parsing: {LOG_FILE}")
    records = parse_log(LOG_FILE)
    print(f"Parsed {len(records)} record(s)")

    if records:
        upload(records)
    else:
        print("Nothing to upload")
