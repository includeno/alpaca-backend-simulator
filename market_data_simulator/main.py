from fastapi import FastAPI
import uvicorn
from config.settings import MARKET_DATA_SIMULATOR_URL
from urllib.parse import urlparse
import datetime

app = FastAPI()

@app.get("/v2/stocks/{symbol}/quotes/latest")
async def get_latest_quote(symbol: str):
    # Fixed sample data for a quote
    return {
        "symbol": symbol,
        "quote": {
            "bp": 150.00,  # Bid price
            "ap": 150.05,  # Ask price
            "t": datetime.datetime.utcnow().isoformat() + "Z" # Timestamp
        }
    }

@app.get("/v2/stocks/{symbol}/bars")
async def get_historical_bars(symbol: str, start_date: str = None, end_date: str = None, timeframe: str = None):
    # Fixed sample bar data
    return {
        "symbol": symbol,
        "bars": [
            {
                "o": 100.00, # Open
                "h": 102.50, # High
                "l": 99.50,  # Low
                "c": 101.00, # Close
                "v": 10000,  # Volume
                "t": "2023-10-26T10:00:00Z" # Timestamp
            },
            {
                "o": 101.00,
                "h": 103.00,
                "l": 100.50,
                "c": 102.00,
                "v": 12000,
                "t": "2023-10-27T10:00:00Z"
            }
        ],
        "start_date": start_date,
        "end_date": end_date,
        "timeframe": timeframe
    }

if __name__ == "__main__":
    parsed_url = urlparse(MARKET_DATA_SIMULATOR_URL)
    host = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 8001
    uvicorn.run(app, host=host, port=port)
