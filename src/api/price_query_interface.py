# src/api/price_query_interface.py

from abc import ABC, abstractmethod
from typing import Tuple

class PriceQueryInterface(ABC):
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        """
        获取股票价格
        :param symbol: 股票代码
        :return: (价格, API名称)
        """
        pass