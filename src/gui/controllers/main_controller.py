# src/gui/controllers/main_controller.py

import logging
import pandas as pd
from tkinter import messagebox, simpledialog
import tkinter as tk
import time
from typing import Dict, Any, List, Tuple, Optional
from src.utils.error_handler import APIError, TradingLogicError, InputValidationError
from src.utils.gui_helpers import exception_handler
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
        self.trading_logic = TradingLogic(self.config_manager)
        self.api_manager = APIManager()
        self.moomoo_api = self.api_manager.trading.get_current_api()

        # 添加 Moomoo 连接状态追踪
        self.moomoo_connected = False
        self.last_connected_env = None
        self.last_connected_market = None
        self.current_acc_id = None
        self.connection_thread = []

        # 初始化设置
        self.initialize_settings()

    def initialize_settings(self):
        default_config = self.config_manager.get_config('RecentCalculations', {})
        self.viewmodel.update_calculation_inputs(
            total_investment=float(default_config.get('funds', 50000)),
            current_price=float(default_config.get('initial_price', 0)),
            stop_loss_price=float(default_config.get('stop_loss_price', 0)),
            grid_levels=int(default_config.get('num_grids', 5)),
            allocation_method=default_config.get('allocation_method', 1)
        )
        self.viewmodel.api_choice = self.config_manager.get_config('API', {}).get('choice', 'yahoo')

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

    def _validate_account_access(self) -> bool:
        if not self.check_moomoo_connection():
            return False
        if self.current_acc_id is None:
            self.show_calculation_result("无法获取账户信息")
            return False
        return True

    def test_moomoo_connection(self):
        trade_env = TrdEnv.REAL if self.viewmodel.get_trade_env() == "真实" else TrdEnv.SIMULATE
        market = TrdMarket.US if self.viewmodel.get_market() == "美股" else TrdMarket.HK

        try:
            env_str = "真实" if trade_env == TrdEnv.REAL else "模拟"
            market_str = "美股" if market == TrdMarket.US else "港股"
            
            connecting_msg = f"正在连接到 {market_str}（{env_str}环境）..."
            self.update_status(connecting_msg, force_update=True)
            self.show_calculation_result(f"{connecting_msg}\n请稍候...")

            result = self.moomoo_api.test_moomoo_connection(trade_env, market)
            
            if result:
                self.moomoo_connected = True
                self.last_connected_env = trade_env
                self.last_connected_market = market

                # 先发起账户获取
                self.get_current_account()
                
                # 然后更新显示
                success_msg = f"{market_str}（{env_str}环境）连接测试成功"
                self.show_calculation_result(success_msg)
                self.update_status(success_msg, force_update=True)
            else:
                self.moomoo_connected = False
                error_msg = f"{market_str}（{env_str}环境）连接测试失败"
                # 更新状态栏显示失败信息
                self.update_status(error_msg, force_update=True)
                self.show_calculation_result(f"{error_msg}\n\n"
                                        f"可能的原因:\n"
                                        f"1. Moomoo OpenD 未启动或未响应\n"
                                        f"2. 网络连接异常\n"
                                        f"3. API 配置错误\n\n"
                                        f"建议操作:\n"
                                        f"1. 检查并启动 OpenD\n"
                                        f"2. 检查网络连接\n"
                                        f"3. 确认配置正确")
                
                # 尝试清理连接
                self.moomoo_api.stop_all_connections()

        except Exception as e:
            self.moomoo_connected = False
            error_msg = f"连接测试错误: {str(e)}"
            self.update_status("连接测试失败", force_update=True)
            self.show_calculation_result(f"连接测试失败\n\n错误信息: {str(e)}")
            logger.error(error_msg)
            # 发生异常时也尝试清理连接
            self.moomoo_api.stop_all_connections()
    
    def on_closing(self):
        """执行控制器的清理工作"""
        logger.info("开始清理控制器资源...")
        try:
            # 设置停止标志
            if hasattr(self, 'moomoo_api'):
                self.moomoo_api.stop_all_connections()
            
            # 保存配置
            self.save_config()
            
            logger.info("控制器资源清理完成")
        except Exception as e:
            logger.error(f"控制器清理过程中发生错误: {str(e)}")

    @exception_handler
    def run_calculation(self) -> None:
        error_message = self.viewmodel.validate_inputs()
        if error_message:
            messagebox.showerror("输入错误", error_message)
            self.viewmodel.update_status("输入验证失败")
            return

        logger.info("开始运行计算...")
        
        try:
            # 首先检查是否有交易指令
            instruction = self.viewmodel.get_instruction()
            if instruction and instruction != "例：SOXL现价到37.5之间分批买，压力39+，止损36.8":
                logger.info(f"检测到交易指令: {instruction}")
                self.update_status("正在解析交易指令...", force_update=True)
                try:
                    current_price = None
                    if self.viewmodel.current_symbol:
                        current_price = self.api_manager.get_stock_price(self.viewmodel.current_symbol)[0]
                    processed_instruction = self.trading_logic.process_instruction(instruction, current_price)
                    self._update_viewmodel_from_instruction(processed_instruction)
                except Exception as e:
                    logger.error(f"解析交易指令失败: {str(e)}")
                    messagebox.showerror("指令解析错误", str(e))
                    return

            input_values = self.viewmodel.get_input_values()
            logger.debug(f"获取到的输入值中的分配方式: {input_values.get('allocation_method')}")
            input_values['allocation_method'] = int(input_values['allocation_method'])
            logger.debug(f"转换为整数后的分配方式: {input_values['allocation_method']}")
        
            if not self.viewmodel.current_symbol:
                logger.warning("股票代码未设置，使用默认值进行计算")
                self.viewmodel.update_stock_symbol("DEFAULT")

            result = self._prepare_result_header()
            buy_plan, warning_message, summary = self.trading_logic.calculate_buy_plan(**input_values)
            
            calculation_result = self._format_buy_plan(buy_plan, warning_message, summary)
            result += calculation_result
            
            # 保存计算结果用于下单
            self.last_calculation_result = {
                'buy_plan': buy_plan,
                'total_cost': summary.get('total_cost', 0),
                'total_shares': summary.get('total_shares', 0)
            }
            
            self.show_calculation_result(result)
            
            # 更新状态栏消息并锁定
            allocation_methods = {
                0: "等金额分配",
                1: "等比例分配",
                2: "线性加权"
            }
            
            symbol_info = ""
            if self.viewmodel.current_symbol and self.viewmodel.current_symbol != "DEFAULT":
                symbol_info = f" | 标的: {self.viewmodel.current_symbol}"
            
            status_message = f"购买计划计算完成 | {allocation_methods.get(input_values['allocation_method'], '未知')}{symbol_info}"

            self.status_locked = False  # 临时解锁
            self.update_status(status_message)  # 更新状态
            self.status_locked = True  # 重新锁定
            
            logger.debug(f"计算完成，当前股票代码: {self.viewmodel.current_symbol or '无'}")
            
        except (InputValidationError, TradingLogicError, ValueError, FloatingPointError) as e:
            self.status_locked = False
            error_message = str(e)
            logger.error(f"计算过程中发生错误: {error_message}")
            messagebox.showerror("计算错误", error_message)
            self.show_calculation_result(f"计算失败: {error_message}")
            self.viewmodel.update_status("计算失败")

    @exception_handler
    def calculate_with_reserve(self, reserve_percentage: int) -> None:
        """执行保留部分资金的计算"""
        error_message = self.viewmodel.validate_inputs()
        if error_message:
            messagebox.showerror("输入错误", error_message)
            self.viewmodel.update_status("输入验证失败")
            return

        logger.info(f"开始计算（保留{reserve_percentage}%资金）...")
        
        try:
            # 首先检查是否有交易指令
            instruction = self.viewmodel.get_instruction()
            if instruction and instruction != "例：SOXL现价到37.5之间分批买，压力39+，止损36.8":
                logger.info(f"检测到交易指令: {instruction}")
                self.update_status("正在解析交易指令...", force_update=True)
                try:
                    current_price = None
                    if self.viewmodel.current_symbol:
                        current_price = self.api_manager.get_stock_price(self.viewmodel.current_symbol)[0]
                    processed_instruction = self.trading_logic.process_instruction(instruction, current_price)
                    self._update_viewmodel_from_instruction(processed_instruction)
                except Exception as e:
                    logger.error(f"解析交易指令失败: {str(e)}")
                    messagebox.showerror("指令解析错误", str(e))
                    return

            input_values = self.viewmodel.get_input_values()
            logger.debug(f"获取到的输入值中的分配方式: {input_values.get('allocation_method')}")
            input_values['allocation_method'] = int(input_values['allocation_method'])
            logger.debug(f"转换为整数后的分配方式: {input_values['allocation_method']}")
            
            # 计算保留资金
            total_funds = input_values['funds']
            reserved_funds = total_funds * (reserve_percentage / 100)
            available_funds = total_funds - reserved_funds
            
            # 更新可用资金
            input_values['funds'] = available_funds
            
            result = self._prepare_result_header(with_reserve=True, reserve_percentage=reserve_percentage)
            buy_plan, warning_message, summary = self.trading_logic.calculate_buy_plan(**input_values)
            
            calculation_result = self._format_buy_plan(buy_plan, warning_message, summary, reserved_funds)
            result += calculation_result
            
            # 保存计算结果用于下单
            self.last_calculation_result = {
                'buy_plan': buy_plan,
                'total_cost': summary.get('total_cost', 0),
                'total_shares': summary.get('total_shares', 0)
            }
            
            self.show_calculation_result(result)
            
            # 更新状态栏消息并锁定
            allocation_methods = {
                0: "等金额分配",
                1: "等比例分配",
                2: "线性加权"
            }
            
            symbol_info = ""
            if self.viewmodel.current_symbol and self.viewmodel.current_symbol != "DEFAULT":
                symbol_info = f" | 标的: {self.viewmodel.current_symbol}"
            
            # 在计算完成后更新状态
            allocation_method = allocation_methods.get(input_values['allocation_method'], '未知')
            status_message = f"购买计划计算完成 | {allocation_method} | 保留{reserve_percentage}%资金{symbol_info}"

            self.status_locked = False  # 临时解锁
            self.update_status(status_message)  # 更新状态
            self.status_locked = True  # 重新锁定
            
            logger.debug(f"计算完成（保留{reserve_percentage}%资金），当前股票代码: {self.viewmodel.current_symbol or '无'}")
                
        except (InputValidationError, TradingLogicError, ValueError, FloatingPointError) as e:
            self.status_locked = False
            error_message = str(e)
            logger.error(f"计算过程中发生错误: {error_message}")
            messagebox.showerror("计算错误", error_message)
            self.show_calculation_result(f"计算失败: {error_message}")
            self.viewmodel.update_status("计算失败")
            
    def _validate_inputs(self) -> None:
        """验证输入值"""
        error_message = self.viewmodel.validate_inputs()
        if error_message:
            raise InputValidationError(error_message)

    def _prepare_result_header(self, with_reserve=False, reserve_percentage=0) -> str:
        """准备结果头部信息"""
        result = ""
        if self.viewmodel.current_symbol:
            result += f"标的: {self.viewmodel.current_symbol}\n"
            logger.info(f"计算购买计划，标的: {self.viewmodel.current_symbol}")
        else:
            logger.warning("当前没有设置标的")
            result += "注意: 未设置标的，使用默认参数计算\n"
        
        input_values = self.viewmodel.get_input_values()
        total_funds = input_values['funds']
        
        if with_reserve:
            reserved_funds = total_funds * (reserve_percentage / 100)
            available_funds = total_funds - reserved_funds
            result += (f"总资金: {total_funds:.2f} | "
                    f"保留资金: {reserved_funds:.2f} | "
                    f"可用资金: {available_funds:.2f}\n")
        else:
            result += (f"总资金: {total_funds:.2f} | "
                    f"可用资金: {total_funds:.2f}\n")
        
        result += (f"初始价格: {input_values['initial_price']:.2f} | "
                f"止损价格: {input_values['stop_loss_price']:.2f} | "
                f"网格数量: {input_values['num_grids']}\n")
        return result

    def set_stock_price(self, symbol: str) -> None:
        logger.info(f"开始设置股票价格，标的: {symbol}")
        
        # 立即更新状态栏和用户提示区
        status_msg = f"正在查询 {symbol} 的实时价格..."
        self.update_status(status_msg, force_update=True)
        self.show_calculation_result(f"{status_msg}\n\n正在从 {self.viewmodel.api_choice} 获取最新价格，请稍候...")
        
        # 强制更新UI
        self.main_window.master.update()
        
        if self.viewmodel.api_choice != self.api_manager.current_price_api:
            self._initialize_api_manager()

        try:
            current_price, api_used = self.api_manager.get_stock_price(symbol)
            current_price = round(current_price, 2)
            self._update_price_fields(symbol, current_price, api_used)
            
            # 确保更新 UI
            self.main_window.right_frame.update_fields({
                'initial_price': current_price,
                'stop_loss_price': round(current_price * 0.9, 2)
            })
            
        except APIError as e:
            self._handle_price_query_error(str(e), symbol)
        except Exception as e:
            self._handle_price_query_error(f"获取股票价格时发生未知错误: {str(e)}", symbol)

    def _update_price_fields(self, symbol: str, current_price: float, api_used: str) -> None:
        if not current_price:
            raise APIError(f"无法从 {api_used} 获取有效的价格数据")
            
        current_price = round(current_price, 2)
        stop_loss_price = round(current_price * 0.9, 2)
        self.viewmodel.update_price_fields(symbol, current_price, stop_loss_price)
        
        logger.info(f"更新价格字段，标的: {symbol}, 当前价格: {current_price:.2f}, 止损价格: {stop_loss_price:.2f}")
        
        # 更新状态栏消息
        status_message = f"已选择标的 {symbol}，当前价格: {current_price:.2f} 元，止损价格: {stop_loss_price:.2f} 元 (来自 {api_used})"
        self.update_status(status_message)  # 使用 controller 的 update_status 方法
        
        result_message = (
            f"选中标的: {symbol}\n"
            f"当前价格: {current_price:.2f} 元 (来自 {api_used})\n"
            f"止损价格: {stop_loss_price:.2f} 元 (按90%当前价格计算)\n\n"
            f"初始价格和止损价格已更新。您可以直接点击\"计算购买计划\"按钮或调整其他参数。"
        )
        self.show_calculation_result(result_message)

    def _handle_price_query_error(self, error_message: str, symbol: str) -> None:
        """处理股票价格查询相关的API错误"""
        full_error_message = (f"无法获取标的 {symbol} 的价格\n\n"
                            f"错误信息: {error_message}\n\n"
                            f"建议检查网络连接、API key 是否有效，或尝试切换到其他 API。")
        self.update_status(error_message)
        self.show_calculation_result(full_error_message)
        logger.error(error_message)
        self.viewmodel.current_symbol = symbol  # 即使获取价格失败，也设置当前标的

    def _handle_trading_error(self, error_message: str, operation: str, show_details: bool = True) -> None:
        """统一的交易相关错误处理
        
        Args:
            error_message: 错误信息
            operation: 操作类型描述
            show_details: 是否显示详细错误信息
        """
        full_error_message = f"{operation}时发生错误: {error_message}"
        if show_details:
            full_error_message += "\n\n建议检查:\n1. 网络连接\n2. API状态\n3. 账户权限"
            
        logger.error(full_error_message)
        self.show_calculation_result(full_error_message)
        self.update_status(f"{operation}失败")

    def _initialize_api_manager(self) -> None:
        """初始化API管理器"""
        self.api_manager.switch_price_api(self.viewmodel.api_choice)

    def _format_buy_plan(self, buy_plan: List[Tuple[float, int]], warning_message: str, summary: Dict[str, Any], reserved_funds: float = 0) -> str:
        result = ""
        if warning_message:
            result += warning_message + "\n\n"
        result += "购买计划如下：\n"
        
        try:
            for price, quantity in buy_plan:
                result += f"价格: {price:.2f}, 数量: {quantity}\n"
            
            result += f"\n总购买股数: {summary.get('total_shares', 0)}\n"
            result += f"总投资成本: {summary.get('total_cost', 0):.2f}\n"
            result += f"平均购买价格: {summary.get('average_price', 0):.2f}\n"
            result += f"最大潜在亏损: {summary.get('max_loss', 0):.2f}\n"
            result += f"最大亏损比例: {summary.get('max_loss_percentage', 0):.2f}%\n"
            result += f"选择的分配方式: {summary.get('allocation_method_name', '未知')}\n"
            
            if reserved_funds > 0:
                result += f"\n保留资金: {reserved_funds:.2f}\n"
            
        except Exception as e:
            logger.error(f"格式化购买计划时发生错误: {str(e)}")
            logger.debug(f"buy_plan: {buy_plan}")
            logger.debug(f"summary: {summary}")
            result += f"\n格式化结果时发生错误: {str(e)}\n"
        
        return result

    def update_api_choice(self, api_choice: str) -> None:
        """更新API选择"""
        self.viewmodel.update_api_choice(api_choice)
        self._initialize_api_manager()

    def reset_calculation(self) -> None:
        """重置计算"""
        self.viewmodel.reset()
        self.update_status("计算已重置")
        self.show_calculation_result("所有输入已清除。请输入新的参数。")

    def save_config(self):
        """保存配置到配置管理器"""
        try:
            # 保存通用配置
            general_config = {
                'allocation_method': self.viewmodel.allocation_method,
                'max_num_grids': 10
            }
            self.config_manager.set_config('General', general_config)
            
            # 保存 API 配置
            api_config = {
                'choice': self.viewmodel.api_choice
            }
            self.config_manager.set_config('API', api_config)
            
            # 保存最近的计算配置
            recent_calc = {
                'funds': str(self.viewmodel.total_investment),
                'initial_price': str(self.viewmodel.current_price),
                'stop_loss_price': str(self.viewmodel.stop_loss_price),
                'num_grids': str(self.viewmodel.grid_levels)
            }
            self.config_manager.set_config('RecentCalculations', recent_calc)
            
            # 立即保存到文件
            self.config_manager.save_user_config()
            logger.info("用户配置已保存")
        except Exception as e:
            logger.error(f"保存配置时发生错误: {str(e)}")

    def load_config(self) -> None:
        """从配置管理器加载配置"""
        try:
            # 加载通用配置
            general_config = self.config_manager.get_config('General', {})
            # 先尝试获取用户配置中的 allocation_method，如果没有则使用默认值
            allocation_method = int(general_config.get('allocation_method', 1))
            self.viewmodel.update_allocation_method(allocation_method)
            
            # 加载 API 配置
            api_config = self.config_manager.get_config('API', {})
            self.viewmodel.update_api_choice(api_config.get('choice', 'yahoo'))
            
            # 加载最近的计算配置
            recent_calc = self.config_manager.get_config('RecentCalculations', {})
            if recent_calc:
                self.viewmodel.update_calculation_inputs(
                    total_investment=float(recent_calc.get('funds', 50000)),
                    current_price=float(recent_calc.get('initial_price', 100)),
                    stop_loss_price=float(recent_calc.get('stop_loss_price', 90)),
                    grid_levels=int(recent_calc.get('num_grids', 10)),
                    allocation_method=allocation_method
                )
            logger.info("配置已加载")
        except Exception as e:
            logger.error(f"加载配置时发生错误: {str(e)}")
                
    def save_user_settings(self):
        self.config_manager.save_user_config()

    def save_to_csv(self):
        try:
            self.main_window.result_frame.save_to_csv()
            self.update_status("结果已保存为CSV文件")
        except Exception as e:
            self.update_status(f"保存CSV文件时发生错误: {str(e)}")
            logger.error(f"保存CSV文件时发生错误: {str(e)}", exc_info=True)

    def update_status(self, message: str, force_update: bool = False) -> None:
        """
        更新状态栏和viewmodel的状态信息
        
        :param message: 状态消息
        :param force_update: 是否强制更新状态栏，即使状态被锁定
        """
        try:
            max_length = 100
            if len(message) > max_length:
                message = message[:max_length] + "..."
            
            # 检查状态锁定
            if hasattr(self, 'status_locked') and self.status_locked and not force_update:
                logger.debug(f"状态栏已锁定，忽略更新: {message}")
                return
                
            if hasattr(self.main_window, 'status_bar'):
                self.main_window.update_status_bar(message)
            else:
                logger.warning("状态栏组件未初始化")
                
        except Exception as e:
            logger.error(f"更新状态栏时发生错误: {str(e)}")

    def show_calculation_result(self, result: str) -> None:
        """显示计算结果到UI并更新ViewModel状态"""
        try:
            # 1. 更新 ViewModel 状态
            self.viewmodel.display_results(result)
            
            # 2. 更新 UI
            def update_ui():
                if hasattr(self.main_window, 'result_frame'):
                    if hasattr(self.main_window.result_frame, 'result_text'):
                        self.main_window.result_frame.display_results(result)
                        # 更新状态栏
                        first_line = result.split('\n')[0] if result else "无结果"
                        self.update_status(first_line)
            
            # 在主线程中执行UI更新
            self.main_window.master.after(0, update_ui)
            
        except Exception as e:
            logger.error(f"显示计算结果时发生错误: {str(e)}")
            self.update_status(f"显示结果失败: {str(e)}")

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
                'allocation_method': int(system_config.get('General', {}).get('default_allocation_method', 1)),
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
        
        # 更新 UI
        self.main_window.right_frame.set_default_values(
            funds=new_config['RecentCalculations']['funds'],
            initial_price=new_config['RecentCalculations']['initial_price'],
            stop_loss_price=new_config['RecentCalculations']['stop_loss_price'],
            num_grids=new_config['RecentCalculations']['num_grids'],
            allocation_method=new_config['General']['allocation_method']
        )
        
        reset_message = "除常用标的和Moomoo设置外,所有设置已重置为默认值"
        self.update_status(reset_message)
        self.show_calculation_result(reset_message)
        self._initialize_api_manager()

    def update_ui_from_config(self, config):
        """根据配置更新 UI 组件"""
        self.viewmodel.update_from_config(config)
        self.update_status("UI 已根据配置更新")
        self.main_window.update_from_viewmodel()

    def place_order_by_plan(self):
        if not self._validate_account_access():
            return
        
        if not hasattr(self, 'last_calculation_result') or not self.last_calculation_result:
            messagebox.showwarning("提示", "请先计算购买计划")
            return
            
        try:
            self.update_status("正在执行购买计划...", force_update=True)
            
            plan = self.last_calculation_result.get('buy_plan', [])
            if not plan:
                messagebox.showwarning("提示", "没有可执行的购买计划")
                return
                
            # 显示确认对话框
            result = messagebox.askyesno("确认下单", 
                f"是否确认按照计划下单？\n"
                f"标的: {self.viewmodel.current_symbol}\n"
                f"总价格: {self.last_calculation_result.get('total_cost', 0):.2f}\n"
                f"总数量: {self.last_calculation_result.get('total_shares', 0)}")
                
            if result:
                # 执行下单逻辑
                for price, quantity in plan:
                    order_result = self.moomoo_api.place_order(
                        self.current_acc_id,
                        self.viewmodel.current_symbol,
                        quantity,
                        price
                    )
                    # 处理下单结果...
                    
                self.update_status("下单完成", force_update=True)
            else:
                self.update_status("已取消下单", force_update=True)
                
        except Exception as e:
            error_msg = f"下单执行失败: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
            self.update_status("下单失败", force_update=True)

    def query_available_funds(self):
        try:
            if not self._validate_account_access():
                return
                
            current_env = TrdEnv.REAL if self.viewmodel.get_trade_env() == "真实" else TrdEnv.SIMULATE
            current_market = TrdMarket.US if self.viewmodel.get_market() == "美股" else TrdMarket.HK
            
            info = self.moomoo_api.get_account_info(
                acc_id=self.current_acc_id,
                trade_env=current_env,
                market=current_market
            )
            
            if info:
                self._display_account_info(info)
            else:
                self.main_window.result_frame.display_results("无法获取账户资金信息")
                self.update_status("资金查询失败")
                
        except Exception as e:
            self._handle_trading_error(str(e), "查询账户资金")

    def query_positions(self):
        try:
            if not self._validate_account_access():
                return
                
            current_env = TrdEnv.REAL if self.viewmodel.get_trade_env() == "真实" else TrdEnv.SIMULATE
            current_market = TrdMarket.US if self.viewmodel.get_market() == "美股" else TrdMarket.HK
            
            positions = self.moomoo_api.get_positions(
                acc_id=self.current_acc_id,
                trade_env=current_env,
                market=current_market
            )
            
            self._display_positions(positions)
                
        except Exception as e:
            self._handle_trading_error(str(e), "查询持仓")

    def query_history_orders(self):
        try:
            if not self._validate_account_access():
                return
                
            current_env = TrdEnv.REAL if self.viewmodel.get_trade_env() == "真实" else TrdEnv.SIMULATE
            current_market = TrdMarket.US if self.viewmodel.get_market() == "美股" else TrdMarket.HK
            
            orders = self.moomoo_api.get_history_orders(
                acc_id=self.current_acc_id,
                trade_env=current_env,
                market=current_market,
                include_cancelled=True,
                days=30
            )
            
            self._display_history_orders(orders)
                
        except Exception as e:
            self._handle_trading_error(str(e), "查询历史订单")

    def _display_account_info(self, info: Dict[str, Any]) -> None:
        try:
            env_str = self.viewmodel.get_trade_env()
            market_str = self.viewmodel.get_market()
            
            result = f"当前连接: {market_str}（{env_str}环境）\n"
            result += f"账户 {self.current_acc_id} 资金情况:\n\n"
            
            # 格式化金额显示
            fields = [
                ("总资产", 'total_assets'),
                ("现金", 'cash'),
                ("证券市值", 'securities_assets'),
                ("购买力", 'power'),
                ("最大购买力", 'max_power_short'),
                ("币种", 'currency')
            ]
            
            for label, key in fields:
                if key in info and info[key] not in ['', 'N/A']:
                    value = info[key]
                    if isinstance(value, (int, float)) and key != 'currency':
                        result += f"{label}: ${value:,.2f}\n"
                    else:
                        result += f"{label}: {value}\n"
            
            self.show_calculation_result(result)
            self.update_status(f"{market_str}（{env_str}环境）资金查询完成")
        except Exception as e:
            self._handle_trading_error(str(e), "显示账户信息")

    def _display_positions(self, positions: Optional[List[Dict[str, Any]]]) -> None:
        try:
            env_str = self.viewmodel.get_trade_env()
            market_str = self.viewmodel.get_market()
            
            result = f"当前连接: {market_str}（{env_str}环境）\n"
            result += f"账户 {self.current_acc_id} 持仓情况:\n\n"
            
            if positions:
                # 添加表头
                result += "{:<5}{:<10}{:<12}{:<15}{:<15}{:<15}\n".format(
                    "序号", "代码", "数量", "市值($)", "成本价", "盈亏比例(%)"
                )
                result += "-" * 75 + "\n"
                
                # 按市值降序排序
                sorted_positions = sorted(positions, key=lambda x: float(x.get('market_val', 0)), reverse=True)
                
                for i, pos in enumerate(sorted_positions, 1):
                    result += "{:<5}{:<10}{:<12,.2f}{:<15,.2f}{:<15,.2f}{:<15,.2f}\n".format(
                        i,
                        pos.get('code', 'N/A'),
                        float(pos.get('qty', 0)),
                        float(pos.get('market_val', 0)),
                        float(pos.get('cost_price', 0)),
                        float(pos.get('pl_ratio', 0))
                    )
            else:
                result += "当前账户没有持仓"
            
            self.main_window.result_frame.display_results(result)
            status_message = f"{market_str}（{env_str}环境）{'持仓查询完成' if positions else '无持仓'}"
            self.update_status(status_message)
            
        except Exception as e:
            self._handle_trading_error(str(e), "显示持仓信息")

    def _display_history_orders(self, orders: Optional[List[Dict[str, Any]]]) -> None:
        try:
            env_str = self.viewmodel.get_trade_env()
            market_str = self.viewmodel.get_market()
            
            result = f"当前连接: {market_str}（{env_str}环境）\n"
            result += f"账户 {self.current_acc_id} 历史订单:\n"
            result += f"总订单数: {len(orders) if orders else 0}\n"
            result += "显示最近30天内的订单（最多显示20笔）:\n\n"
            
            if orders:
                result += "{:<5}{:<10}{:<12}{:<15}{:<15}{:<15}\n".format(
                    "序号", "代码", "方向", "数量", "价格", "创建日期"
                )
                result += "-" * 75 + "\n"
                
                # 按日期降序排序并限制显示数量
                sorted_orders = sorted(orders, 
                                key=lambda x: x.get('create_time', ''), 
                                reverse=True)[:20]
                
                for i, order in enumerate(sorted_orders, 1):
                    create_time = pd.to_datetime(order.get('create_time', ''))
                    formatted_date = create_time.strftime('%Y-%m-%d')
                    
                    result += "{:<5}{:<10}{:<12}{:<15,.2f}{:<15,.2f}{:<15}\n".format(
                        i,
                        order.get('code', 'N/A'),
                        order.get('trd_side', 'N/A'),
                        float(order.get('qty', 0)),
                        float(order.get('price', 0)),
                        formatted_date
                    )
            else:
                result += "没有历史订单记录"
            
            self.main_window.result_frame.display_results(result)
            status_message = f"{market_str}（{env_str}环境）{'历史订单查询完成' if orders else '无历史订单'}"
            self.update_status(status_message)
            
        except Exception as e:
            self._handle_trading_error(str(e), "显示历史订单")
            
    def check_moomoo_connection(self) -> bool:
        try:
            # 确保从 viewmodel 获取最新的设置
            trade_env_str = self.viewmodel.get_trade_env()
            market_str = self.viewmodel.get_market()
            
            current_env = TrdEnv.REAL if trade_env_str == "真实" else TrdEnv.SIMULATE
            current_market = TrdMarket.US if market_str == "美股" else TrdMarket.HK

            if not self.moomoo_connected or self.last_connected_env != current_env or self.last_connected_market != current_market:
                result = self.moomoo_api.test_moomoo_connection(current_env, current_market)
                if result:
                    self.moomoo_connected = True
                    self.last_connected_env = current_env
                    self.last_connected_market = current_market
                    
                    # 获取账户列表
                    acc_list = self.moomoo_api.get_acc_list(current_env, current_market)
                    if acc_list is not None:
                        if isinstance(acc_list, dict) and 'acc_id' in acc_list:
                            self.current_acc_id = acc_list['acc_id'].get(0)
                            return True if self.current_acc_id else False
                        
                    self.main_window.show_warning("无法获取账户", "未能获取到账户列表")
                    return False
                else:
                    self.main_window.show_warning("未连接", "请先在Moomoo设置中完成测试连接")
                    return False
            return True
            
        except Exception as e:
            logger.error(f"检查Moomoo连接时发生错误: {str(e)}")
            self.main_window.show_warning("连接错误", f"检查Moomoo连接时发生错误: {str(e)}")
            return False

    def enable_real_time_notifications(self):
        if not self.check_moomoo_connection():
            return
        message = "实时通知功能需要注册用户并付费开通。\n根据discord群的喊单记录直接调用解析指令并生成购买计划\n请联系作者了解更多信息。"
        self.show_calculation_result(message)
        self.main_window.show_info("实时通知", message)

    def process_trading_instruction(self, instruction: str) -> None:
        """处理交易指令"""
        try:
            current_price = self.api_manager.get_stock_price(self.viewmodel.current_symbol)[0] if self.viewmodel.current_symbol else None
            processed_instruction = self.trading_logic.process_instruction(instruction, current_price)
            self._update_viewmodel_from_instruction(processed_instruction)
            self.run_calculation()
        except TradingLogicError as e:
            self._handle_trading_error(str(e), "处理交易指令")
        except Exception as e:
            self._handle_trading_error(str(e), "处理交易指令")

    def _update_viewmodel_from_instruction(self, processed_instruction: Dict[str, Any]) -> None:
        """根据处理后的指令更新 ViewModel"""
        self.viewmodel.update_from_instruction(processed_instruction)

    def initialize_api_manager(self, api_choice: str, api_key: str = '') -> None:
        self.api_manager.switch_price_api(api_choice)
        if api_choice == 'alpha_vantage':
            self.api_manager.set_alpha_vantage_key(api_key)

    def update_force_simulate_mode(self, state: str) -> None:
        self.update_status(f"已{state}强制模拟模式")