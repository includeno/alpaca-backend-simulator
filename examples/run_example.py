import httpx  # Using httpx for async requests, can also use 'requests' for sync
import asyncio
import time
import os
from dotenv import load_dotenv

# It's assumed that the .env file for examples might be in the root or examples/ directory.
# Load environment variables (e.g., for API base URLs if needed, though they are hardcoded in servers for now)
load_dotenv(dotenv_path="../.env") # If .env is in root
load_dotenv() # If .env is in examples/

# Get base URLs from environment or use defaults
# These should match what's in alpaca_simulator/common/config.py and used by the servers
MARKET_DATA_BASE_URL = os.getenv("MARKET_DATA_SIMULATOR_URL", "http://localhost:8001")
TRADING_API_BASE_URL = os.getenv("MOCK_API_BASE_URL", "http://localhost:8000")

# --- Helper Functions ---
async def make_request(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    try:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()  # Raise an exception for bad status codes
        print(f"Request to {url} successful.")
        try:
            return response.json()
        except Exception:
            return response.text
    except httpx.HTTPStatusError as e:
        print(f"Error request to {url}: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"Error request to {url}: {e}")
    return None

async def run_all_examples():
    async with httpx.AsyncClient() as client:
        print("--- Starting Alpaca Backend Simulator Examples ---")
        print(f"Market Data URL: {MARKET_DATA_BASE_URL}")
        print(f"Trading API URL: {TRADING_API_BASE_URL}")
        print("\nNOTE: Ensure both market_data_api.py and trading_api.py servers are running in separate terminals before executing these examples.")
        print("You can run them using:")
        print("python -m alpaca_simulator.api.market_data_api")
        print("python -m alpaca_simulator.api.trading_api")
        print("----------------------------------------------------\n")

        # Give some time for servers to potentially start if run concurrently (not done here)
        # await asyncio.sleep(2)

        # --- Market Data API Examples ---
        print("\n--- Market Data API Examples ---")

        # Example 1: Get Latest Quotes
        print("\n1. Fetching latest quotes for AAPL,MSFT...")
        symbols_query = "AAPL,MSFT"
        latest_quotes = await make_request(client, "GET", f"{MARKET_DATA_BASE_URL}/v2/stocks/quotes/latest", params={"symbols": symbols_query})
        if latest_quotes:
            print("Latest Quotes:")
            for symbol, quote in latest_quotes.items():
                print(f"  {symbol}: Ask Price: {quote.get('ap')}, Bid Price: {quote.get('bp')}") # Using .get for safety

        # Example 2: Get Historical Bars
        print("\n2. Fetching historical bars for TSLA...")
        symbol_bars = "TSLA"
        bars_params = {"timeframe": "1Day", "start": "2023-01-01T00:00:00Z", "end": "2023-01-05T00:00:00Z"} # Example params
        historical_bars = await make_request(client, "GET", f"{MARKET_DATA_BASE_URL}/v2/stocks/{symbol_bars}/bars", params=bars_params)
        if historical_bars:
            print(f"Historical Bars for {historical_bars.get('symbol')}:")
            for bar in historical_bars.get('bars', []):
                print(f"  Timestamp: {bar.get('t')}, Open: {bar.get('o')}, Close: {bar.get('c')}, Volume: {bar.get('v')}")

        # --- Trading API Examples ---
        print("\n\n--- Trading API Examples ---")

        # Example 3: Get Account Information
        print("\n3. Fetching account information...")
        account_info = await make_request(client, "GET", f"{TRADING_API_BASE_URL}/v2/account")
        if account_info:
            print("Account Information:")
            print(f"  ID: {account_info.get('id')}, Status: {account_info.get('status')}, Buying Power: {account_info.get('buying_power')}")

        # Example 4: Place a Market Buy Order
        print("\n4. Placing a market buy order for 10 shares of AAPL...")
        market_order_payload = {
            "symbol": "AAPL",
            "qty": 10,
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }
        placed_market_order = await make_request(client, "POST", f"{TRADING_API_BASE_URL}/v2/orders", json=market_order_payload)
        if placed_market_order:
            print("Placed Market Order:")
            print(f"  ID: {placed_market_order.get('id')}, Symbol: {placed_market_order.get('symbol')}, Status: {placed_market_order.get('status')}, Filled Qty: {placed_market_order.get('filled_qty')}")
            # Store order_id for later fetching
            market_order_id = placed_market_order.get('id')
        else:
            market_order_id = None

        # Example 5: Place a Limit Sell Order
        print("\n5. Placing a limit sell order for 5 shares of MSFT...")
        limit_order_payload = {
            "symbol": "MSFT",
            "qty": 5,
            "side": "sell",
            "type": "limit",
            "time_in_force": "gtc",
            "limit_price": 350.50 # Example limit price
        }
        placed_limit_order = await make_request(client, "POST", f"{TRADING_API_BASE_URL}/v2/orders", json=limit_order_payload)
        if placed_limit_order:
            print("Placed Limit Order:")
            print(f"  ID: {placed_limit_order.get('id')}, Symbol: {placed_limit_order.get('symbol')}, Status: {placed_limit_order.get('status')}, Limit Price: {placed_limit_order.get('limit_price')}")
            limit_order_id = placed_limit_order.get('id')
        else:
            limit_order_id = None

        # Example 6: List Positions (after potential buy order)
        print("\n6. Listing current positions...")
        await asyncio.sleep(0.1) # Brief pause for server to process order if it was very fast
        positions = await make_request(client, "GET", f"{TRADING_API_BASE_URL}/v2/positions")
        if positions:
            if positions: # Check if list is not empty
                print("Current Positions:")
                for pos in positions:
                    print(f"  Symbol: {pos.get('symbol')}, Qty: {pos.get('qty')}, Avg Entry Price: {pos.get('avg_entry_price')}")
            else:
                print("  No open positions.")

        # Example 7: Get a specific order by ID (market order placed earlier)
        if market_order_id:
            print(f"\n7. Fetching market order by ID: {market_order_id}...")
            specific_order = await make_request(client, "GET", f"{TRADING_API_BASE_URL}/v2/orders/{market_order_id}")
            if specific_order:
                print("Fetched Order Details:")
                print(f"  ID: {specific_order.get('id')}, Status: {specific_order.get('status')}, Filled Avg Price: {specific_order.get('filled_avg_price')}")
        else:
            print("\n7. Skipping fetch market order by ID (previous order placement failed or no ID).")

        # Example 8: List all 'filled' and 'new' orders for AAPL and MSFT
        print("\n8. Listing 'filled' and 'new' orders for AAPL,MSFT...")
        list_orders_params = {"status": "filled,new", "symbols": "AAPL,MSFT", "limit": 10}
        filtered_orders = await make_request(client, "GET", f"{TRADING_API_BASE_URL}/v2/orders", params=list_orders_params)
        if filtered_orders:
            print("Filtered Orders:")
            for order in filtered_orders:
                print(f"  ID: {order.get('id')}, Symbol: {order.get('symbol')}, Type: {order.get('type')}, Status: {order.get('status')}")

        print("\n--- Examples Complete ---")

if __name__ == "__main__":
    # Python 3.7+
    asyncio.run(run_all_examples())
