from fastapi import FastAPI, Query, HTTPException
import uvicorn
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timezone
import random

from config.settings import MARKET_DATA_SIMULATOR_URL

app = FastAPI()

class QuoteData(BaseModel):
    ask_price: float = Field(alias="ap")
    ask_size: int = Field(alias="as")
    ask_exchange: str = Field(alias="ax")
    bid_price: float = Field(alias="bp")
    bid_size: int = Field(alias="bs")
    bid_exchange: str = Field(alias="bx")
    conditions: Optional[List[str]] = Field(default=None, alias="c")
    timestamp: str = Field(alias="t")
    tape: Optional[str] = Field(default=None, alias="z")

    # For Pydantic V2 (preferred if version is >= 2.0)
    model_config = {
        "populate_by_name": True  # Allows initialization with field names even if aliases are used elsewhere
    }
    # For Pydantic V1 (if version is < 2.0)
    # class Config:
    #     allow_population_by_name = True # Pydantic V1 equivalent


@app.get("/v2/stocks/quotes/latest", response_model=Dict[str, QuoteData])
async def get_latest_quotes_for_symbols(
    symbols: str = Query(..., description="A comma-separated list of stock symbols, e.g., AAPL,MSFT")
):
    requested_symbols = [s.strip().upper() for s in symbols.split(',')]
    response_data: Dict[str, Any] = {} # Store raw dicts first

    for sym_ticker in requested_symbols:
        now_utc = datetime.now(timezone.utc)

        # Generate local variables for quote data
        local_bid_price = round(random.uniform(50, 500), 2)
        local_ask_price = round(local_bid_price + random.uniform(0.01, 0.20), 2)
        local_ask_size_val = random.randint(1, 10) * 100
        local_ask_exchange_val = "MOCK_EX_ASK"
        local_bid_size_val = random.randint(1, 10) * 100
        local_bid_exchange_val = "MOCK_EX_BID"
        local_conditions_val = ["R"] if random.choice([True, False]) else None
        local_timestamp_val = now_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        local_tape_val = random.choice(["A", "B", "C"]) if random.choice([True, False]) else None

        # Create a dictionary using descriptive Python field names
        quote_data_dict_for_fastapi = {
            "ask_price": local_ask_price,
            "ask_size": local_ask_size_val,
            "ask_exchange": local_ask_exchange_val,
            "bid_price": local_bid_price,
            "bid_size": local_bid_size_val,
            "bid_exchange": local_bid_exchange_val,
            "conditions": local_conditions_val,
            "timestamp": local_timestamp_val,
            "tape": local_tape_val
        }
        # FastAPI will take this dict, parse it into QuoteData (using field names due to populate_by_name),
        # and then serialize the QuoteData instance to JSON (using aliases).
        response_data[sym_ticker] = quote_data_dict_for_fastapi

    if not response_data:
        pass

    return response_data


@app.get("/v2/stocks/{symbol}/bars")
async def get_historical_bars(symbol: str, start_date: str = None, end_date: str = None, timeframe: str = None):
    now_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds') + "Z"
    return {
        "symbol": symbol,
        "bars": [
            {
                "o": round(random.uniform(90,110),2),
                "h": round(random.uniform(110,120),2),
                "l": round(random.uniform(80,90),2),
                "c": round(random.uniform(90,110),2),
                "v": random.randint(10000, 50000),
                "t": now_iso,
                "n": random.randint(100,1000),
                "vw": round(random.uniform(90,110),2)
            }
        ],
        "next_page_token": None,
    }

if __name__ == "__main__":
    parsed_url = urlparse(MARKET_DATA_SIMULATOR_URL)
    host = parsed_url.hostname if parsed_url.hostname else "localhost"
    port = parsed_url.port if parsed_url.port else 8001
    uvicorn.run(app, host=host, port=port)
