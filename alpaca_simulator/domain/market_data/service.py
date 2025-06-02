from datetime import datetime, timezone
import random
from typing import List, Optional, Dict, Any
from .models import QuoteData, BarData, BarsResponse

def generate_latest_quotes(symbols_list: List[str]) -> Dict[str, QuoteData]:
    response_data: Dict[str, Any] = {}
    # requested_symbols already processed in API layer
    for sym_ticker in symbols_list:
        now_utc = datetime.now(timezone.utc)

        local_bid_price = round(random.uniform(100, 200), 2)
        local_ask_price = round(local_bid_price + random.uniform(0.01, 0.1), 2)
        local_ask_size_val = float(random.randint(1, 10) * 100)
        local_bid_size_val = float(random.randint(1, 10) * 100)
        possible_exchanges = ["NASDAQ", "NYSE", "ARCA", None]
        local_ask_exchange_val = random.choice(possible_exchanges)
        local_bid_exchange_val = random.choice(possible_exchanges)
        local_conditions_val = random.choice([["R"], ["O", "R"], None])
        local_timestamp_val = now_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        local_tape_val = random.choice(["A", "B", "C", None])

        quote_instance = QuoteData(
            ask_price=local_ask_price,
            ask_size=local_ask_size_val,
            ask_exchange=local_ask_exchange_val,
            bid_price=local_bid_price,
            bid_size=local_bid_size_val,
            bid_exchange=local_bid_exchange_val,
            conditions=local_conditions_val,
            timestamp=local_timestamp_val,
            tape=local_tape_val
        )
        response_data[sym_ticker] = quote_instance
    return response_data

def generate_historical_bars(symbol: str, start_date: Optional[str], end_date: Optional[str], timeframe: Optional[str]) -> BarsResponse:
    bars_data: List[BarData] = []
    # Simulate generating a few bars. In a real scenario, this would depend on start/end/timeframe.
    num_bars = random.randint(1, 5)

    for i in range(num_bars):
        # Generate prices ensuring h >= o, h >= c, l <= o, l <= c
        open_price = round(random.uniform(90,110),2)
        close_price = round(random.uniform(90,110),2)
        high_price = round(max(open_price, close_price, random.uniform(open_price, open_price + 10)), 2)
        low_price = round(min(open_price, close_price, random.uniform(open_price - 10, open_price)), 2)

        # Ensure low is not greater than high (can happen with random generation)
        if low_price > high_price:
            low_price = high_price - random.uniform(0.1, 2.0) if high_price > 2.0 else high_price

        bar_ts_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds') + "Z" # Mock timestamp

        local_volume = float(random.randint(5000, 50000))
        local_trade_count = float(random.randint(50, 500)) if random.choice([True, False]) else None
        local_vwap = round(random.uniform(low_price, high_price), 2) if random.choice([True, False]) else None

        bar_instance = BarData(
            close_price=close_price,
            high_price=high_price,
            low_price=low_price,
            trade_count=local_trade_count,
            open_price=open_price,
            timestamp=bar_ts_iso,
            volume=local_volume,
            vwap=local_vwap
        )
        bars_data.append(bar_instance)

    return BarsResponse(
        bars=bars_data,
        symbol=symbol.upper(),
        next_page_token=None # Can be a string if pagination is implemented
    )
