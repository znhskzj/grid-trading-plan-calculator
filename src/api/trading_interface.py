# src/api/trading_interface.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List

class TradingInterface(ABC):
    @abstractmethod
    def get_account_info(self, **kwargs) -> Dict[str, Any]:
        """
        获取账户信息
        
        :param kwargs: 额外的参数
        :return: 账户信息字典
        """
        pass
    
    @abstractmethod
    def place_order(self, **kwargs) -> Any:
        """
        下单
        
        :param kwargs: 订单参数
        :return: 订单结果
        """
        pass
    
    @abstractmethod
    def get_positions(self, **kwargs) -> Dict[str, Any]:
        """
        获取持仓信息
        
        :param kwargs: 额外的参数
        :return: 持仓信息字典
        """
        pass
    
    @abstractmethod
    def get_history_orders(self, **kwargs) -> Dict[str, Any]:
        """
        获取历史订单
        
        :param kwargs: 额外的参数
        :return: 历史订单字典
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str, **kwargs) -> bool:
        """
        取消订单
        
        :param order_id: 订单ID
        :param kwargs: 额外的参数
        :return: 是否成功取消订单
        """
        pass

    @abstractmethod
    def get_real_time_quotes(self, symbols: List[str], **kwargs) -> Dict[str, Any]:
        """
        获取实时报价
        
        :param symbols: 股票代码列表
        :param kwargs: 额外的参数
        :return: 实时报价字典
        """
        pass