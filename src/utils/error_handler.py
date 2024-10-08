# src/utils/error_handler.py

class BaseError(Exception):
    """Base exception for all custom errors in the application."""
    pass

class APIError(BaseError):
    """Base exception for API related errors."""
    pass

class PriceQueryError(APIError):
    """Exception raised for errors in price querying."""
    pass

class TradingError(APIError):
    """Exception raised for errors in trading operations."""
    pass

class InputValidationError(BaseError):
    """Exception raised for errors in input validation."""
    pass

class ConfigurationError(BaseError):
    """Exception raised for errors in configuration."""
    pass

class GUIError(BaseError):
    """Exception raised for errors in GUI operations."""
    pass