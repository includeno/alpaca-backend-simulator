import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from alpaca_simulator.domain.trading.models import OrderRequest # Will be used by order functions

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

mock_orders_data: Dict[str, Dict[str, Any]] = {}

# --- Account Data Access ---
def get_account_data() -> Dict[str, Any]:
    # In a real repo, this might fetch from DB or cache
    return mock_account_data

def update_account_data(updated_data: Dict[str, Any]):
    mock_account_data.update(updated_data)
    # In a real repo, this would persist the changes

# --- Positions Data Access ---
def get_all_positions() -> List[Dict[str, Any]]:
    return mock_positions_data

def add_position(position: Dict[str, Any]):
    mock_positions_data.append(position)

def update_position(symbol: str, updated_values: Dict[str, Any]):
    for pos in mock_positions_data:
        if pos['symbol'] == symbol:
            pos.update(updated_values)
            return
    # Handle case where position to update is not found if necessary

def remove_position(symbol: str):
    global mock_positions_data
    mock_positions_data = [p for p in mock_positions_data if p['symbol'] != symbol]

# --- Orders Data Access ---
def get_all_orders() -> List[Dict[str, Any]]:
    return list(mock_orders_data.values())

def get_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    return mock_orders_data.get(order_id)

def get_order_by_client_order_id(client_order_id: str) -> Optional[Dict[str, Any]]:
    for order in mock_orders_data.values():
        if order.get('client_order_id') == client_order_id:
            return order
    return None

def save_order(order_data: Dict[str, Any]):
    mock_orders_data[order_data['id']] = order_data
