from fastapi import FastAPI, HTTPException, status as http_status # Renamed status to avoid conflict
import uvicorn
from config.settings import MOCK_API_BASE_URL
from pydantic import BaseModel
from urllib.parse import urlparse
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# In-memory data stores
mock_account_data: Dict[str, Any] = {
    "id": str(uuid.uuid4()),
    "account_number": "PA_MOCK_001",
    "status": "ACTIVE",
    "currency": "USD",
    "buying_power": "100000.00", # Initial buying power
    "cash": "100000.00", # Initial cash
    "portfolio_value": "100000.00",
    "equity": "100000.00",
    "last_equity": "100000.00",
    "long_market_value": "0.00",
    "short_market_value": "0.00",
    "initial_margin": "0.00",
    "maintenance_margin": "0.00",
    "daytrade_count": 0,
    "daytrading_buying_power": "0.00",
    "regt_buying_power": "100000.00", # Should be same as buying_power for cash account
    "non_marginable_buying_power": "100000.00", # Cash available to purchase non-marginable assets
    "sma": "0", # Special Memorandum Account, relevant for margin accounts
    "created_at": "2023-01-01T00:00:00.000000Z"
}
mock_positions_data: List[Dict[str, Any]] = []
mock_orders_data: Dict[str, Dict[str, Any]] = {} # Store orders by order_id


app = FastAPI()

# Pydantic model for order request body
class OrderRequest(BaseModel):
    symbol: str
    qty: float # Alpaca API uses float for qty
    side: str # 'buy' or 'sell'
    type: str # 'market', 'limit', etc.
    time_in_force: str # 'day', 'gtc', etc.
    limit_price: Optional[float] = None # Changed to float
    stop_price: Optional[float] = None  # Changed to float
    client_order_id: Optional[str] = None # Optional

@app.get("/v2/account")
async def get_account_info():
    # Update portfolio value based on current positions
    current_portfolio_value = float(mock_account_data["cash"])
    for pos in mock_positions_data:
        current_portfolio_value += float(pos.get("market_value", "0.00"))
    mock_account_data["portfolio_value"] = str(current_portfolio_value)
    mock_account_data["equity"] = str(current_portfolio_value) # Simplified equity calculation
    return mock_account_data

@app.get("/v2/positions")
async def list_positions():
    # In a real scenario, you might want to update current_price and market_value here
    # based on a mock market data feed. For simplicity, we'll return them as stored.
    # Remove positions with qty 0
    live_positions = [p for p in mock_positions_data if float(p.get("qty", "0")) != 0]
    return live_positions

@app.post("/v2/orders", status_code=http_status.HTTP_200_OK)
async def place_order_endpoint(order_request: OrderRequest):
    order_id = str(uuid.uuid4())
    client_order_id = order_request.client_order_id or f"mock_client_{str(uuid.uuid4())[:12]}"
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    order_data = {
        "id": order_id,
        "client_order_id": client_order_id,
        "created_at": now_iso,
        "updated_at": now_iso,
        "submitted_at": now_iso,
        "filled_at": None,
        "expired_at": None,
        "canceled_at": None,
        "failed_at": None,
        "replaced_at": None,
        "replaced_by": None,
        "replaces": None,
        "asset_id": str(uuid.uuid4()), # Mock asset_id
        "symbol": order_request.symbol.upper(),
        "asset_class": "us_equity", # Assuming equity
        "notional": None,
        "qty": str(order_request.qty),
        "filled_qty": "0",
        "filled_avg_price": None,
        "order_class": "",
        "order_type": order_request.type,
        "type": order_request.type,
        "side": order_request.side,
        "time_in_force": order_request.time_in_force,
        "limit_price": str(order_request.limit_price) if order_request.limit_price is not None else None,
        "stop_price": str(order_request.stop_price) if order_request.stop_price is not None else None,
        "status": "accepted", # Initial status for non-market orders
        "extended_hours": False,
        "legs": None,
        "trail_percent": None,
        "trail_price": None,
        "hwm": None # High Water Mark for trail orders
    }

    if order_request.type == "market":
        order_data["status"] = "filled"
        order_data["filled_at"] = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        order_data["filled_qty"] = str(order_request.qty)

        # Simulate a fill price (e.g., a fixed price or slightly randomized from a mock market)
        # For now, use a very simple fixed price based on symbol
        mock_fill_price = 0.0
        if order_request.symbol.upper() == "AAPL": mock_fill_price = 150.0
        elif order_request.symbol.upper() == "MSFT": mock_fill_price = 300.0
        elif order_request.symbol.upper() == "TSLA": mock_fill_price = 250.0
        elif order_request.symbol.upper() == "GOOG": mock_fill_price = 140.0 # For tests
        else: mock_fill_price = 50.0 # Default for other symbols

        order_data["filled_avg_price"] = str(mock_fill_price)

        # Update positions
        found_position = False
        for pos_idx, pos in enumerate(mock_positions_data):
            if pos["symbol"] == order_request.symbol.upper():
                current_qty = float(pos["qty"])
                current_avg_entry = float(pos["avg_entry_price"])
                current_cost_basis = float(pos.get("cost_basis", str(current_qty * current_avg_entry)))

                order_value = order_request.qty * mock_fill_price

                if order_request.side == "buy":
                    new_qty = current_qty + order_request.qty
                    new_cost_basis = current_cost_basis + order_value
                    pos["avg_entry_price"] = str(new_cost_basis / new_qty if new_qty != 0 else 0)
                    pos["qty"] = str(new_qty)
                    pos["cost_basis"] = str(new_cost_basis)
                    pos["side"] = "long" # Can only be long in this simplified model
                else: # sell
                    new_qty = current_qty - order_request.qty
                    # Cost basis reduces proportionally on sell. Simplified: reduce by avg_entry_price * sell_qty
                    # A more accurate method would use tax lot accounting (FIFO, LIFO, etc.)
                    sold_cost_basis_reduction = order_request.qty * current_avg_entry
                    pos["cost_basis"] = str(current_cost_basis - sold_cost_basis_reduction)
                    pos["qty"] = str(new_qty)
                    if new_qty == 0:
                         pos["avg_entry_price"] = "0" # Reset if position is closed
                         # Optionally remove the position from mock_positions_data if qty is 0
                         # mock_positions_data.pop(pos_idx)
                         # For now, keep it but qty will be 0, list_positions will filter it.

                pos["market_value"] = str(float(pos["qty"]) * mock_fill_price)
                pos["current_price"] = str(mock_fill_price)
                # Simplified P/L: (current_price - avg_entry_price) * qty
                if float(pos["qty"]) != 0:
                    pos["unrealized_pl"] = str((mock_fill_price - float(pos["avg_entry_price"])) * float(pos["qty"]))
                else:
                    pos["unrealized_pl"] = "0.00"

                found_position = True
                break

        if not found_position and order_request.side == "buy":
            new_position_cost = order_request.qty * mock_fill_price
            mock_positions_data.append({
                "asset_id": str(uuid.uuid4()),
                "symbol": order_request.symbol.upper(),
                "exchange": "NASDAQ",
                "asset_class": "us_equity",
                "avg_entry_price": str(mock_fill_price),
                "qty": str(order_request.qty),
                "side": "long",
                "market_value": str(new_position_cost),
                "cost_basis": str(new_position_cost),
                "unrealized_pl": "0.00",
                "unrealized_plpc": "0.0000",
                "unrealized_intraday_pl": "0.00",
                "unrealized_intraday_plpc": "0.0000",
                "current_price": str(mock_fill_price),
                "lastday_price": str(mock_fill_price - 1.0),
                "change_today": "0.0000"
            })

        # Update cash
        current_cash = float(mock_account_data["cash"])
        order_total_value = order_request.qty * mock_fill_price
        if order_request.side == "buy":
            mock_account_data["cash"] = str(current_cash - order_total_value)
        else: # sell
            mock_account_data["cash"] = str(current_cash + order_total_value)

        # Update buying power (simplified, assumes cash account)
        mock_account_data["buying_power"] = mock_account_data["cash"]
        mock_account_data["regt_buying_power"] = mock_account_data["cash"]
        mock_account_data["non_marginable_buying_power"] = mock_account_data["cash"]

        # Update portfolio value and equity
        current_portfolio_value = float(mock_account_data["cash"])
        current_long_market_value = 0.0
        for pos in mock_positions_data:
            if float(pos.get("qty", "0")) > 0 : # only consider active positions
                 pos_market_val = float(pos.get("qty")) * float(pos.get("current_price", str(mock_fill_price)))
                 current_portfolio_value += pos_market_val
                 current_long_market_value += pos_market_val

        mock_account_data["portfolio_value"] = str(current_portfolio_value)
        mock_account_data["equity"] = str(current_portfolio_value) # Simplified equity
        mock_account_data["long_market_value"] = str(current_long_market_value)

    elif order_request.type == "limit": # For limit orders, just accept them for now.
        order_data["status"] = "new" # Or "pending_new" or "accepted" as per Alpaca docs for unfillable limits

    mock_orders_data[order_id] = order_data
    return order_data

@app.get("/v2/orders")
async def list_orders_endpoint(status: Optional[str] = None, limit: Optional[int] = None,
                               after: Optional[str] = None, until: Optional[str] = None,
                               direction: Optional[str] = "desc", nested: Optional[bool] = False,
                               symbols: Optional[str] = None):
    orders_to_return = list(mock_orders_data.values())

    if status and status != "all":
        statuses = status.split(',')
        orders_to_return = [o for o in orders_to_return if o["status"] in statuses]

    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        orders_to_return = [o for o in orders_to_return if o["symbol"] in symbol_list]

    # Filtering by date (simplified, assumes ISO format)
    if after:
        orders_to_return = [o for o in orders_to_return if o["submitted_at"] > after]
    if until:
        orders_to_return = [o for o in orders_to_return if o["submitted_at"] < until]

    # Sorting
    orders_to_return.sort(key=lambda x: x["submitted_at"], reverse=(direction == "desc"))

    if limit:
        orders_to_return = orders_to_return[:limit]

    return orders_to_return

@app.get("/v2/orders/{order_id}")
async def get_order_by_id(order_id: str):
    if order_id in mock_orders_data:
        return mock_orders_data[order_id]
    # Check if it's a client_order_id
    for order in mock_orders_data.values():
        if order["client_order_id"] == order_id:
            return order
    raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Order not found")

if __name__ == "__main__":
    parsed_url = urlparse(MOCK_API_BASE_URL)
    host = parsed_url.hostname if parsed_url.hostname else "localhost"
    port = parsed_url.port if parsed_url.port else 8000
    uvicorn.run(app, host=host, port=port)
