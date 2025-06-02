from fastapi import FastAPI, Query, HTTPException
import uvicorn
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timezone
import random

from config.settings import MARKET_DATA_SIMULATOR_URL

app = FastAPI()

# --- Quote Data Models and Endpoint ---
class QuoteData(BaseModel):
    ask_price: float = Field()
    ask_size: float = Field() # Changed to float
    ask_exchange: Optional[str] = Field(default=None) # Changed to Optional[str]
    bid_price: float = Field()
    bid_size: float = Field() # Changed to float
    bid_exchange: Optional[str] = Field(default=None) # Changed to Optional[str]
    conditions: Optional[List[str]] = Field(default=None)
    timestamp: str = Field()
    tape: Optional[str] = Field(default=None)

    model_config = {
        "populate_by_name": True
    }

@app.get("/v2/stocks/quotes/latest", response_model=Dict[str, QuoteData])
async def get_latest_quotes_for_symbols(
    symbols: str = Query(..., description="A comma-separated list of stock symbols, e.g., AAPL,MSFT")
):
    requested_symbols = [s.strip().upper() for s in symbols.split(',')]
    response_data: Dict[str, Any] = {}

    for sym_ticker in requested_symbols:
        now_utc = datetime.now(timezone.utc)

        local_bid_price = round(random.uniform(100, 200), 2)
        local_ask_price = round(local_bid_price + random.uniform(0.01, 0.1), 2)
        local_ask_size_val = float(random.randint(1, 10) * 100)
        local_bid_size_val = float(random.randint(1, 10) * 100)
        possible_exchanges = ["NASDAQ", "NYSE", "ARCA", None]
        local_ask_exchange_val = random.choice(possible_exchanges)
        local_bid_exchange_val = random.choice(possible_exchanges)
        local_conditions_val = random.choice([["R"], ["O", "R"], None])
        local_timestamp_val = now_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        local_tape_val = random.choice(["A", "B", "C", None])

        quote_instance = QuoteData(
            ask_price=local_ask_price,
            ask_size=local_ask_size_val,
            ask_exchange=local_ask_exchange_val,
            bid_price=local_bid_price,
            bid_size=local_bid_size_val,
            bid_exchange=local_bid_exchange_val,
            conditions=local_conditions_val,
            timestamp=local_timestamp_val,
            tape=local_tape_val
        )
        try:
            aliased_quote_dict = quote_instance.model_dump(by_alias=True)
        except AttributeError:
            aliased_quote_dict = quote_instance.dict(by_alias=True)
        response_data[sym_ticker] = aliased_quote_dict

    return response_data

# --- Bar Data Models and Endpoint ---
class BarData(BaseModel):
    close_price: float = Field(alias="c")
    high_price: float = Field(alias="h")
    low_price: float = Field(alias="l")
    trade_count: Optional[float] = Field(default=None, alias="n") # Changed from Optional[int]
    open_price: float = Field(alias="o")
    timestamp: str = Field(alias="t") # Expects ISO 8601 string
    volume: float = Field(alias="v") # Changed from int
    vwap: Optional[float] = Field(default=None, alias="vw")

    model_config = {
        "populate_by_name": True
    }

class BarsResponse(BaseModel):
    bars: List[BarData]
    symbol: str
    next_page_token: Optional[str] = None


@app.get("/v2/stocks/{symbol}/bars", response_model=BarsResponse)
async def get_historical_bars(
    symbol: str,
    start_date: Optional[str] = Query(None, alias="start"), # Use alias for query params if needed
    end_date: Optional[str] = Query(None, alias="end"),
    timeframe: Optional[str] = Query(None) # Alpaca uses "timeframe", not StockTimeFrame for query
):
    bars_data: List[BarData] = []
    # Simulate generating a few bars. In a real scenario, this would depend on start/end/timeframe.
    num_bars = random.randint(1, 5)

    for i in range(num_bars):
        # Generate prices ensuring h >= o, h >= c, l <= o, l <= c
        open_price = round(random.uniform(90,110),2)
        close_price = round(random.uniform(90,110),2)
        high_price = round(max(open_price, close_price, random.uniform(open_price, open_price + 10)), 2)
        low_price = round(min(open_price, close_price, random.uniform(open_price - 10, open_price)), 2)

        # Ensure low is not greater than high (can happen with random generation)
        if low_price > high_price:
            low_price = high_price - random.uniform(0.1, 2.0) if high_price > 2.0 else high_price

        bar_ts_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds') + "Z" # Mock timestamp

        local_volume = float(random.randint(5000, 50000))
        local_trade_count = float(random.randint(50, 500)) if random.choice([True, False]) else None
        local_vwap = round(random.uniform(low_price, high_price), 2) if random.choice([True, False]) else None

        bar_instance = BarData(
            close_price=close_price,
            high_price=high_price,
            low_price=low_price,
            trade_count=local_trade_count,
            open_price=open_price,
            timestamp=bar_ts_iso,
            volume=local_volume,
            vwap=local_vwap
        )
        bars_data.append(bar_instance)

    return BarsResponse(
        bars=bars_data,
        symbol=symbol.upper(),
        next_page_token=None # Can be a string if pagination is implemented
    )

if __name__ == "__main__":
    parsed_url = urlparse(MARKET_DATA_SIMULATOR_URL)
    host = parsed_url.hostname if parsed_url.hostname else "localhost"
    port = parsed_url.port if parsed_url.port else 8001
    uvicorn.run(app, host=host, port=port)
