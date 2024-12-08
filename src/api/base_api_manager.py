# src/api/base_api_manager.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from api.alpha_vantage_adapter import AlphaVantageAdapter
from src.config.config_manager import ConfigManager
from src.utils.logger import setup_logger

logger = setup_logger('api_manager')

class BaseAPIManager(ABC):
    """API管理器基类"""
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
    
    @abstractmethod
    def initialize_apis(self):
        """初始化API"""
        pass
    
    @abstractmethod
    def stop_all_connections(self):
        """停止所有连接"""
        pass

class PriceQueryManager(BaseAPIManager):
    """价格查询API管理器"""
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        self.api_config = self.config_manager.get_api_config()
        self.current_api = self.api_config.get('choice', 'yahoo')
        self.price_query_apis = {}
        self.initialize_apis()
    
    def initialize_apis(self):
        from .alpha_vantage_adapter import AlphaVantageAdapter
        from .yahoo_finance_adapter import YahooFinanceAdapter
        
        self.price_query_apis = {
            'yahoo': YahooFinanceAdapter(),
            'alpha_vantage': AlphaVantageAdapter(
                self.api_config.get('alpha_vantage_key', '')
            )
        }
    
    def switch_api(self, api_name: str):
        if api_name not in self.price_query_apis:
            raise ValueError(f"不支持的 API: {api_name}")
        self.current_api = api_name
        self.config_manager.set_api_config({'choice': api_name})
        logger.info(f"切换到价格查询 API: {api_name}")
    
    def set_alpha_vantage_key(self, api_key: str) -> None:
        """设置 Alpha Vantage API key 并重新初始化适配器"""
        self.api_config['alpha_vantage_key'] = api_key
        self.price_query_apis['alpha_vantage'] = AlphaVantageAdapter(api_key)
        self.config_manager.set_api_config(self.api_config)
        self.config_manager.save_user_config()
        logger.info("Alpha Vantage API key 已更新")
    
    def get_stock_price(self, symbol: str) -> tuple[float, str]:
        try:
            return self.price_query_apis[self.current_api].get_stock_price(symbol)
        except Exception as e:
            logger.error(f"使用 {self.current_api} 获取价格失败: {str(e)}")
            raise
    
    def stop_all_connections(self):
        for api in self.price_query_apis.values():
            if hasattr(api, 'close'):
                api.close()

class TradingAPIManager(BaseAPIManager):
    """交易API管理器"""
    def __init__(self, config_manager: ConfigManager):
        super().__init__(config_manager)
        self.trading_apis = {}
        self.current_api = None
        self.initialize_apis()
    
    def initialize_apis(self):
        from .moomoo_adapter import MoomooAdapter
        
        moomoo_config = self.config_manager.get_config('MoomooAPI', {})
        self.trading_apis['moomoo'] = MoomooAdapter(moomoo_config)
        self.current_api = 'moomoo'  # 默认使用 moomoo
    
    def get_current_api(self):
        return self.trading_apis.get(self.current_api)
    
    def stop_all_connections(self):
        for api in self.trading_apis.values():
            if hasattr(api, 'stop_all_connections'):
                api.stop_all_connections()