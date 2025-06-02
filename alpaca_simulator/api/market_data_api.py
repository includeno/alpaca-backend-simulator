from fastapi import FastAPI, Query, HTTPException
import uvicorn
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from alpaca_simulator.domain.market_data.models import QuoteData, BarData, BarsResponse
from alpaca_simulator.domain.market_data.service import generate_latest_quotes, generate_historical_bars
from alpaca_simulator.common.config import MARKET_DATA_SIMULATOR_URL

app = FastAPI()

@app.get("/v2/stocks/quotes/latest", response_model=Dict[str, QuoteData])
async def get_latest_quotes_for_symbols(
    symbols: str = Query(..., description="A comma-separated list of stock symbols, e.g., AAPL,MSFT")
):
    requested_symbols = [s.strip().upper() for s in symbols.split(',')]
    # Call service function
    quotes_data_models = generate_latest_quotes(requested_symbols)
    # Convert model instances to dicts for response, handling potential alias usage
    response_output = {
        symbol: quote.model_dump(by_alias=True) if hasattr(quote, 'model_dump') else quote.dict(by_alias=True)
        for symbol, quote in quotes_data_models.items()
    }
    return response_output

@app.get("/v2/stocks/{symbol}/bars", response_model=BarsResponse)
async def get_historical_bars(
    symbol: str,
    start_date: Optional[str] = Query(None, alias="start"), # Use alias for query params if needed
    end_date: Optional[str] = Query(None, alias="end"),
    timeframe: Optional[str] = Query(None) # Alpaca uses "timeframe", not StockTimeFrame for query
):
    # Call service function
    bars_response_model = generate_historical_bars(symbol, start_date, end_date, timeframe)
    # FastAPI will automatically convert Pydantic model to JSON
    return bars_response_model

if __name__ == "__main__":
    parsed_url = urlparse(MARKET_DATA_SIMULATOR_URL)
    host = parsed_url.hostname if parsed_url.hostname else "localhost"
    port = parsed_url.port if parsed_url.port else 8001
    uvicorn.run(app, host=host, port=port)
