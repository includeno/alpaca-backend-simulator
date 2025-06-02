import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_API_BASE_URL = os.getenv("ALPACA_API_BASE_URL", "https://paper-api.alpaca.markets")
MOCK_API_BASE_URL = os.getenv("MOCK_API_BASE_URL", "http://localhost:8000")
MARKET_DATA_SIMULATOR_URL = os.getenv("MARKET_DATA_SIMULATOR_URL", "http://localhost:8001")
