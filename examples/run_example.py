import os
from alpaca_client.client import AlpacaClient
from config.settings import MOCK_API_BASE_URL, MARKET_DATA_SIMULATOR_URL
import requests # For exception handling

if __name__ == "__main__":
    print("Running Alpaca Client examples...")
    print("Using local mock services by default for trading and market data.")
    print(f"Mock Trading API URL: {MOCK_API_BASE_URL}")
    print(f"Market Data Simulator URL: {MARKET_DATA_SIMULATOR_URL}")
    print("-" * 50)

    # Get API key and secret key from environment variables or use defaults
    # For mock services, these don't need to be real but are expected by the client.
    api_key = os.getenv("ALPACA_API_KEY", "YOUR_MOCK_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY", "YOUR_MOCK_SECRET_KEY")

    if api_key == "YOUR_MOCK_API_KEY" or secret_key == "YOUR_MOCK_SECRET_KEY":
        print("\nWarning: Using default mock API key/secret. ")
        print("Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables if you intend to use real credentials.")

    print("-" * 50)
    print("--- Trading API Examples (Mock Service) ---")
    trading_client = AlpacaClient(api_key=api_key, secret_key=secret_key, base_url=MOCK_API_BASE_URL)

    try:
        print("\nFetching account information...")
        account_info = trading_client.get_account_info()
        print("Account Info:", account_info)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching account info: {e}")

    try:
        print("\nListing positions...")
        positions = trading_client.list_positions()
        if positions:
            print("Positions:", positions)
        else:
            print("No open positions.")
    except requests.exceptions.RequestException as e:
        print(f"Error listing positions: {e}")

    try:
        print("\nPlacing a sample order (AAPL, 1 share, buy, market, gtc)...")
        order_details = trading_client.place_order(symbol="AAPL", qty=1, side="buy", type="market", time_in_force="gtc")
        print("Order Placement Response:", order_details)
    except requests.exceptions.RequestException as e:
        print(f"Error placing order: {e}")

    print("-" * 50)
    print("\n--- Market Data API Examples (Mock Service) ---")
    # Note: The AlpacaClient is primarily for trading.
    # A separate client or methods would typically handle market data endpoints
    # which often have different authentication (e.g. some are keyless or use different key types).
    # For this example, we'll re-use AlpacaClient but point it to the market data sim.
    # The market data simulator itself uses /v2/stocks/{symbol}/quotes/latest etc.

    # The AlpacaClient is primarily for trading.
    # For this example, we'll re-use AlpacaClient but point it to the market data sim.
    # The AlpacaClient now has dedicated market data methods.
    market_data_client = AlpacaClient(api_key=api_key, secret_key=secret_key, base_url=MARKET_DATA_SIMULATOR_URL)
    # Note: Alpaca's actual market data API might use different keys or auth,
    # so a real-world scenario might involve a different client or configuration.
    # For this mock setup, we reuse the same keys and client structure.

    try:
        symbol_quote = "AAPL" # Changed to AAPL as per instructions
        print(f"\nFetching latest quote for {symbol_quote} using client method...")
        latest_quote = market_data_client.get_latest_quote(symbol_quote)
        print(f"Latest Quote for {symbol_quote}: {latest_quote}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest quote for {symbol_quote}: {e}")

    try:
        symbol_bars = "TSLA"
        timeframe = "1Day" # As per instructions
        start_date = "2023-10-01"
        end_date = "2023-10-05"
        print(f"\nFetching bars for {symbol_bars} ({timeframe}, {start_date}-{end_date}) using client method...")
        bars = market_data_client.get_bars(symbol_bars, timeframe=timeframe, start=start_date, end=end_date)
        print(f"Bars for {symbol_bars}: {bars}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bars for {symbol_bars}: {e}")

    print("\n" + "-" * 50)
    print("Example run finished.")
