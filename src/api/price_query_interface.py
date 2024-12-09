# src/api/price_query_interface.py
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from src.config.config_manager import ConfigManager

class PriceQueryInterface(ABC):
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        """获取股票价格"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """获取API名称"""
        pass