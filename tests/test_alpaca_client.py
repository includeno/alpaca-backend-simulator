import pytest
from alpaca_client.client import AlpacaClient
# These imports are to show where settings would normally come from.
# In tests, they are effectively overridden by conftest.py loading .env.test.
from config.settings import API_KEY, SECRET_KEY, ALPACA_API_BASE_URL, MOCK_API_BASE_URL, MARKET_DATA_SIMULATOR_URL
import os

class TestAlpacaClient:

    # Test Client Initialization
    def test_client_initialization_default(self, mock_trading_base_url, mock_api_key, mock_secret_key):
        """
        Tests client initialization with default parameters,
        expecting values from environment variables loaded by conftest.py.
        """
        # Temporarily clear os.environ to ensure AlpacaClient picks up from config.settings defaults
        # then relies on conftest to load .env.test which populates config.settings through load_dotenv()
        # This test ensures that AlpacaClient's default __init__ parameters work as expected.

        # The AlpacaClient's __init__ defaults to API_KEY, SECRET_KEY, ALPACA_API_BASE_URL from config.settings
        # config.settings.API_KEY is os.getenv("ALPACA_API_KEY")
        # config.settings.SECRET_KEY is os.getenv("ALPACA_SECRET_KEY")
        # config.settings.ALPACA_API_BASE_URL is os.getenv("ALPACA_API_BASE_URL", "default_value")
        # conftest.py ensures .env.test values are loaded into os.environ BEFORE these modules are loaded.

        client = AlpacaClient() # Uses defaults from config.settings, which are now from .env.test

        assert client.api_key == mock_api_key, "Client API key should match mock_api_key from .env.test"
        assert client.secret_key == mock_secret_key, "Client secret key should match mock_secret_key from .env.test"
        # The client's base_url default is config.settings.ALPACA_API_BASE_URL
        assert client.base_url == mock_trading_base_url, \
            f"Client base_url should match MOCK_API_BASE_URL from .env.test ({mock_trading_base_url}), got {client.base_url}"


    def test_client_initialization_custom_url(self, mock_api_key, mock_secret_key):
        custom_url = "http://custom.url"
        client = AlpacaClient(api_key=mock_api_key, secret_key=mock_secret_key, base_url=custom_url)
        assert client.base_url == custom_url
        assert client.api_key == mock_api_key
        assert client.secret_key == mock_secret_key

    # Trading API Tests
    def test_get_account_info(self, mock_trading_base_url, mock_api_key, mock_secret_key):
        client = AlpacaClient(api_key=mock_api_key, secret_key=mock_secret_key, base_url=mock_trading_base_url)
        account_info = client.get_account_info()
        assert isinstance(account_info, dict)
        assert "id" in account_info
        assert "status" in account_info
        assert "currency" in account_info
        assert "buying_power" in account_info

    def test_list_positions(self, mock_trading_base_url, mock_api_key, mock_secret_key):
        client = AlpacaClient(api_key=mock_api_key, secret_key=mock_secret_key, base_url=mock_trading_base_url)
        positions = client.list_positions()
        assert isinstance(positions, list)
        if positions: # Mock service might return empty list
            assert "symbol" in positions[0]
            assert "qty" in positions[0]

    def test_place_order(self, mock_trading_base_url, mock_api_key, mock_secret_key):
        client = AlpacaClient(api_key=mock_api_key, secret_key=mock_secret_key, base_url=mock_trading_base_url)
        symbol_to_trade = "MSFT"
        order_details = client.place_order(symbol=symbol_to_trade, qty=5, side="buy", type="market", time_in_force="gtc")
        assert isinstance(order_details, dict)
        assert "id" in order_details
        assert order_details["symbol"] == symbol_to_trade
        assert "qty" in order_details # Alpaca returns qty as string
        assert order_details["qty"] == "5"
        assert "status" in order_details

    # Market Data API Tests
    def test_get_latest_quote(self, mock_market_data_base_url, mock_api_key, mock_secret_key):
        # Note: AlpacaClient's auth headers might not be required or might be different for market data APIs.
        # For this test, we assume the market data simulator uses the same base_url and client structure.
        client = AlpacaClient(api_key=mock_api_key, secret_key=mock_secret_key, base_url=mock_market_data_base_url)
        symbol_to_quote = "GOOG"
        quote_data = client.get_latest_quote(symbol_to_quote)
        assert isinstance(quote_data, dict)
        assert "symbol" in quote_data
        assert quote_data["symbol"] == symbol_to_quote
        assert "quote" in quote_data
        assert "bp" in quote_data["quote"] # Bid Price
        assert "ap" in quote_data["quote"] # Ask Price

    def test_get_bars(self, mock_market_data_base_url, mock_api_key, mock_secret_key):
        client = AlpacaClient(api_key=mock_api_key, secret_key=mock_secret_key, base_url=mock_market_data_base_url)
        symbol_for_bars = "AMD"
        bars_data = client.get_bars(symbol_for_bars, timeframe="1Min", start="2023-01-01T00:00:00Z", end="2023-01-01T00:05:00Z")
        assert isinstance(bars_data, dict)
        assert "symbol" in bars_data
        assert bars_data["symbol"] == symbol_for_bars
        assert "bars" in bars_data
        assert isinstance(bars_data["bars"], list)
        if bars_data["bars"]: # Mock service might return empty list
            assert "o" in bars_data["bars"][0] # Open
            assert "h" in bars_data["bars"][0] # High
            assert "l" in bars_data["bars"][0] # Low
            assert "c" in bars_data["bars"][0] # Close
            assert "v" in bars_data["bars"][0] # Volume
            assert "t" in bars_data["bars"][0] # Timestamp
