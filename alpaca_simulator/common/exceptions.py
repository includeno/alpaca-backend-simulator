# Custom exceptions for the Alpaca Simulator project

class AlpacaSimulatorException(Exception):
    """Base exception class for this application."""
    pass

class InvalidAPIVersion(AlpacaSimulatorException):
    """Raised when an invalid API version is requested."""
    pass

class AuthenticationError(AlpacaSimulatorException):
    """Raised for authentication failures."""
    pass

class RateLimitExceeded(AlpacaSimulatorException):
    """Raised when rate limits are hit."""
    pass

class InsufficientFundsError(AlpacaSimulatorException):
    """Raised when an action cannot be performed due to insufficient funds."""
    pass

class OrderNotFoundError(AlpacaSimulatorException):
    """Raised when an order cannot be found."""
    pass

class SymbolNotFoundError(AlpacaSimulatorException):
    """Raised when a symbol cannot be found or is invalid."""
    pass

# Add more specific exceptions as needed
