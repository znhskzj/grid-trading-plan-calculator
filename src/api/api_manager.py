import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_manager import ConfigManager
from typing import Dict, Any, Tuple
from .price_query_interface import PriceQueryInterface
from .trading_interface import TradingInterface
from .yahoo_finance_adapter import YahooFinanceAdapter
from .alpha_vantage_adapter import AlphaVantageAdapter
from .moomoo_adapter import MoomooAdapter

class APIManager:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.api_config = self.config_manager.get_api_config()
        self.current_api = self.api_config.get('choice', 'yahoo')
        
        self.price_query_apis: Dict[str, PriceQueryInterface] = {}
        self.trading_apis: Dict[str, TradingInterface] = {}

        # 初始化各种 API 适配器
        self.add_price_query_api('yahoo', YahooFinanceAdapter())
        self.add_price_query_api('alpha_vantage', AlphaVantageAdapter(self.api_config.get('alpha_vantage_key', '')))
        
        moomoo_config = self.config_manager.get_config('MoomooAPI', {})
        moomoo_adapter = MoomooAdapter(moomoo_config)
        self.add_price_query_api('moomoo', moomoo_adapter)
        self.add_trading_api('moomoo', moomoo_adapter)

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

    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        if self.current_api not in self.price_query_apis:
            raise ValueError(f"Current API '{self.current_api}' is not a valid price query API")
        return self.get_price_query_api(self.current_api).get_stock_price(symbol)

    def place_order(self, api_name: str, **kwargs) -> Any:
        return self.get_trading_api(api_name).place_order(**kwargs)

    def switch_api(self, api_name: str):
        if api_name not in self.price_query_apis:
            raise ValueError(f"Unsupported API: {api_name}")
        self.current_api = api_name
        self.config_manager.set_api_config({'choice': api_name})

    # 可以添加其他方法来封装不同的 API 操作
    def get_account_info(self, api_name: str, **kwargs) -> Dict[str, Any]:
        return self.get_trading_api(api_name).get_account_info(**kwargs)

    def get_positions(self, api_name: str, **kwargs) -> Dict[str, Any]:
        return self.get_trading_api(api_name).get_positions(**kwargs)

    def get_history_orders(self, api_name: str, **kwargs) -> Dict[str, Any]:
        return self.get_trading_api(api_name).get_history_orders(**kwargs)