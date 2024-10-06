from abc import ABC, abstractmethod
from typing import Tuple

class PriceQueryInterface(ABC):
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        pass