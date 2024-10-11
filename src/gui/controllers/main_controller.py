# src/gui/controllers/main_controller.py

import logging
import pandas as pd
from tkinter import messagebox, simpledialog
import tkinter as tk
from typing import Dict, Any, List, Tuple, Optional
from src.utils.error_handler import APIError, TradingLogicError, InputValidationError
from ..viewmodels.main_viewmodel import MainViewModel
from src.core.trading_logic import TradingLogic
from src.config.config_manager import ConfigManager
from src.api.moomoo_adapter import MoomooAdapter, TrdEnv, TrdMarket
from src.api.api_manager import APIManager

logger = logging.getLogger(__name__)

class MainController:
    def __init__(self, main_window):
        self.main_window = main_window
        self.config_manager = ConfigManager()
        self.viewmodel = MainViewModel()
        self.viewmodel.api_choice = self.config_manager.get_config('API', {}).get('choice', 'yahoo')
        self.trading_logic = TradingLogic(self.config_manager)
        self.api_manager = APIManager()
        self.moomoo_api = self.api_manager.trading_api  # 使用 APIManager 中的 MoomooAdapter 实例
        self.current_acc_id = None
        self.trade_env = TrdEnv.SIMULATE
        self.market = TrdMarket.US
        self.moomoo_connected = False
        self.last_connected_env = None
        self.last_connected_market = None
        self.force_simulate = False

        # 加载默认配置
        default_config = self.config_manager.get_config('RecentCalculations', {})
        
        # 使用默认配置更新 ViewModel
        self.viewmodel.update_calculation_inputs(
            total_investment=float(default_config.get('funds', 50000)),
            grid_levels=int(default_config.get('num_grids', 10)),
            allocation_method=default_config.get('allocation_method', '0')
        )

    def get_current_account(self):
        self.trade_env = TrdEnv.REAL if self.viewmodel.trade_mode == "真实" else TrdEnv.SIMULATE
        self.market = TrdMarket.US if self.viewmodel.market == "美股" else TrdMarket.HK
        logger.info(f"Current settings: trade_env={self.trade_env}, market={self.market}")
        acc_list = self.moomoo_api.get_acc_list(self.trade_env, self.market)
        if acc_list is not None and not acc_list.empty:
            self.current_acc_id = acc_list.iloc[0]['acc_id']
            logger.info(f"Selected account: {self.current_acc_id}")
        else:
            self.current_acc_id = None
            logger.warning("No accounts found")

    def query_available_funds(self):
        if not self._validate_account_access():
            return
        
        info = self.moomoo_api.get_account_info(self.current_acc_id, self.trade_env, self.market)
        if info is not None and not info.empty:
            self._display_account_info(info)
        else:
            self.viewmodel.display_results("无法获取账户信息")

    def _validate_account_access(self) -> bool:
        if not self.check_moomoo_connection():
            return False
        if self.current_acc_id is None:
            self.viewmodel.display_results("无法获取账户信息")
            return False
        return True

    def _display_account_info(self, info: pd.DataFrame):
        env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
        market_str = "美股" if self.market == TrdMarket.US else "港股"
        result = f"当前连接: {market_str}{env_str}账户\n"
        result += f"账户 {self.current_acc_id} 资金情况:\n"
        
        def safe_format(value):
            try:
                return f"${float(value):,.2f}" if value != 'N/A' else 'N/A'
            except ValueError:
                return str(value)
        
        fields = [
            ("总资产", 'total_assets'),
            ("现金", 'cash'),
            ("证券市值", 'securities_assets'),
            ("购买力", 'power'),
            ("最大购买力", 'max_power_short'),
            ("币种", 'currency')
        ]
        
        for label, key in fields:
            value = safe_format(info[key].values[0])
            if value != 'N/A' and value != '$N/A':
                result += f"{label}: {value}\n"
        
        self.viewmodel.display_results(result)
        self.viewmodel.update_status(f"Moomoo API - {market_str}{env_str}账户 - 资金查询完成")

    def test_moomoo_connection(self):
        trade_env = self.viewmodel.get_trade_env()
        market = self.viewmodel.get_market()
        try:
            result = self.api_manager.test_moomoo_connection(trade_env, market)
            if result:
                self.viewmodel.update_status("Moomoo 连接测试成功")
            else:
                self.viewmodel.update_status("Moomoo 连接测试失败")
        except Exception as e:
            self.viewmodel.update_status(f"Moomoo 连接测试错误: {str(e)}")
            logger.error(f"Moomoo 连接测试错误: {str(e)}")
    
    def run_calculation(self) -> None:
        logger.info("开始运行计算...")
        self.viewmodel.update_status("开始计算购买计划...")
        
        try:
            input_values = self.viewmodel.get_input_values()
            logger.debug(f"计算使用的输入值: {input_values}")
        
            if not self.viewmodel.current_symbol:
                logger.warning("股票代码未设置，使用默认值进行计算")
                self.viewmodel.update_stock_symbol("DEFAULT")

            result = self._prepare_result_header()
            buy_plan, warning_message, summary = self.trading_logic.calculate_buy_plan(**input_values)
            
            calculation_result = self._format_buy_plan(buy_plan, warning_message, summary)
            result += calculation_result
            
            self.display_results(result)
            self.viewmodel.update_status("计算完成")
            
            logger.debug(f"计算完成，当前股票代码: {self.viewmodel.current_symbol}")
        except Exception as e:
            self._handle_calculation_error(f"计算过程中发生错误: {str(e)}")
            
    def calculate_with_reserve(self, reserve_percentage: int) -> None:
        """执行保留部分资金的计算"""
        logger.info(f"开始计算（保留{reserve_percentage}%资金）...")
        self.viewmodel.update_status(f"开始计算（保留{reserve_percentage}%资金）...")
        
        try:
            self.viewmodel.update_input_values(self.view)
            self._validate_inputs()
            input_values = self.viewmodel.get_input_values()
            
            result = self._prepare_result_header(with_reserve=True, reserve_percentage=reserve_percentage)
            buy_plan, warning_message, reserved_funds, summary = self.trading_logic.calculate_with_reserve(input_values, reserve_percentage)
            
            calculation_result = self._format_buy_plan(buy_plan, warning_message, summary, reserved_funds)
            result += calculation_result
            
            self.viewmodel.display_results(result)
            self.viewmodel.update_status(f"计算完成（保留{reserve_percentage}%资金）")
            
            logger.debug(f"计算完成（保留{reserve_percentage}%资金），当前股票代码: {self.viewmodel.current_symbol}")
        except InputValidationError as e:
            self._handle_calculation_error(str(e))
        except TradingLogicError as e:
            self._handle_calculation_error(str(e))
        except Exception as e:
            self._handle_calculation_error(f"计算过程中发生未知错误: {str(e)}")

    def _calculate_without_stock(self):
        """在没有设置股票代码的情况下进行计算"""
        input_values = self.viewmodel.get_input_values()
        result = "注意：未设置股票代码，使用当前输入值进行计算\n\n"
        result += self._prepare_result_header()
        buy_plan, warning_message, summary = self.trading_logic.calculate_buy_plan(**input_values)
        calculation_result = self._format_buy_plan(buy_plan, warning_message, summary)
        result += calculation_result
        self.viewmodel.display_results(result)
        self.viewmodel.update_status("计算完成（无股票代码）")
    
    def _validate_inputs(self) -> None:
        """验证输入值"""
        error_message = self.viewmodel.validate_inputs()
        if error_message:
            raise InputValidationError(error_message)

    def _prepare_result_header(self) -> str:
        """准备结果头部信息"""
        result = ""
        if self.viewmodel.current_symbol:
            result += f"标的: {self.viewmodel.current_symbol}\n"
            logger.info(f"计算购买计划，标的: {self.viewmodel.current_symbol}")
        else:
            logger.warning("当前没有设置标的")
            result += "警告: 未设置标的\n"
        
        input_values = self.viewmodel.get_input_values()
        result += (f"总资金: {input_values['funds']:.2f} | "
                   f"可用资金: {input_values['funds']:.2f}\n"
                   f"初始价格: {input_values['initial_price']:.2f} | "
                   f"止损价格: {input_values['stop_loss_price']:.2f} | "
                   f"网格数量: {input_values['num_grids']}\n")
        return result

    def set_stock_price(self, symbol: str) -> None:
        logger.info(f"设置股票价格，标的: {symbol}")
        if self.viewmodel.api_choice != self.api_manager.current_price_api:
            self._initialize_api_manager()

        try:
            current_price, api_used = self.api_manager.get_stock_price(symbol)
            self._update_price_fields(symbol, current_price, api_used)
            
            self.viewmodel.display_results(f"已更新股票 {symbol} 的价格：{current_price:.2f}")
            
            # 确保更新 UI
            self.main_window.right_frame.update_fields({
                'initial_price': current_price,
                'stop_loss_price': current_price * 0.9
            })
            
        except APIError as e:
            self._handle_api_error(str(e), symbol)
        except Exception as e:
            self._handle_api_error(f"获取股票价格时发生未知错误: {str(e)}", symbol)

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

    def _handle_api_error(self, error_message: str, symbol: str) -> None:
        """处理API错误"""
        full_error_message = (f"无法获取标的 {symbol} 的价格\n\n"
                              f"错误信息: {error_message}\n\n"
                              f"建议检查网络连接、API key 是否有效，或尝试切换到其他 API。")
        self.viewmodel.update_status(error_message)
        self.viewmodel.display_results(full_error_message)
        logger.error(error_message)
        self.viewmodel.current_symbol = symbol  # 即使获取价格失败，也设置当前标的

    def _initialize_api_manager(self) -> None:
        """初始化API管理器"""
        self.api_manager.switch_price_api(self.viewmodel.api_choice)

    def _format_buy_plan(self, buy_plan: List[Tuple[float, int]], warning_message: str, summary: Dict[str, Any], reserved_funds: float = 0) -> str:
        """格式化购买计划结果"""
        result = ""
        if warning_message:
            result += warning_message + "\n\n"
        result += "购买计划如下：\n"
        for price, quantity in buy_plan:
            result += f"价格: {price:.2f}, 数量: {quantity}\n"
        
        result += f"\n总购买股数: {summary['total_shares']}\n"
        result += f"总投资成本: {summary['total_cost']:.2f}\n"
        result += f"平均购买价格: {summary['average_price']:.2f}\n"
        result += f"最大潜在亏损: {summary['max_loss']:.2f}\n"
        result += f"最大亏损比例: {summary['max_loss_percentage']:.2f}%\n"
        result += f"选择的分配方式: {summary['allocation_method']}\n"
        
        if reserved_funds > 0:
            result += f"\n保留资金: {reserved_funds:.2f}\n"
        
        return result

    def _handle_calculation_error(self, error_message: str) -> None:
        """处理计算过程中的错误"""
        logger.error(error_message)
        self.viewmodel.display_results(error_message)
        self.viewmodel.update_status("计算失败")

    def update_api_choice(self, api_choice: str) -> None:
        """更新API选择"""
        self.viewmodel.update_api_choice(api_choice)
        self._initialize_api_manager()

    def reset_calculation(self) -> None:
        """重置计算"""
        self.viewmodel.reset()
        self.viewmodel.update_status("计算已重置")
        self.viewmodel.display_results("所有输入已清除。请输入新的参数。")

    def load_config(self) -> None:
        """从配置管理器加载配置"""
        config = self.config_manager.get_config('Trading', {})
        self.viewmodel.update_api_choice(config.get('api_choice', 'yahoo'))
        # 加载其他配置...

    def save_config(self) -> None:
        """保存配置到配置管理器"""
        config = {
            'api_choice': self.viewmodel.api_choice,
            # 保存其他配置...
        }
        self.config_manager.set_config('Trading', config)

    def save_to_csv(self):
        try:
            # 这里实现保存到CSV的逻辑
            # 可以调用 ResultFrame 中的方法来获取结果并保存
            self.main_window.result_frame.save_to_csv()
            self.viewmodel.update_status("结果已保存为CSV文件")
        except Exception as e:
            self.viewmodel.update_status(f"保存CSV文件时发生错误: {str(e)}")
            logger.error(f"保存CSV文件时发生错误: {str(e)}", exc_info=True)

    def update_status(self, message: str) -> None:
        """更新状态栏信息"""
        max_length = 100  # 可以根据需要调整
        if len(message) > max_length:
            message = message[:max_length] + "..."
        self.viewmodel.update_status(message)
        self.main_window.update_status_bar(message)

    def display_results(self, result: str) -> None:
        logger.debug(f"Input result to display_results: {result}")
        
        def update_result_text():
            if not hasattr(self.main_window, 'result_frame'):
                logger.error("result_frame not found in main_window")
                return
            
            result_text = self.main_window.result_frame.result_text
            if not result_text:
                logger.error("result_text widget not found in result_frame")
                return
        
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, result)
            result_text.config(state=tk.DISABLED)
            result_text.see("1.0")  # 滚动到顶部
            
            self.main_window.result_frame.update()
            result_text.update()
            self.main_window.master.update_idletasks()
            
            logger.debug("Results displayed in result_text widget")

        self.main_window.master.after(0, update_result_text)
        
        # 更新状态栏
        first_line = result.split('\n')[0] if result else "无结果"
        self.update_status(first_line)

        # 更新 ViewModel
        self.viewmodel.display_results(result)

    def reset_to_default(self):
        """重置所有设置到默认状态,但保留常用标的和Moomoo设置"""
        logger.info("用户重置为默认值")

        # 获取当前的用户配置
        current_config = self.config_manager.get_user_config()
        # 获取系统默认配置
        system_config = self.config_manager.get_system_config()

        # 重新初始化 user_config
        new_config = {
            'API': {
                'choice': 'yahoo',
                'alpha_vantage_key': current_config.get('API', {}).get('alpha_vantage_key', '')
            },
            'General': {
                'allocation_method': system_config.get('General', {}).get('default_allocation_method', '1'),
            },
            'RecentCalculations': {
                'funds': system_config.get('General', {}).get('default_funds', '10000'),
                'initial_price': system_config.get('General', {}).get('default_initial_price', '100'),
                'stop_loss_price': system_config.get('General', {}).get('default_stop_loss_price', '90'),
                'num_grids': system_config.get('General', {}).get('default_num_grids', '5')
            },
            'CommonStocks': current_config.get('CommonStocks', {}),  # 保留现有的常用标的
            'MoomooSettings': current_config.get('MoomooSettings', {}),  # 保留现有的Moomoo设置
            'MoomooAPI': current_config.get('MoomooAPI', {})  # 保留MoomooAPI设置
        }

        self.config_manager.save_user_config(new_config)
        self.update_ui_from_config(new_config)

        reset_message = "除常用标的和Moomoo设置外,所有设置已重置为默认值"
        self.viewmodel.update_status(reset_message)
        self.viewmodel.display_results(reset_message)
        self._initialize_api_manager()

    def update_ui_from_config(self, config):
        """根据配置更新 UI 组件"""
        self.viewmodel.update_from_config(config)
        self.update_status("UI 已根据配置更新")
        self.main_window.update_from_viewmodel()

    def place_order_by_plan(self):
        if not self._validate_account_access():
            return
        
        # 实现按计划下单的逻辑
        # 使用 self.moomoo_api.place_order 来执行下单
        # 处理下单结果并更新 ViewModel

    def query_positions(self):
        if not self._validate_account_access():
            return
        
        positions = self.moomoo_api.get_positions(self.current_acc_id, self.trade_env, self.market)
        if positions is not None and not positions.empty:
            # 处理持仓信息并更新 ViewModel
            self._display_positions(positions)
        else:
            self.viewmodel.display_results("无法获取持仓信息或没有持仓")

    def query_history_orders(self):
        if not self._validate_account_access():
            return
        
        orders = self.moomoo_api.get_history_orders(self.current_acc_id, self.trade_env, self.market)
        if orders is not None and not orders.empty:
            # 处理历史订单信息并更新 ViewModel
            self._display_history_orders(orders)
        else:
            self.viewmodel.display_results("无法获取历史订单信息或没有历史订单")

    def _display_positions(self, positions: pd.DataFrame):
        # 实现显示持仓信息的逻辑
        pass

    def _display_history_orders(self, orders: pd.DataFrame):
        # 实现显示历史订单的逻辑
        pass

    def check_moomoo_connection(self) -> bool:
        current_env = TrdEnv.REAL if self.viewmodel.trade_mode == "真实" else TrdEnv.SIMULATE
        current_market = TrdMarket.US if self.viewmodel.market == "美股" else TrdMarket.HK

        if not self.moomoo_connected or self.last_connected_env != current_env or self.last_connected_market != current_market:
            result = self.moomoo_api.test_moomoo_connection(current_env, current_market)
            if result:
                self.moomoo_connected = True
                self.last_connected_env = current_env
                self.last_connected_market = current_market
                return True
            else:
                self.main_window.show_warning("未连接", "请先在Moomoo设置中完成测试连接")
                return False
        return True
    
    def enable_real_time_notifications(self):
        if not self.check_moomoo_connection():
            return
        message = "实时通知功能需要注册用户并付费开通。\n根据discord群的喊单记录直接调用解析指令并生成购买计划\n请联系作者了解更多信息。"
        self.viewmodel.display_results(message)
        self.main_window.show_info("实时通知", message)

    def process_trading_instruction(self, instruction: str) -> None:
        """处理交易指令"""
        try:
            current_price = self.api_manager.get_stock_price(self.viewmodel.current_symbol)[0] if self.viewmodel.current_symbol else None
            processed_instruction = self.trading_logic.process_instruction(instruction, current_price)
            self._update_viewmodel_from_instruction(processed_instruction)
            self.run_calculation()
        except TradingLogicError as e:
            self._handle_calculation_error(str(e))
        except Exception as e:
            self._handle_calculation_error(f"处理交易指令时发生错误: {str(e)}")

    def _update_viewmodel_from_instruction(self, processed_instruction: Dict[str, Any]) -> None:
        """根据处理后的指令更新 ViewModel"""
        self.viewmodel.update_from_instruction(processed_instruction)

    def initialize_api_manager(self, api_choice: str, api_key: str = '') -> None:
        self.api_manager.switch_price_api(api_choice)
        if api_choice == 'alpha_vantage':
            self.api_manager.set_alpha_vantage_key(api_key)