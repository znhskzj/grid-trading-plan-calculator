# src/utils/error_handler.py

from src.utils.logger import main_logger as logger

class BaseError(Exception):
    """应用程序所有自定义错误的基类。"""
    def __init__(self, message):
        super().__init__(message)
        logger.error(f"{self.__class__.__name__}: {message}")

class APIError(BaseError):
    """API相关错误的基类。"""
    pass

class PriceQueryError(APIError):
    """价格查询错误。"""
    pass

class TradingError(APIError):
    """交易操作错误。"""
    pass

class InputValidationError(BaseError):
    """输入验证错误。"""
    pass

class ConfigurationError(BaseError):
    """配置错误。"""
    pass

class GUIError(BaseError):
    """GUI操作错误。"""
    pass

class TradingLogicError(BaseError):
    """交易逻辑计算错误。"""
    pass