from typing import Dict, Tuple, Any
from .price_query_interface import PriceQueryInterface
from .trading_interface import TradingInterface

class APIManager:
    def __init__(self):
        self.price_query_apis: Dict[str, PriceQueryInterface] = {}
        self.trading_apis: Dict[str, TradingInterface] = {}

    def add_price_query_api(self, name: str, api: PriceQueryInterface):
        self.price_query_apis[name] = api

    def add_trading_api(self, name: str, api: TradingInterface):
        self.trading_apis[name] = api

    def get_price_query_api(self, name: str) -> PriceQueryInterface:
        if name not in self.price_query_apis:
            raise ValueError(f"Price query API '{name}' not found")
        return self.price_query_apis[name]

    def get_trading_api(self, name: str) -> TradingInterface:
        if name not in self.trading_apis:
            raise ValueError(f"Trading API '{name}' not found")
        return self.trading_apis[name]

    def get_stock_price(self, api_name: str, symbol: str) -> Tuple[float, str]:
        return self.get_price_query_api(api_name).get_stock_price(symbol)

    def place_order(self, api_name: str, **kwargs) -> Any:
        return self.get_trading_api(api_name).place_order(**kwargs)

    # Add other methods for account info, positions, history orders, etc.
