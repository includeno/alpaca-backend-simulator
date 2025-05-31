import os
import time
from datetime import datetime, timezone # Import timezone
from decimal import Decimal # For handling cash amounts precisely

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    GetOrdersRequest,
    OrderSide,
    TimeInForce,
    QueryOrderStatus # Enum for order status filtering
)
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
# Removed: from alpaca.data.enums import StockTimeFrame (and any other StockTimeFrame or direct TimeFrame import)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit # Corrected import
from alpaca.common.exceptions import APIError

from config import settings # Import project settings

def run_examples():
    print("--- Alpaca Python SDK (alpaca-py) Example Script ---")
    print(f"Using MOCK_API_BASE_URL (for TradingClient): {settings.MOCK_API_BASE_URL}")
    print(f"Using MARKET_DATA_SIMULATOR_URL (for StockHistoricalDataClient): {settings.MARKET_DATA_SIMULATOR_URL}")
    print("--- --- --- ---\n")

    # Default mock keys if not provided by environment
    DEFAULT_API_KEY = "DEFAULT_MOCK_API_KEY"
    DEFAULT_SECRET_KEY = "DEFAULT_MOCK_SECRET_KEY"

    api_key_to_use = settings.API_KEY
    secret_key_to_use = settings.SECRET_KEY

    using_defaults = False
    if not api_key_to_use:
        api_key_to_use = DEFAULT_API_KEY
        using_defaults = True
    if not secret_key_to_use:
        secret_key_to_use = DEFAULT_SECRET_KEY
        using_defaults = True

    if using_defaults:
        print(f"Warning: ALPACA_API_KEY or ALPACA_SECRET_KEY not found in environment or .env file. "
              f"Using hardcoded default mock keys ('{DEFAULT_API_KEY}', '{DEFAULT_SECRET_KEY[:4]}...'). "
              f"Please set them in your .env file for specific mock keys or real trading.\n")
    elif "YOUR_MOCK_API_KEY" in api_key_to_use or api_key_to_use == "test_api_key": # Or other known placeholders
         print("Info: Using placeholder or test API keys from .env file. This is fine for mock testing.\n")
    else:
        print("Info: Using API keys loaded from your environment/.env file.\n")

    # Instantiate TradingClient for trading operations
    # Uses APCA_API_KEY_ID and APCA_API_SECRET_KEY if api_key/secret_key are None
    # For our setup, we explicitly pass keys from our custom config/settings.py which loads ALPACA_API_KEY
    trading_client = TradingClient(
        api_key=api_key_to_use,
        secret_key=secret_key_to_use,
        paper=True, # Important for paper, or use live=True for live. Mock doesn't care.
        url_override=settings.MOCK_API_BASE_URL # Points to our mock trading service
    )

    # Instantiate StockHistoricalDataClient for market data
    # Also uses APCA_API_KEY_ID etc. by default.
    stock_data_client = StockHistoricalDataClient(
        api_key=api_key_to_use,
        secret_key=secret_key_to_use,
        url_override=settings.MARKET_DATA_SIMULATOR_URL # Points to our mock market data service
    )

    print("--- Trading API Examples (using alpaca-py & Stateful Mock Service) ---")
    try:
        # 1. Get Account Information
        print("\n1. Fetching Account Information...")
        account_info = trading_client.get_account()
        initial_cash = Decimal(account_info.cash) # Ensure it's Decimal
        print(f"   Account Info: ID={account_info.id}, Cash={initial_cash:.2f}, Buying Power={account_info.buying_power}, Equity={account_info.equity}")

        # 2. List Initial Positions for specific example symbols
        example_symbol_1 = "ALPYEX1"
        example_symbol_2 = "ALPYEX2"
        print(f"\n2. Listing Initial Positions for {example_symbol_1}, {example_symbol_2}...")
        initial_positions = trading_client.get_all_positions()
        found_initial_example_pos = False
        for pos in initial_positions:
            if pos.symbol in [example_symbol_1, example_symbol_2]:
                print(f"   Found existing position for {pos.symbol}: Qty={pos.qty}, Avg Entry={pos.avg_entry_price}")
                found_initial_example_pos = True
        if not found_initial_example_pos:
            print(f"   No initial positions found for {example_symbol_1} or {example_symbol_2} (expected for new symbols or fresh mock service).")

        # 3. Place a Market Buy Order for example_symbol_1
        qty_buy1 = 5.0
        print(f"\n3. Placing Market Buy Order for {qty_buy1} shares of {example_symbol_1}...")
        market_order_data1 = MarketOrderRequest(
            symbol=example_symbol_1,
            qty=qty_buy1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        buy_order1 = trading_client.submit_order(order_data=market_order_data1)
        print(f"   Placed Buy Order 1: ID={buy_order1.id}, Symbol={buy_order1.symbol}, Status={buy_order1.status}, FilledQty={buy_order1.filled_qty}, FilledAvgPrice={buy_order1.filled_avg_price}")
        buy_order1_id = buy_order1.id

        # Give mock service a moment to process if needed, though it should be quick for fills
        time.sleep(0.1)

        # 4. Place another Market Buy Order for example_symbol_2
        qty_buy2 = 3.0
        print(f"\n4. Placing Market Buy Order for {qty_buy2} shares of {example_symbol_2}...")
        market_order_data2 = MarketOrderRequest(
            symbol=example_symbol_2,
            qty=qty_buy2,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC
        )
        buy_order2 = trading_client.submit_order(order_data=market_order_data2)
        print(f"   Placed Buy Order 2: ID={buy_order2.id}, Symbol={buy_order2.symbol}, Status={buy_order2.status}, FilledQty={buy_order2.filled_qty}, FilledAvgPrice={buy_order2.filled_avg_price}")

        time.sleep(0.1)

        # 5. List Positions After Buy Orders
        print("\n5. Listing Positions After Buy Orders...")
        positions_after_buy = trading_client.get_all_positions()
        print("   Current Positions (relevant to example):")
        found_updated_pos = False
        for pos in positions_after_buy:
            if pos.symbol in [example_symbol_1, example_symbol_2]:
                print(f"   - Symbol: {pos.symbol}, Qty: {pos.qty}, Avg Entry: {pos.avg_entry_price}, MarketVal: {pos.market_value}")
                found_updated_pos = True
        if not found_updated_pos:
            print(f"   No positions found for {example_symbol_1} or {example_symbol_2} (unexpected if orders filled).")

        # 6. Get Specific Order Details for the first buy order
        if buy_order1_id:
            print(f"\n6. Fetching details for Order ID: {buy_order1_id}...")
            retrieved_order1 = trading_client.get_order_by_id(buy_order1_id)
            print(f"   Retrieved Order 1: Symbol={retrieved_order1.symbol}, Qty={retrieved_order1.qty}, Status={retrieved_order1.status}, FilledQty={retrieved_order1.filled_qty}")

        # 7. List All 'filled' Orders for the example symbols
        print(f"\n7. Listing 'filled' Orders for {example_symbol_1}, {example_symbol_2}...")
        get_orders_filter = GetOrdersRequest(
            status=QueryOrderStatus.FILLED,
            symbols=[example_symbol_1, example_symbol_2],
            limit=10,
            direction="desc"
        )
        filled_orders = trading_client.get_orders(filter=get_orders_filter)
        print(f"   Found {len(filled_orders)} filled orders for these symbols:")
        for order in filled_orders:
            print(f"   - ID: {order.id}, Sym: {order.symbol}, Stat: {order.status}, FilledQty: {order.filled_qty}, FilledAvgPrice: {order.filled_avg_price}")
            assert order.status == QueryOrderStatus.FILLED

        # 8. Place a Limit Sell Order for example_symbol_1 (will be 'accepted' or 'new' by current mock)
        qty_sell_limit = 2.0
        # Ensure limit_price matches the type expected by LimitOrderRequest (usually float or Decimal)
        # The mock service's OrderRequest model uses Optional[str], but alpaca-py's LimitOrderRequest expects float.
        # For simplicity, let's assume the mock can handle a string that can be parsed to float.
        # However, best practice is to use float for the SDK.
        limit_price_sell_val = 200.00
        print(f"\n8. Placing Limit Sell Order for {qty_sell_limit} of {example_symbol_1} @{limit_price_sell_val:.2f} (expect 'accepted' or 'new')...")
        limit_order_data = LimitOrderRequest(
            symbol=example_symbol_1,
            qty=qty_sell_limit,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price_sell_val
        )
        limit_sell_order = trading_client.submit_order(order_data=limit_order_data)
        print(f"   Placed Limit Sell Order: ID={limit_sell_order.id}, Symbol={limit_sell_order.symbol}, Status={limit_sell_order.status}")
        assert limit_sell_order.status in [QueryOrderStatus.ACCEPTED, QueryOrderStatus.NEW, QueryOrderStatus.PENDING_NEW]


        # 9. Check Account Information Again
        print("\n9. Fetching Account Information After Trades...")
        final_account_info = trading_client.get_account()
        final_cash = Decimal(final_account_info.cash) # Ensure Decimal
        print(f"    Final Account Info: Cash={final_cash:.2f}, Equity={final_account_info.equity}")

        cash_change = final_cash - initial_cash
        print(f"    Cash Change: {cash_change:.2f}")
        if abs(cash_change) < Decimal("0.01") and any(o.status == QueryOrderStatus.FILLED for o in filled_orders):
             print("    Note: Cash change is very small despite filled orders. This might indicate an issue in mock accounting or offsetting trades not captured here.")
        elif not any(o.status == QueryOrderStatus.FILLED for o in filled_orders) and abs(cash_change) < Decimal("0.01"):
             print("    Cash change is negligible, consistent with no market orders being filled.")


    except APIError as e:
        print(f"\n!!! An Alpaca API error occurred during trading examples: {str(e)}") # Using str(e) for robust summary
        # The detailed response (if JSON) is still attempted below, which is good.
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json() # Alpaca often returns JSON errors
                print(f"!!! Error Details: {error_details}")
            except ValueError: # If response is not JSON
                print(f"!!! Raw Response: {e.response.text}")

    except Exception as e:
        print(f"\n!!! An unexpected error occurred during trading examples: {type(e).__name__} - {e}")

    print("\n\n--- Market Data API Examples (using alpaca-py & Mock Simulator) ---")
    try:
        # 1. Get Latest Quote for AAPL
        print("\n1. Fetching Latest Quote for AAPL...")
        latest_quote_req = StockLatestQuoteRequest(symbol_or_symbols="AAPL")
        latest_quote_data_map = stock_data_client.get_stock_latest_quote(latest_quote_req)
        if "AAPL" in latest_quote_data_map:
            aapl_quote = latest_quote_data_map["AAPL"]
            print(f"   Latest Quote for AAPL: Bid={aapl_quote.bid_price}, Ask={aapl_quote.ask_price}, Timestamp={aapl_quote.timestamp}")
        else:
            print("   AAPL quote not found in response.")

        # 2. Get 1-Day Bars for TSLA
        print("\n2. Fetching 1-Day Bars for TSLA...")
        bars_req = StockBarsRequest(
            symbol_or_symbols="TSLA",
            timeframe=TimeFrame.Day, # Use TimeFrame class property
            start=datetime(2023, 1, 1, tzinfo=timezone.utc),
            end=datetime(2023, 1, 5, tzinfo=timezone.utc)
        )
        bars_data_map = stock_data_client.get_stock_bars(bars_req)
        if "TSLA" in bars_data_map and bars_data_map["TSLA"]:
            tsla_bars = bars_data_map["TSLA"]
            print(f"   Found {len(tsla_bars)} bars for TSLA. First bar: O={tsla_bars[0].open}, H={tsla_bars[0].high}, L={tsla_bars[0].low}, C={tsla_bars[0].close}, V={tsla_bars[0].volume}, T={tsla_bars[0].timestamp}")
        else:
            print("   No bars found for TSLA in the example response.")

    except APIError as e:
        print(f"\n!!! An Alpaca API error occurred during market data examples: {str(e)}") # Using str(e) for robust summary
        # The detailed response (if JSON) is still attempted below.
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                print(f"!!! Error Details: {error_details}")
            except ValueError:
                print(f"!!! Raw Response: {e.response.text}")
    except Exception as e:
        print(f"\n!!! An unexpected error occurred during market data examples: {type(e).__name__} - {e}")

    print("\n\n--- Example Script Finished ---")

if __name__ == "__main__":
    print("Reminder: Ensure the mock_service and market_data_simulator are running in separate terminals.")
    print("If you just restarted them, their state (like positions, orders) will be fresh for these examples.\n")
    time.sleep(1)
    run_examples()
