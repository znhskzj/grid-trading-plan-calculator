# /src/gui/viewmodels/main_viewmodel.py

from typing import Dict, Any, Optional
import logging
from src.utils.error_handler import InputValidationError
from src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class MainViewModel:
    def __init__(self):
        self.stock_symbol: str = ""
        self.current_price: float = 0.0
        self.stop_loss_price: float = 0.0
        self.total_investment: float = 50000.0  # 设置默认值
        self.grid_levels: int = 5  # 设置默认值
        self.allocation_method: int = "1"  # 设置默认值
        
        self.api_choice: str = "yahoo"
        self.current_symbol: str = ""
        self.status_message: str = ""
        self.result_message: str = ""
        self.trade_mode: str = "模拟"
        self.market: str = "美股"

    def update_stock_symbol(self, symbol: str) -> None:
        """更新股票代码并触发相关更新"""
        self.stock_symbol = symbol
        self.current_symbol = symbol
        logger.info(f"股票代码更新为: {symbol}")
        # 这里可以添加触发其他更新的逻辑

    def update_current_price(self, price: float) -> None:
        """更新当前价格并触发相关更新"""
        self.current_price = price
        logger.info(f"当前价格更新为: {price}")
        # 这里可以添加触发其他更新的逻辑，比如更新止损价格
        self.update_stop_loss_price(price * 0.9)

    def update_stop_loss_price(self, price: float) -> None:
        """更新止损价格"""
        self.stop_loss_price = price
        logger.info(f"止损价格更新为: {price}")

    def get_input_values(self) -> Dict[str, Any]:
        return {
            "funds": self.total_investment,
            "initial_price": self.current_price,
            "stop_loss_price": self.stop_loss_price,
            "num_grids": self.grid_levels,
            "allocation_method": int(self.allocation_method)
        }

    def update_status(self, message: str) -> None:
        """更新状态消息"""
        self.status_message = message
        logger.info(f"状态更新: {message}")
        # 这里可以添加通知UI更新状态的逻辑

    def display_results(self, result: str) -> None:
        """更新并显示结果"""
        self.result_message = result
        logger.info("结果更新")
        logger.debug(f"更新的结果: {result}")
        # 这里可以添加通知UI显示结果的逻辑

    def update_price_fields(self, symbol: str, current_price: float, stop_loss_price: float) -> None:
        """更新与价格相关的所有字段"""
        self.update_stock_symbol(symbol)
        self.update_current_price(current_price)
        self.update_stop_loss_price(stop_loss_price)
        logger.info(f"价格字段已更新 - 股票: {symbol}, 当前价格: {current_price}, 止损价格: {stop_loss_price}")

    def validate_inputs(self) -> Optional[str]:
        if self.current_price <= 0:
            return "当前价格必须大于0"
        if self.stop_loss_price <= 0:
            return "止损价格必须大于0"
        if self.total_investment <= 0:
            return "总投资额必须大于0"
        
        config_manager = ConfigManager()
        max_num_grids = int(config_manager.get_config('General', {}).get('max_num_grids', 10))
        if self.grid_levels <= 0 or self.grid_levels > max_num_grids:
            return f"网格级别必须大于0且不超过{max_num_grids}"
        
        if not self.allocation_method:
            return "分配方法未设置"
        return None

    def reset(self) -> None:
        """重置所有值到初始状态"""
        self.__init__()
        logger.info("ViewModel已重置到初始状态")

    def update_api_choice(self, api: str) -> None:
        """更新API选择"""
        self.api_choice = api
        logger.info(f"API选择更新为: {api}")

    def get_display_data(self) -> Dict[str, Any]:
        """获取用于显示的数据"""
        return {
            "symbol": self.stock_symbol,
            "current_price": self.current_price,
            "stop_loss_price": self.stop_loss_price,
            "total_investment": self.total_investment,
            "grid_levels": self.grid_levels,
            "allocation_method": self.allocation_method,
            "api_choice": self.api_choice,
            "status": self.status_message,
            "result": self.result_message
        }
    
    def update_calculation_inputs(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        logger.debug(f"ViewModel 更新: {kwargs}")  # 添加日志

    def bulk_update(self, data: Dict[str, Any]) -> None:
        """批量更新多个字段"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        logger.info("批量更新ViewModel字段")

    def get_trade_env(self) -> str:
        """获取交易环境（真实/模拟）"""
        # 这个方法需要根据实际情况实现
        return "模拟"  # 默认返回模拟环境

    def get_market(self) -> str:
        """获取交易市场（美股/港股）"""
        # 这个方法需要根据实际情况实现
        return "美股"  # 默认返回美股市场
    
    def update_trade_mode(self, mode: str) -> None:
        """更新交易模式"""
        self.trade_mode = mode
        logger.info(f"交易模式更新为: {mode}")

    def update_market(self, market: str) -> None:
        """更新交易市场"""
        self.market = market
        logger.info(f"交易市场更新为: {market}")

    def update_input_values(self, input_values: Dict[str, Any]) -> None:
        """从 GUI 获取并更新最新的输入值"""
        try:
            self.total_investment = float(input_values.get('funds', 0))
            self.current_price = float(input_values.get('initial_price', 0))
            self.stop_loss_price = float(input_values.get('stop_loss_price', 0))
            self.grid_levels = int(input_values.get('num_grids', 0))
            self.allocation_method = int(input_values.get('allocation_method', 0))
            logger.info("输入值已从 GUI 更新")
        except ValueError as e:
            logger.error(f"更新输入值时发生错误: {str(e)}")
            raise InputValidationError("请确保所有输入字段都包含有效的数值")
        
    def validate_num_grids(self, value: str) -> Optional[str]:
        try:
            num_grids = int(value)
            config_manager = ConfigManager()
            max_num_grids = int(config_manager.get_config('General', {}).get('max_num_grids', 10))
            if num_grids <= 0:
                return "网格数量必须大于0"
            elif num_grids > max_num_grids:
                return f"网格数量不能超过{max_num_grids}"
        except ValueError:
            return "请输入有效的整数"
        return None
    
    def update_allocation_method(self, method: int):
        self.allocation_method = method
        logger.debug(f"分配方法更新为: {method}")