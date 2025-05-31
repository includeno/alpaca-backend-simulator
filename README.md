# Alpaca Python Offline/Private SDK Environment

This project provides a modular Alpaca Python client development and testing environment designed for fully offline or private deployment. It includes mock services for trading and market data, allowing developers to build and test Alpaca integrations without needing live API keys or internet connectivity initially.

## Features

*   **Environment Variable Configuration**: Manage API keys, secrets, and base URLs via environment variables. Easily switch between local mock services and online Alpaca environments.
*   **Uses Official `alpaca-py` SDK**: Integrates the official `alpaca-py` library for interacting with Alpaca APIs (or the mock services).
*   **Market Data Simulator**: Simulates Alpaca market data endpoints (quotes, bars) for offline testing. This service provides realistic responses for market data queries.
*   **Local Mock Trading Service**: Simulates key Alpaca trading API endpoints (account, positions, orders) using FastAPI. It now features **stateful behavior**, including in-memory data persistence during a session and simulation of market order fills.
*   **Example Usage**: Demonstrates client initialization and API calls for both trading and market data, showcasing stateful interactions.
*   **Unit Tests**: Includes tests for the client against the mock services.

## Prerequisites

*   Python 3.7+
*   pip (Python package installer)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    (Replace `<repository_url>` and `<repository_directory>` with actual values when known)

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (This file includes `alpaca-py` and other necessary libraries like `fastapi`, `uvicorn`, `pytest`).

## Configuration

Configuration is managed via environment variables. You can set these directly in your system or use a `.env` file in the project root.

Create a `.env` file by copying the example:
```bash
cp .env.example .env
```
Then edit the `.env` file with your desired settings.

**Available Environment Variables:**

*   `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`: These are custom variables loaded by this project's `config/settings.py` and then used to explicitly instantiate `alpaca-py` clients.
*   `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`: These are the standard environment variables that `alpaca-py` can automatically detect if API key arguments are not passed directly to its client constructors. They are included in `.env.example` for completeness if you use other tools or scripts that rely on them.
*   `ALPACA_API_BASE_URL`: General base URL, often used to decide if targeting paper or live. `config/settings.py` uses this as a default for client instantiation if more specific mock URLs aren't overriding.
    *   For Alpaca paper trading: `https://paper-api.alpaca.markets`
    *   For local mock trading (used by `TradingClient`): `http://localhost:8000` (set this for `ALPACA_API_BASE_URL` or `MOCK_API_BASE_URL`)
*   `MOCK_API_BASE_URL`: Specifically for the local mock trading service. This is passed as the `url_override` parameter when instantiating `alpaca.trading.client.TradingClient` to connect to the local mock.
    *   Default: `http://localhost:8000`
*   `MARKET_DATA_SIMULATOR_URL`: Specifically for the local market data simulator. This is passed as `url_override` when instantiating `alpaca.data.historical.stock.StockHistoricalDataClient`.
    *   Default: `http://localhost:8001`

**Example `.env` for Local Development (using Mock Services):**
```env
ALPACA_API_KEY="your_mock_api_key"
ALPACA_SECRET_KEY="your_mock_secret_key"
ALPACA_API_BASE_URL="http://localhost:8000"
MOCK_API_BASE_URL="http://localhost:8000"
MARKET_DATA_SIMULATOR_URL="http://localhost:8001"
```

**Example `.env` for Alpaca Paper Trading:**
```env
ALPACA_API_KEY="YOUR_PAPER_API_KEY"
ALPACA_SECRET_KEY="YOUR_PAPER_SECRET_KEY"
ALPACA_API_BASE_URL="https://paper-api.alpaca.markets"
# MOCK_API_BASE_URL and MARKET_DATA_SIMULATOR_URL can be left commented out or set if needed for other purposes
```

## Running Local Services

For offline development and testing, you need to run the mock trading service and the market data simulator. Open two separate terminal windows for this.

1.  **Start the Mock Trading API Service:**
    ```bash
    python mock_service/main.py
    ```
    This service will typically run on `http://localhost:8000` (or the URL configured in `MOCK_API_BASE_URL`).
    It is stateful and simulates a real trading backend more closely:
    *   **In-memory Data Storage**: Account details, positions, and orders are stored in memory. This data persists as long as the service is running but will be reset upon restart.
    *   **Market Order Simulation**: Market orders are simulated as "filled" almost instantly, with corresponding updates to account cash and positions (quantity, average entry price, cost basis).
    *   **Limit Order Handling**: Limit orders are accepted and stored with a "new" or "accepted" status but are not automatically filled in this mock.
    *   **Order Retrieval**: Supports fetching specific orders via `GET /v2/orders/{order_id}` and listing orders with filters (status, symbols, dates, etc.) via `GET /v2/orders`. The `alpaca-py` SDK provides client methods like `get_order_by_id()` and `get_orders()` for these.

2.  **Start the Market Data Simulator:**
    ```bash
    python market_data_simulator/main.py
    ```
    This service will typically run on `http://localhost:8001` (or the URL configured in `MARKET_DATA_SIMULATOR_URL`). It provides sample quote and bar data.

## Using the `alpaca-py` SDK

The project now uses the official `alpaca-py` SDK. Key interactions involve:
*   Importing clients: `from alpaca.trading.client import TradingClient`, `from alpaca.data.historical.stock import StockHistoricalDataClient`.
*   Importing request objects and enums: e.g., `from alpaca.trading.requests import MarketOrderRequest, OrderSide, TimeInForce`, `from alpaca.data.requests import StockBarsRequest, StockTimeFrame`.
*   Instantiating clients with your API keys (from `config.settings`) and using `url_override` to point to the appropriate base URL for the target environment (live, paper, or local mock). For local mocks, use `MOCK_API_BASE_URL` for `TradingClient` and `MARKET_DATA_SIMULATOR_URL` for `StockHistoricalDataClient`.
*   Making API calls, e.g., `trading_client.get_account()`, `trading_client.submit_order(order_data=MarketOrderRequest(...))`, `stock_data_client.get_stock_bars(StockBarsRequest(...))`.
*   Handling responses, which are typically Pydantic models provided by `alpaca-py`.
*   Catching exceptions using `from alpaca.common.exceptions import APIError`.

## Running the Example Script

The example script (`examples/run_example.py`) demonstrates how to use the `alpaca-py` SDK to interact with both the mock trading and market data APIs.

Ensure your `.env` file is configured (e.g., for local mock services) and the local services are running.

```bash
python examples/run_example.py
```

You should see output demonstrating the stateful nature of the mock service:
*   Initial account information and (likely empty) positions.
*   Placement of a market order, followed by its confirmation showing a "filled" status.
*   Updated account information (e.g., reduced cash if it was a buy order).
*   Updated positions list showing the newly acquired asset.
*   Demonstrations of fetching the placed order by its ID and listing orders, including the one just placed.
*   Calls to the market data simulator for quotes and bars.

If you run the script multiple times without restarting the `mock_service`, you will see the state (account cash, positions, orders) persist and accumulate from previous runs.

## Running Tests

Unit tests are provided in `tests/test_alpaca_py_integration.py` to verify the functionality of the `alpaca-py` SDK client interacting with the mock services.

1.  **Ensure local services are running** (Mock Trading API and Market Data Simulator). Tests expect these to be available at the URLs defined in `.env.test` (defaults to `http://localhost:8000` and `http://localhost:8001`).
2.  **Run tests using pytest:**
    ```bash
    pytest
    ```
    Test-specific environment variables are loaded from `.env.test`.
    The unit tests now validate client operations against the stateful mock service, checking for expected changes in account balances, position quantities, and order statuses after simulated trades.
    You should see output indicating that all tests have passed.

## Switching Environments

To switch between the local mock environment and an online Alpaca environment (e.g., paper trading):

1.  **Update your `.env` file** (or system environment variables) with the appropriate values for `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, and `ALPACA_API_BASE_URL`.
    *   For Alpaca paper trading, set `ALPACA_API_BASE_URL="https://paper-api.alpaca.markets"`.
    *   For the local mock environment, set `ALPACA_API_BASE_URL="http://localhost:8000"`.
2.  **No code changes are required.** The `AlpacaClient` and example script will use the new configuration automatically because `config/settings.py` loads these values from the environment.
3.  If switching to an online environment, ensure the local mock services are not needed or are stopped if they conflict.

## Project Structure
```
alpaca-python-sdk/
├── config/             # Environment variable and settings management
│   ├── __init__.py
│   └── settings.py
├── examples/           # Example usage scripts
│   ├── __init__.py
│   └── run_example.py
├── market_data_simulator/ # FastAPI app for simulating market data
│   ├── __init__.py
│   └── main.py         # Contains FastAPI app, Pydantic models, endpoints
├── mock_service/       # FastAPI app for simulating trading API
│   ├── __init__.py
│   └── main.py         # Contains FastAPI app, Pydantic models, stateful logic
├── tests/              # Unit tests
│   ├── __init__.py
│   ├── conftest.py
│   └── test_alpaca_py_integration.py # Updated name
├── .env                # Local environment configurations (user-created from .env.example, gitignored)
├── .env.example        # Example environment file
├── .env.test           # Environment file for tests
├── .gitignore          # Specifies intentionally untracked files that Git should ignore
├── requirements.txt    # Project dependencies
└── README.md           # This file
```
