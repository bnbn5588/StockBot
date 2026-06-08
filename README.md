# Stock Analysis LINE Bot

A Python bot that sends daily stock analysis summaries via LINE messaging. Ticker list is managed from Google Sheets, runs as a Docker container triggered by cron.

## Features

- Daily automated stock analysis (weekdays only — skips weekends)
- Ticker list driven by Google Sheets — no code change needed to add/remove stocks
- Sends full daily summary via LINE broadcast
- Separate urgent alert for BUY/SELL signals with confidence ≥ 70%
- Retry with exponential backoff on API failures (3 attempts)
- Writes daily recommendations to a Google Sheets history tab
- Color-coded recommendations (🟢 BUY, 🔴 SELL, 🟡 HOLD)
- Runs as non-root user inside Docker

## Prerequisites

- Python 3.11+
- Docker
- LINE Messaging API token
- Stock analysis API key
- Google Sheet with a ticker list tab (public read access)
- Google Cloud service account with Sheets + Drive API enabled (for history write-back)

## Configuration

Create a `.env` file in the project root:

```
LINE_TOKEN=your_line_token
API_KEY=your_api_key
ANALYSIS_API=https://your_analysis_api_endpoint
GOOGLE_SHEET_ID=your_google_sheet_id
TICKER_SHEET_NAME=tickers

# Optional: enable history write-back
GOOGLE_CREDENTIALS_FILE=/app/credentials.json
HISTORY_SHEET_NAME=history
```

### Google Sheets setup

**Ticker sheet** — first column should contain ticker symbols, one per row. Must be publicly readable (no auth needed).

**History sheet** (optional) — add a tab named `history` (or whatever `HISTORY_SHEET_NAME` is set to) and share the sheet with your service account email. The bot will write the header row automatically on first run.

Columns written: `Date | Ticker | Recommendation | Strength | Confidence | Trend Strength | Price`

### Service account credentials (for history write-back)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → Enable **Google Sheets API** and **Google Drive API**
2. Create a service account → download the JSON key as `credentials.json`
3. Share your Google Sheet with the service account email (Editor role)
4. Place `credentials.json` on the server and set `GOOGLE_CREDENTIALS_FILE` in `.env`

## Deployment

### Build the Docker image

```bash
docker build -t stockbot:latest .
```

### Run manually

```bash
docker run --rm \
  --env-file /path/to/.env \
  -v /path/to/credentials.json:/app/credentials.json \
  stockbot:latest
```

### Cron (recommended)

Add to crontab (`crontab -e`):

```
0 1 * * * docker run --rm --env-file /home/opc/Bot/StockBot/.env -v /home/opc/Bot/StockBot/credentials.json:/app/credentials.json stockbot:latest >> /home/opc/Bot/StockBot/log/stockbot.log 2>&1
```

Runs at 01:00 UTC (08:00 Bangkok time) daily. The bot automatically skips Saturday and Sunday.

## Output format

**Daily summary (sent every weekday):**
```
📈 Daily Summary (2024-01-15)
🟢 AAPL | 💰 $150.00
   ➤ BUY (STRONG, 85%) | STRONG_UP
🟡 MSFT | 💰 $380.00
   ➤ HOLD (WEAK, 42%) | FLAT
```

**Urgent alert (sent only when BUY/SELL confidence ≥ 70%):**
```
⚡ Action Signals:
🟢 NVDA | 💰 $875.00
   ➤ BUY (STRONG, 91%) | STRONG_UP
```

## Dependencies

- `requests`
- `python-dotenv`
- `pandas`
- `gspread`
- `google-auth`
