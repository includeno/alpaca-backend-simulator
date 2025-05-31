import pytest
import os
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    # Load environment variables from .env.test
    # This will override any existing system env variables for the test session
    # Correct path assuming .env.test is in the root, and conftest.py is in tests/
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
    if not os.path.exists(dotenv_path):
        print(f"Warning: .env.test file not found at {dotenv_path}")
        return
    load_dotenv(dotenv_path=dotenv_path, override=True)
    # For debugging:
    # print(f"Loaded test env from {dotenv_path}:")
    # print(f"  ALPACA_API_KEY={os.getenv('ALPACA_API_KEY')}")
    # print(f"  ALPACA_SECRET_KEY={os.getenv('ALPACA_SECRET_KEY')}")
    # print(f"  ALPACA_API_BASE_URL={os.getenv('ALPACA_API_BASE_URL')}")
    # print(f"  MOCK_API_BASE_URL={os.getenv('MOCK_API_BASE_URL')}")
    # print(f"  MARKET_DATA_SIMULATOR_URL={os.getenv('MARKET_DATA_SIMULATOR_URL')}")


@pytest.fixture(scope="session")
def mock_api_key():
    return os.getenv("ALPACA_API_KEY")

@pytest.fixture(scope="session")
def mock_secret_key():
    return os.getenv("ALPACA_SECRET_KEY")

@pytest.fixture(scope="session")
def mock_trading_base_url():
    # This should be the URL for the mock trading service
    return os.getenv("MOCK_API_BASE_URL")

@pytest.fixture(scope="session")
def mock_market_data_base_url():
    # This should be the URL for the market data simulator
    return os.getenv("MARKET_DATA_SIMULATOR_URL")
