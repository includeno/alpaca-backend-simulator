from pydantic import BaseModel
from typing import Optional

class OrderRequest(BaseModel):
    symbol: str
    qty: float # Alpaca API uses float for qty
    side: str # 'buy' or 'sell'
    type: str # 'market', 'limit', etc.
    time_in_force: str # 'day', 'gtc', etc.
    limit_price: Optional[float] = None # Changed to float
    stop_price: Optional[float] = None  # Changed to float
    client_order_id: Optional[str] = None # Optional
