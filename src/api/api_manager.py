# src/api/api_manager.py

from typing import Dict, Any, Tuple
from src.utils.logger import setup_logger
from src.utils.error_handler import APIError, PriceQueryError, TradingError
from .alpha_vantage_adapter import AlphaVantageAdapter
from .yahoo_finance_adapter import YahooFinanceAdapter
from .moomoo_adapter import MoomooAdapter
from src.config.config_manager import ConfigManager

logger = setup_logger('api_manager', 'logs/api_manager.log')

class APIManager:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.api_config = self.config_manager.get_api_config()
        self.current_price_api = self.api_config.get('choice', 'yahoo')
        
        self.price_query_apis = {
            'yahoo': YahooFinanceAdapter(),
            'alpha_vantage': AlphaVantageAdapter(self.api_config.get('alpha_vantage_key', ''))
        }
        
        self.trading_api = MoomooAdapter(self.config_manager.get_config('MoomooAPI', {}))

    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        try:
            return self.price_query_apis[self.current_price_api].get_stock_price(symbol)
        except PriceQueryError as e:
            logger.error(f"使用 {self.current_price_api} 获取价格失败: {str(e)}")
            raise

    def switch_price_api(self, api_name: str):
        if api_name not in self.price_query_apis:
            raise ValueError(f"不支持的 API: {api_name}")
        self.current_price_api = api_name
        self.config_manager.set_api_config({'choice': api_name})
        logger.info(f"切换到价格查询 API: {api_name}")

    def test_moomoo_connection(self, trade_env, market, timeout=10.0):
        return self.trading_api.test_moomoo_connection(trade_env, market, timeout)

    def stop_all_connections(self):
        self.trading_api.stop_all_connections()

    def get_acc_list(self, trade_env, market):
        return self.trading_api.get_acc_list(trade_env, market)

    def get_account_info(self, **kwargs):
        return self.trading_api.get_account_info(**kwargs)

    def get_history_orders(self, **kwargs):
        return self.trading_api.get_history_orders(**kwargs)

    def get_positions(self, **kwargs):
        return self.trading_api.get_positions(**kwargs)

    def place_order(self, **kwargs):
        return self.trading_api.place_order(**kwargs)

    def unlock_trade(self, acc_id, trade_env, market, password):
        return self.trading_api.unlock_trade(acc_id, trade_env, market, password)

    # 可以在这里添加计算盈利的方法
    def calculate_profit(self, **kwargs):
        # 实现盈利计算逻辑
        pass