# src/gui/controllers/main_controller.py

import logging
import re
from typing import Dict, Any, List, Tuple
from src.utils.error_handler import APIError, TradingLogicError
from ..viewmodels.main_viewmodel import MainViewModel
from src.core.trading_logic import TradingLogic
from src.config.config_manager import ConfigManager
from src.api.api_manager import APIManager

logger = logging.getLogger(__name__)

class MainController:
    def __init__(self, main_window):
        self.main_window = main_window
        self.viewmodel = MainViewModel()
        self.trading_logic = TradingLogic()
        self.config_manager = ConfigManager()
        self.api_manager = APIManager()
        
    def run_calculation(self) -> None:
        logger.info("开始运行计算...")
        self.viewmodel.update_status("开始计算购买计划...")
        try:
            input_values = self.viewmodel.get_input_values()
            
            result = ""
            if self.viewmodel.current_symbol:
                result += f"标的: {self.viewmodel.current_symbol}\n"
                logger.info(f"计算购买计划，标的: {self.viewmodel.current_symbol}")
            else:
                logger.warning("当前没有设置标的")
                result += "警告: 未设置标的\n"
            
            total_funds = input_values['funds']
            result += f"总资金: {total_funds:.2f} | 可用资金: {total_funds:.2f}\n"
            result += f"初始价格: {input_values['initial_price']:.2f} | 止损价格: {input_values['stop_loss_price']:.2f} | 网格数量: {input_values['num_grids']}\n"
            
            buy_plan, warning_message = self.trading_logic.calculate_buy_plan(**input_values)
            
            calculation_result = self._format_buy_plan(buy_plan, warning_message)
            
            result += calculation_result
            
            if not result.strip():
                result = "没有计算结果。请确保所有输入字段都已填写，并且有效。"

            self.viewmodel.display_results(result)
            self.viewmodel.update_status("计算完成")
            
            logger.debug(f"计算完成，当前股票代码: {self.viewmodel.current_symbol}")
        except TradingLogicError as tle:
            error_message = f"交易逻辑错误: {str(tle)}"
            logger.error(error_message)
            self.viewmodel.display_results(error_message)
            self.viewmodel.update_status("计算失败：交易逻辑错误")
        except Exception as e:
            error_message = f"计算过程中发生错误: {str(e)}"
            logger.error(error_message, exc_info=True)
            self.viewmodel.display_results(error_message)
            self.viewmodel.update_status("计算失败：未知错误")
        
    def set_stock_price(self, symbol: str) -> None:
        logger.info(f"设置股票价格，标的: {symbol}")
        if self.viewmodel.api_choice != self.api_manager.current_price_api:
            self.initialize_api_manager()

        try:
            current_price, api_used = self.api_manager.get_stock_price(symbol)
            self._update_price_fields(symbol, current_price, api_used)
            
            self.viewmodel.display_results(f"已更新股票 {symbol} 的价格：{current_price:.2f}")
            
            self.main_window.check_widget_visibility()
        except APIError as e:
            self.handle_api_error(str(e), symbol)
        except Exception as e:
            self.handle_api_error(f"获取股票价格时发生未知错误: {str(e)}", symbol)

    def _update_price_fields(self, symbol: str, current_price: float, api_used: str) -> None:
        if not current_price:
            raise APIError(f"无法从 {api_used} 获取有效的价格数据")
            
        current_price = round(current_price, 2)
        stop_loss_price = round(current_price * 0.9, 2)
        self.viewmodel.update_price_fields(symbol, current_price, stop_loss_price)
        
        logger.info(f"更新价格字段，标的: {symbol}, 当前价格: {current_price:.2f}, 止损价格: {stop_loss_price:.2f}")
        status_message = f"已选择标的 {symbol}，当前价格为 {current_price:.2f} 元 (来自 {api_used})"
        self.viewmodel.update_status(status_message)
        result_message = (
            f"选中标的: {symbol}\n"
            f"当前价格: {current_price:.2f} 元 (来自 {api_used})\n"
            f"止损价格: {stop_loss_price:.2f} 元 (按90%当前价格计算)\n\n"
            f"初始价格和止损价格已更新。您可以直接点击\"计算购买计划\"按钮或调整其他参数。"
        )
        self.viewmodel.display_results(result_message)

    def handle_api_error(self, error_message: str, symbol: str) -> None:
        """处理API错误"""
        full_error_message = f"无法获取标的 {symbol} 的价格\n\n错误信息: {error_message}\n\n建议检查网络连接、API key 是否有效，或尝试切换到其他 API。"
        self.viewmodel.update_status(error_message)
        self.viewmodel.display_results(full_error_message)
        logger.error(error_message)
        self.viewmodel.current_symbol = symbol  # 即使获取价格失败，也设置当前标的

    def initialize_api_manager(self) -> None:
        # 实现API管理器的初始化逻辑
        self.api_manager.switch_price_api(self.viewmodel.api_choice)

    def _format_buy_plan(self, buy_plan: List[Tuple[float, int]], warning_message: str) -> str:
        result = ""
        if warning_message:
            result += warning_message + "\n\n"
        result += "购买计划如下：\n"
        for price, quantity in buy_plan:
            result += f"价格: {price:.2f}, 数量: {quantity}\n"
        return result