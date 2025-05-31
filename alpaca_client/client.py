import requests
import os # Added os import
from typing import Optional, List
# Removed direct import of API_KEY, SECRET_KEY, ALPACA_API_BASE_URL for default __init__ values
# They will be fetched via os.getenv() within __init__ to ensure test environment overrides are respected.

class AlpacaClient:
    def __init__(self, api_key: str = None, secret_key: str = None, base_url: str = None):
        # Fetch from environment if parameters are not provided, allowing pytest fixtures to set env vars first.
        self.api_key = api_key if api_key is not None else os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key if secret_key is not None else os.getenv("ALPACA_SECRET_KEY")

        # Determine default base URL:
        # 1. Use provided base_url if any
        # 2. Else, use ALPACA_API_BASE_URL from env
        # 3. Else, use the hardcoded default "https://paper-api.alpaca.markets"
        if base_url is not None:
            self.base_url = base_url
        else:
            self.base_url = os.getenv("ALPACA_API_BASE_URL", "https://paper-api.alpaca.markets")

        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json"
        })

    def get_account_info(self):
        response = self.session.get(f"{self.base_url}/v2/account")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()

    def list_positions(self):
        response = self.session.get(f"{self.base_url}/v2/positions")
        response.raise_for_status()
        return response.json()

    def place_order(self, symbol: str, qty: int, side: str, type: str, time_in_force: str):
        payload = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": type,
            "time_in_force": time_in_force
        }
        response = self.session.post(f"{self.base_url}/v2/orders", json=payload)
        response.raise_for_status()
        return response.json()

    def get_latest_quote(self, symbol: str):
        response = self.session.get(f"{self.base_url}/v2/stocks/{symbol}/quotes/latest")
        response.raise_for_status()
        return response.json()

    def get_bars(self, symbol: str, timeframe: str, start: str = None, end: str = None, limit: int = None):
        params = {"timeframe": timeframe}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if limit:
            params["limit"] = limit

        response = self.session.get(f"{self.base_url}/v2/stocks/{symbol}/bars", params=params)
        response.raise_for_status()
        return response.json()

    def get_order(self, order_id: str) -> dict:
        """Retrieves a single order by its ID."""
        endpoint = f"{self.base_url}/v2/orders/{order_id}"
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Add more specific error handling or logging if desired
            print(f"Error fetching order {order_id}: {e}")
            raise

    def list_orders(
        self,
        status: Optional[str] = None, # e.g., 'open', 'closed', 'all'
        limit: Optional[int] = None,
        after: Optional[str] = None, # datetime string
        until: Optional[str] = None, # datetime string
        direction: Optional[str] = None, # 'asc' or 'desc'
        nested: Optional[bool] = None, # If true, nesting is supported otherwise the most recent order for each symbol is returned.
        symbols: Optional[str] = None # A comma-separated list of symbols to filter by
    ) -> List[dict]:
        """Retrieves a list of orders based on parameters."""
        endpoint = f"{self.base_url}/v2/orders"
        params = {}
        if status:
            params["status"] = status
        if limit:
            params["limit"] = limit
        if after:
            params["after"] = after
        if until:
            params["until"] = until
        if direction:
            params["direction"] = direction
        if nested is not None: # nested can be False, so check for None
            params["nested"] = nested
        if symbols:
            params["symbols"] = symbols

        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing orders: {e}")
            raise
