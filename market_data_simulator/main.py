from fastapi import FastAPI, Query, HTTPException
import uvicorn
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timezone # Ensure timezone is imported
import random # For random data generation

from config.settings import MARKET_DATA_SIMULATOR_URL

app = FastAPI()

# Pydantic model for Quote Data (aligns with alpaca.data.models.Quote)
class QuoteData(BaseModel):
    ask_price: float = Field(..., alias="ap", example=150.05)
    ask_size: int = Field(..., alias="as", example=100)
    ask_exchange: str = Field(..., alias="ax", example="NASDAQ")
    bid_price: float = Field(..., alias="bp", example=150.00)
    bid_size: int = Field(..., alias="bs", example=50)
    bid_exchange: Optional[str] = Field(None, alias="bx", example="NYSE") # Made optional as not always present
    conditions: Optional[List[str]] = Field(None, alias="c", example=["R"]) # Optional
    timestamp: datetime = Field(..., alias="t") # Will be converted to ISO string by FastAPI
    tape: Optional[str] = Field(None, alias="z", example="C") # Optional, often 'C' for CTA

    class Config:
        allow_population_by_field_name = True # Allows using alias names for population


# No longer using LatestQuoteResponse as the endpoint returns Dict[str, QuoteData] directly
# class LatestQuoteResponse(BaseModel):
#    symbol: str
#    quote: QuoteData


@app.get("/v2/stocks/quotes/latest", response_model=Dict[str, QuoteData])
async def get_latest_quotes_for_symbols(
    symbols: str = Query(..., description="A comma-separated list of stock symbols, e.g., AAPL,MSFT")
):
    requested_symbols = [s.strip().upper() for s in symbols.split(',')]
    response_data: Dict[str, QuoteData] = {}

    for sym_ticker in requested_symbols:
        # For this mock, generate data for any requested symbol
        # In a more advanced mock, you might have a predefined list or more complex logic
        now_utc = datetime.now(timezone.utc) # Use timezone aware datetime

        bid_price = round(random.uniform(50, 500), 2)
        ask_price = round(bid_price + random.uniform(0.01, 0.20), 2) # Ensure ask is higher

        quote_details = QuoteData(
            ap=ask_price,
            as_=random.randint(1, 10) * 100, # ask_size
            ax="MOCK_EX", # ask_exchange
            bp=bid_price,
            bs=random.randint(1, 10) * 100, # bid_size
            bx="MOCK_EX", # bid_exchange
            c=["R"], # conditions, "R" is regular
            t=now_utc, # timestamp
            z="A" # tape, example, could be "C" for CTA etc.
        )
        response_data[sym_ticker] = quote_details

    if not response_data:
        # If symbols list was empty or only contained whitespace.
        # alpaca-py typically expects a dict, even if empty, if the request was valid.
        # If symbols parameter itself is invalid (e.g. not provided if mandatory), FastAPI handles it.
        pass # Return empty dict {}

    return response_data


# Bars endpoint remains largely the same for now
@app.get("/v2/stocks/{symbol}/bars")
async def get_historical_bars(symbol: str, start_date: str = None, end_date: str = None, timeframe: str = None):
    # Fixed sample bar data
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
                "n": random.randint(100,1000), # trade_count
                "vw": round(random.uniform(90,110),2) # vwap
            }
            # Add more bars if needed for robust testing
        ],
        "next_page_token": None, # Alpaca API might return this
        # start_date, end_date, timeframe are implicitly part of the request and reflected in data;
        # not usually part of the response body unless echoing parameters.
    }

if __name__ == "__main__":
    parsed_url = urlparse(MARKET_DATA_SIMULATOR_URL)
    host = parsed_url.hostname if parsed_url.hostname else "localhost"
    port = parsed_url.port if parsed_url.port else 8001
    uvicorn.run(app, host=host, port=port)
