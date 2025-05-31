import pytest
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    GetOrdersRequest
)
from alpaca.trading.enums import (
    OrderSide,
    TimeInForce,
    QueryOrderStatus,
    OrderStatus, # For asserting order.status
    AccountStatus # For asserting account.status
)
# Import specific model types for isinstance checks
from alpaca.trading.models import Account, Position, Order
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.enums import StockTimeFrame
from alpaca.data.models import Quote, Bar
from alpaca.common.exceptions import APIError # For exception checking
from datetime import datetime, timezone
from decimal import Decimal # For precise numeric comparisons
import uuid # For generating unique client_order_ids or symbols

class TestAlpacaPyIntegration:

    def test_get_account(self, mock_trading_client: TradingClient):
        account = mock_trading_client.get_account()
        assert isinstance(account, Account)
        # Assuming mock_account_data in mock_service has "PA_MOCK_001" as account_number
        # and status "ACTIVE", which are default in the mock.
        assert account.account_number == "PA_MOCK_001"
        assert account.status == AccountStatus.ACTIVE
        assert isinstance(account.cash, Decimal)
        assert account.cash >= Decimal("0")

    def test_list_positions_initially_empty_for_new_symbol(self, mock_trading_client: TradingClient):
        # Using a unique symbol to ensure it's not present from a previous test run if mock service isn't reset
        unique_symbol = f"INITTEST{uuid.uuid4().hex[:6].upper()}"
        positions = mock_trading_client.get_all_positions()
        assert isinstance(positions, list)
        found = any(p.symbol == unique_symbol for p in positions)
        assert not found, f"Position for {unique_symbol} should not exist initially."

    def test_place_market_buy_order_and_verify_state(self, mock_trading_client: TradingClient):
        symbol = f"ALPYBUY{uuid.uuid4().hex[:6].upper()}"
        qty_to_buy = 2.0 # alpaca-py uses float for qty in requests

        initial_account = mock_trading_client.get_account()
        initial_cash = initial_account.cash # This is a Decimal

        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty_to_buy,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            client_order_id=f"test_buy_{uuid.uuid4().hex}" # Ensure unique client_order_id
        )
        order = mock_trading_client.submit_order(order_data=order_data)

        assert isinstance(order, Order)
        assert order.symbol == symbol
        # Mock service should fill market orders immediately
        assert order.status == OrderStatus.FILLED
        assert order.filled_qty == Decimal(str(qty_to_buy)) # Order model returns Decimal
        assert order.filled_avg_price is not None
        assert order.filled_avg_price > Decimal("0")

        # Verify position
        positions = mock_trading_client.get_all_positions()
        new_pos = next((p for p in positions if p.symbol == symbol), None)
        assert new_pos is not None, f"Position for {symbol} not found after buy order."
        assert isinstance(new_pos, Position)
        assert new_pos.qty == Decimal(str(qty_to_buy)) # Position model returns Decimal
        assert new_pos.avg_entry_price == order.filled_avg_price

        # Verify cash deduction
        final_account = mock_trading_client.get_account()
        # filled_qty and filled_avg_price on order are Decimal
        filled_value = (order.filled_qty or Decimal(0)) * (order.filled_avg_price or Decimal(0))
        # Ensure we are comparing Decimal to Decimal
        assert final_account.cash == initial_cash - filled_value

    def test_place_limit_order_accepted(self, mock_trading_client: TradingClient):
        symbol = f"ALPYLMT{uuid.uuid4().hex[:6].upper()}"
        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=1.0, # float for request
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
            limit_price=10.00 # float for request (alpaca-py converts to string if needed by API)
        )
        order = mock_trading_client.submit_order(order_data=order_data)
        assert isinstance(order, Order)
        assert order.symbol == symbol
        # Mock service is set to mark limit orders as 'new' or 'accepted'
        assert order.status in [OrderStatus.ACCEPTED, OrderStatus.NEW, OrderStatus.PENDING_NEW]

    def test_get_specific_order(self, mock_trading_client: TradingClient):
        symbol = f"ALPYGETORD{uuid.uuid4().hex[:6].upper()}"
        order_data = MarketOrderRequest(symbol=symbol, qty=1.0, side=OrderSide.BUY, time_in_force=TimeInForce.GTC)
        placed_order = mock_trading_client.submit_order(order_data=order_data)

        fetched_order = mock_trading_client.get_order_by_id(placed_order.id)
        assert isinstance(fetched_order, Order)
        assert fetched_order.id == placed_order.id
        assert fetched_order.symbol == symbol

    def test_get_non_existent_order(self, mock_trading_client: TradingClient):
        non_existent_order_id = str(uuid.uuid4())
        with pytest.raises(APIError) as excinfo:
            mock_trading_client.get_order_by_id(non_existent_order_id)
        # Mock service should return 404 for this
        assert excinfo.value.response.status_code == 404

    def test_list_orders_filtered(self, mock_trading_client: TradingClient):
        symbol_prefix = f"ALPYLIST{uuid.uuid4().hex[:4].upper()}"
        symbol1 = f"{symbol_prefix}A"
        symbol2 = f"{symbol_prefix}B"

        order1 = mock_trading_client.submit_order(MarketOrderRequest(symbol=symbol1, qty=1.0, side=OrderSide.BUY, time_in_force=TimeInForce.GTC))
        order2 = mock_trading_client.submit_order(LimitOrderRequest(symbol=symbol2, qty=1.0, side=OrderSide.SELL, time_in_force=TimeInForce.DAY, limit_price=100.00))

        # Test filtering by FILLED status and one symbol
        filter_req_filled = GetOrdersRequest(status=QueryOrderStatus.FILLED, symbols=[symbol1])
        filled_orders = mock_trading_client.get_orders(filter=filter_req_filled)
        assert isinstance(filled_orders, list)
        found_order1_filled = any(o.id == order1.id and o.status == OrderStatus.FILLED for o in filled_orders)
        assert found_order1_filled, f"Filled order for {symbol1} not found in filtered list."
        assert not any(o.symbol == symbol2 for o in filled_orders), "Should not find symbol2 in filled orders list for symbol1."

        # Test filtering by ACCEPTED/NEW status for the limit order
        # Mock service sets limit orders to 'new' or 'accepted'
        for expected_status in [QueryOrderStatus.ACCEPTED, QueryOrderStatus.NEW]:
            filter_req_accepted = GetOrdersRequest(status=expected_status, symbols=[symbol2])
            accepted_orders = mock_trading_client.get_orders(filter=filter_req_accepted)
            if any(o.id == order2.id for o in accepted_orders): # Check if the order is found with this status
                 assert any(o.id == order2.id and o.status in [OrderStatus.ACCEPTED, OrderStatus.NEW, OrderStatus.PENDING_NEW] for o in accepted_orders)
                 break # Found it with one of the statuses
        else: # If loop completes without break
            pytest.fail(f"Accepted/New limit order for {symbol2} (ID: {order2.id}) not found with expected status.")


    def test_place_sell_order_updates_position(self, mock_trading_client: TradingClient):
        symbol = f"ALPYSELL{uuid.uuid4().hex[:6].upper()}"
        initial_qty_val = 5.0
        sell_qty_val = 2.0

        # Establish initial position
        mock_trading_client.submit_order(MarketOrderRequest(symbol=symbol, qty=initial_qty_val, side=OrderSide.BUY, time_in_force=TimeInForce.GTC))

        # Sell some
        mock_trading_client.submit_order(MarketOrderRequest(symbol=symbol, qty=sell_qty_val, side=OrderSide.SELL, time_in_force=TimeInForce.GTC))

        positions = mock_trading_client.get_all_positions()
        final_pos = next((p for p in positions if p.symbol == symbol), None)
        assert final_pos is not None, f"Position for {symbol} should exist after partial sell."
        # Quantities in Position object are Decimal
        assert final_pos.qty == Decimal(str(initial_qty_val - sell_qty_val))

        # Sell the rest
        mock_trading_client.submit_order(MarketOrderRequest(symbol=symbol, qty=(initial_qty_val - sell_qty_val), side=OrderSide.SELL, time_in_force=TimeInForce.GTC))

        positions_after_all_sold = mock_trading_client.get_all_positions()
        pos_after_all_sold = next((p for p in positions_after_all_sold if p.symbol == symbol), None)
        # After selling all, the position might be removed or have qty 0 depending on broker/API. Mock service removes it.
        assert pos_after_all_sold is None or pos_after_all_sold.qty == Decimal("0")


    def test_get_latest_quote_integration(self, mock_stock_data_client: StockHistoricalDataClient):
        symbol = "AAPL" # Mock service returns this
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quote_data_map = mock_stock_data_client.get_stock_latest_quote(req)
        assert symbol in quote_data_map
        quote = quote_data_map[symbol]
        assert isinstance(quote, Quote)
        assert isinstance(quote.bid_price, float)
        assert isinstance(quote.ask_price, float)
        assert isinstance(quote.bid_size, int)
        assert isinstance(quote.ask_size, int)
        assert isinstance(quote.timestamp, datetime)

    def test_get_bars_integration(self, mock_stock_data_client: StockHistoricalDataClient):
        symbol = "TSLA" # Mock service returns this
        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=StockTimeFrame.DAY, # Using SDK enum
            start=datetime(2023, 1, 1, tzinfo=timezone.utc), # Using datetime objects
            end=datetime(2023, 1, 5, tzinfo=timezone.utc)
        )
        bars_data_map = mock_stock_data_client.get_stock_bars(req)
        assert symbol in bars_data_map
        assert len(bars_data_map[symbol]) > 0
        bar = bars_data_map[symbol][0]
        assert isinstance(bar, Bar)
        assert isinstance(bar.open, float)
        assert isinstance(bar.high, float)
        assert isinstance(bar.low, float)
        assert isinstance(bar.close, float)
        assert isinstance(bar.volume, float) # Mock service returns int, but SDK Bar model expects float
        assert isinstance(bar.timestamp, datetime)
