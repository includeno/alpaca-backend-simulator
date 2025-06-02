import pytest
from alpaca_simulator.domain.market_data.service import generate_latest_quotes, generate_historical_bars
from alpaca_simulator.domain.market_data.models import QuoteData, BarData, BarsResponse

def test_generate_latest_quotes_single_symbol():
    symbols = ["TESTSYM"]
    quotes = generate_latest_quotes(symbols)
    assert isinstance(quotes, dict)
    assert "TESTSYM" in quotes
    quote = quotes["TESTSYM"]
    assert isinstance(quote, QuoteData)
    assert quote.ask_price > 0
    assert quote.bid_price > 0
    assert quote.timestamp is not None

def test_generate_latest_quotes_multiple_symbols():
    symbols = ["SYM1", "SYM2"]
    quotes = generate_latest_quotes(symbols)
    assert isinstance(quotes, dict)
    assert "SYM1" in quotes
    assert "SYM2" in quotes
    assert isinstance(quotes["SYM1"], QuoteData)
    assert isinstance(quotes["SYM2"], QuoteData)

def test_generate_latest_quotes_empty_list():
    symbols = []
    quotes = generate_latest_quotes(symbols)
    assert isinstance(quotes, dict)
    assert not quotes # Empty dict expected

def test_generate_historical_bars():
    symbol = "TESTBAR"
    bars_response = generate_historical_bars(symbol, "2023-01-01", "2023-01-02", "1Day")
    assert isinstance(bars_response, BarsResponse)
    assert bars_response.symbol == symbol.upper()
    assert isinstance(bars_response.bars, list)
    if bars_response.bars: # If any bars are generated
        for bar in bars_response.bars:
            assert isinstance(bar, BarData)
            assert bar.o > 0 # open price
            assert bar.c > 0 # close price
            assert bar.h >= bar.o and bar.h >= bar.c # high
            assert bar.l <= bar.o and bar.l <= bar.c # low
            assert bar.t is not None # timestamp
            assert bar.v >= 0 # volume
