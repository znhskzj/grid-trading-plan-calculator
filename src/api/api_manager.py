# src/api/api_manager.py
from typing import Dict, Any, Tuple
from src.utils.logger import setup_logger
from src.utils.error_handler import APIError, PriceQueryError, TradingError
from src.config.config_manager import ConfigManager
from .base_api_manager import PriceQueryManager, TradingAPIManager

logger = setup_logger('api_manager')

class APIManager:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.price_query = PriceQueryManager(self.config_manager)
        self.trading = TradingAPIManager(self.config_manager)
    
    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        return self.price_query.get_stock_price(symbol)
    
    def switch_price_api(self, api_name: str):
        self.price_query.switch_api(api_name)
    
    def set_alpha_vantage_key(self, api_key: str) -> None:
        self.price_query.set_alpha_vantage_key(api_key)
    
    def test_moomoo_connection(self, trade_env, market, timeout=10.0):
        return self.trading.get_current_api().test_moomoo_connection(
            trade_env, market, timeout
        )
    
    def stop_all_connections(self):
        """停止所有API连接"""
        self.price_query.stop_all_connections()
        self.trading.stop_all_connections()
    
    # 以下方法委托给当前的交易API
    def get_acc_list(self, trade_env, market):
        return self.trading.get_current_api().get_acc_list(trade_env, market)
    
    def get_account_info(self, **kwargs):
        return self.trading.get_current_api().get_account_info(**kwargs)
    
    def get_history_orders(self, **kwargs):
        return self.trading.get_current_api().get_history_orders(**kwargs)
    
    def get_positions(self, **kwargs):
        return self.trading.get_current_api().get_positions(**kwargs)
    
    def place_order(self, **kwargs):
        return self.trading.get_current_api().place_order(**kwargs)
    
    def unlock_trade(self, acc_id, trade_env, market, password):
        return self.trading.get_current_api().unlock_trade(
            acc_id, trade_env, market, password
        )