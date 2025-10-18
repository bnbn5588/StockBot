# Stock Analysis LINE Bot

A Python bot that sends daily stock analysis summaries via LINE messaging platform. The bot analyzes multiple tech stocks and provides recommendations with current prices.

## Features

- Daily automated stock analysis at 9:00 AM
- Supports multiple stock tickers (AAPL, ORCL, AMZN, MSFT, GOOGL, NVDA, AMD)
- Sends analysis results through LINE messaging platform
- Docker support for easy deployment
- Color-coded recommendations (🟢 Buy, 🔴 Sell, 🟡 Neutral)

## Prerequisites

- Python 3.11+
- LINE Messaging API token
- Stock analysis API key

## Installation

1. Clone the repository
2. Install dependencies:

```sh
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory with the following variables:

```
LINE_TOKEN=your_line_token
API_KEY=your_api_key
ANALYSIS_API=your_analysis_api_endpoint
```

## Usage

### Running Locally

```sh
python bot.py
```

### Running with Docker

1. Build the Docker image:

```sh
docker build -t stock-analysis-bot .
```

2. Run the container:

```sh
docker run -d stock-analysis-bot
```

## Output Format

The bot sends daily summaries in the following format:

```
📈 Daily Summary (YYYY-MM-DD)
🟢 AAPL | 💰 Price: $150.00
🔴 ORCL | 💰 Price: $90.50
...
```

## Dependencies

- requests
- schedule
- python-dotenv
