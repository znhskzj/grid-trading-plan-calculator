from abc import ABC, abstractmethod
from typing import Any, Dict

class TradingInterface(ABC):
    @abstractmethod
    def get_account_info(self, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def place_order(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def get_positions(self, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_history_orders(self, **kwargs) -> Dict[str, Any]:
        pass