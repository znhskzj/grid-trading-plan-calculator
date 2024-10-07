class APIError(Exception):
    """Base exception for API related errors."""
    pass

class PriceQueryError(APIError):
    """Exception raised for errors in price querying."""
    pass

class TradingError(APIError):
    """Exception raised for errors in trading operations."""
    pass