from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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
