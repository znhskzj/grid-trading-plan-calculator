# src/gui.py

from __future__ import annotations
import csv
import logging
import os
import time
import json
import threading
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List
from moomoo import TrdEnv, TrdMarket, TrdSide

# 更新 API 相关的导入
from src.api_manager import APIManager, APIError
from src.calculations import (
    run_calculation, 
    calculate_with_reserve,
    parse_trading_instruction, 
    validate_inputs 
)
from src.config import save_user_config, load_user_config, load_system_config, DEFAULT_USER_CONFIG
from src.status_manager import StatusManager
from src.utils import exception_handler, compare_versions, get_latest_version, get_project_root

# 更新 Moomoo API 相关的导入
from src.api_interface import MoomooAPI

logger = logging.getLogger(__name__)

def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class App:
    """
    Grid Trading Tool 的主应用类。
    管理GUI界面和用户交互。
    """
    force_simulate: bool
    DEFAULT_WINDOW_WIDTH = 750
    DEFAULT_WINDOW_HEIGHT = 700

    def __init__(self, master: tk.Tk, config: Dict[str, Any], version: str):
        """
        初始化应用。

        :param master: Tkinter 主窗口
        :param config: 应用配置
        :param version: 应用版本
        """
        self.master = master
        self.system_config = config
        self.version = version
        self.is_closing = False
        self.current_symbol = None
        self.status_bar = None

        self.load_configurations()
        self.ensure_config_structure()
        self.setup_variables()
        self.create_widgets()
        self.setup_layout()
        self.initialize_api_manager()

        App.instance = self
        self.status_manager = self
        StatusManager.set_instance(self)
        
        self.setup_window_properties()
        self.load_user_settings()
        
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.master.title(f"Grid Trading Tool v{self.version}")
        
        # Moomoo API related initializations
        self.trade_env = None
        self.market = None
        self.moomoo_connected = False
        self.last_connected_env = None
        self.last_connected_market = None
        self.moomoo_api = MoomooAPI()
        self.current_acc_id = None
        self.force_simulate = True
        
        # Connection thread management
        self.connection_thread = None
        self.stop_connection_attempts = threading.Event()

    def ensure_config_structure(self):
        for section, values in DEFAULT_USER_CONFIG.items():
            if section not in self.user_config:
                self.user_config[section] = {}
            for key, default_value in values.items():
                if key not in self.user_config[section]:
                    self.user_config[section][key] = default_value

    def load_configurations(self):
            """加载用户配置和系统配置"""
            self.system_config = load_system_config()
            self.user_config = load_user_config()
            if not self.user_config:
                self.user_config = DEFAULT_USER_CONFIG.copy()
                save_user_config(self.user_config)
            
            # 如果用户配置中没有常用标的，则使用系统配置中的默认标的
            if 'CommonStocks' not in self.user_config or not self.user_config['CommonStocks']:
                self.user_config['CommonStocks'] = self.system_config.get('DefaultCommonStocks', {})
                save_user_config(self.user_config)
            
            self.available_apis = self.parse_available_apis()

    def parse_available_apis(self):
        """解析可用的API列表"""
        apis = self.system_config.get('AvailableAPIs', {}).get('apis', ['yahoo', 'alpha_vantage'])
        if isinstance(apis, str):
            apis = apis.split(',')
        return list(dict.fromkeys(apis))  # 去重

    def setup_variables(self):
        """设置GUI变量"""
        self.api_choice = tk.StringVar(value=self.user_config['API']['choice'])
        self.alpha_vantage_key = tk.StringVar(value=self.user_config['API']['alpha_vantage_key'])
        self.instruction_var = tk.StringVar()
        self.trade_mode_var = tk.StringVar(value=self.user_config['MoomooSettings']['trade_mode'])
        self.market_var = tk.StringVar(value=self.user_config['MoomooSettings']['market'])

        general_config = self.user_config['General']
        recent_calc = self.user_config['RecentCalculations']

        self.funds_var = tk.StringVar(value=recent_calc['funds'])
        self.initial_price_var = tk.StringVar(value=recent_calc['initial_price'])
        self.stop_loss_price_var = tk.StringVar(value=recent_calc['stop_loss_price'])
        self.num_grids_var = tk.StringVar(value=recent_calc['num_grids'])
        self.allocation_method_var = tk.StringVar(value=general_config['allocation_method'])

    def open_user_config(self):
        UserConfigWindow(self.master, self.user_config)

    def handle_gui_error(self, message: str, exception: Exception) -> None:
        """处理 GUI 创建过程中的错误"""
        error_msg = f"{message}: {str(exception)}"
        logger.error(error_msg, exc_info=True)
        messagebox.showerror("GUI 错误", error_msg)

    def create_widgets(self) -> None:
        """创建并布局所有GUI组件"""
        self.ensure_attributes()
        try:
            self.create_main_frame()
            self.create_status_bar()
            self.create_left_frame()
            self.create_right_frame()
            self.create_result_frame()
        except Exception as e:
            self.handle_gui_error("创建GUI组件时发生错误", e)

    def create_main_frame(self):
        """创建主框架"""
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Label(self.master, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

    def create_left_frame(self):
        """创建左侧框架"""
        self.left_frame = ttk.Frame(self.main_frame, width=120)
        self.left_frame.grid(row=0, column=0, sticky="ns")
        self.left_frame.grid_propagate(False)
        self.create_left_widgets()

    def create_right_frame(self):
        """创建右侧框架"""
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.right_frame.grid_columnconfigure(1, weight=1)
        self.create_right_widgets()

    def create_result_frame(self):
        """创建结果显示区域"""
        self.result_frame = ttk.Frame(self.main_frame, relief=tk.SUNKEN, borderwidth=1)
        self.result_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10), padx=10)
        
        text_container = ttk.Frame(self.result_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.result_text = tk.Text(text_container, height=20, wrap=tk.WORD)  # 修改：增加 height 值
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_text.yview)

    def create_left_widgets(self):
        """创建左侧组件"""
        self.common_stocks_button = ttk.Button(self.left_frame, text="常用标的", width=10, command=self.toggle_common_stocks)
        self.common_stocks_button.pack(pady=(0, 5))

        self.common_stocks_frame = ttk.Frame(self.left_frame)
        self.common_stocks_frame.pack(fill=tk.Y, expand=True)
        common_stocks = self.user_config.get('CommonStocks', {})
        self.update_common_stocks(common_stocks)
        
    def toggle_common_stocks(self):
        """切换常用标的的显示状态"""
        if self.common_stocks_frame.winfo_viewable():
            self.common_stocks_frame.pack_forget()
            self.common_stocks_button.config(text="显示常用标的")
        else:
            self.common_stocks_frame.pack(fill=tk.Y, expand=True)
            self.common_stocks_button.config(text="隐藏常用标的")

    def update_common_stocks(self, stocks):
        """更新常用股票列表"""
        for widget in self.common_stocks_frame.winfo_children():
            widget.destroy()
        
        if isinstance(stocks, dict):
            stocks = stocks.values()
        
        for symbol in stocks:
            if symbol and symbol.strip():
                btn = ttk.Button(self.common_stocks_frame, text=symbol.strip(), width=10,
                                command=lambda s=symbol.strip(): self.set_stock_price(s))
                btn.pack(pady=2)
        
        # 确保常用标的按钮显示正确的文本
        if self.common_stocks_frame.winfo_children():
            self.common_stocks_button.config(text="隐藏常用标的")
        else:
            self.common_stocks_button.config(text="显示常用标的")

    def create_right_widgets(self) -> None:
        """创建右侧组件"""
        self.create_input_fields()
        self.create_option_frame()
        self.create_buttons()

    def create_input_fields(self) -> None:
        """创建输入字段"""
        labels = ["可用资金:", "初始价格:", "止损价格:", "网格数量:", "交易指令:"]
        vars = [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var, self.instruction_var]

        for i, (label, var) in enumerate(zip(labels, vars)):
            ttk.Label(self.right_frame, text=label).grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(self.right_frame, textvariable=var, width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=(5, 0), pady=2)
            
            # 为交易指令输入框增加特性
            if label == "交易指令:":
                entry.config(width=50)  # 增加宽度
                entry.grid(columnspan=2)  # 跨两列
                
                # 添加提示信息
                entry.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
                entry.config(foreground="gray")
                
                def on_entry_click(event):
                    if entry.get() == "例：SOXL现价到37.5之间分批买，压力39+，止损36.8":
                        entry.delete(0, "end")
                        entry.config(foreground="black")
                
                def on_focusout(event):
                    if entry.get() == "":
                        entry.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
                        entry.config(foreground="gray")
                
                entry.bind('<FocusIn>', on_entry_click)
                entry.bind('<FocusOut>', on_focusout)

    def create_option_frame(self) -> None:
        """创建选项框架"""
        option_frame = ttk.Frame(self.right_frame)
        option_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        option_frame.grid_columnconfigure(0, weight=2)
        option_frame.grid_columnconfigure(1, weight=1)
        option_frame.grid_columnconfigure(2, weight=1)
        
        self.create_allocation_method_widgets(option_frame)
        self.create_api_widgets(option_frame)
        self.create_moomoo_settings(option_frame)

    def create_allocation_method_widgets(self, parent_frame):
        """创建分配方式组件"""
        allocation_frame = ttk.LabelFrame(parent_frame, text="分配方式")
        allocation_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        methods = [("等金额分配", "0", "均匀分配资金"),
                   ("等比例分配", "1", "指数增长分配"),
                   ("线性加权", "2", "线性增长分配")]

        for i, (text, value, desc) in enumerate(methods):
            ttk.Radiobutton(allocation_frame, text=text, variable=self.allocation_method_var, value=value).grid(row=i, column=0, sticky="w")
            ttk.Label(allocation_frame, text=desc).grid(row=i, column=1, sticky="w", padx=(10, 0))

    def create_buttons(self) -> None:
        """创建按钮"""
        button_frame = ttk.Frame(self.right_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(10, 0), sticky='ew')

        buttons = [
            ("计算购买计划", self.run_calculation),
            ("保留10%计算", lambda: self.calculate_with_reserve(10)),
            ("保留20%计算", lambda: self.calculate_with_reserve(20)),
            ("保存为CSV", self.save_to_csv),
            ("重置为默认值", self.reset_to_default)
        ]

        for i, (text, command) in enumerate(buttons):
            ttk.Button(button_frame, text=text, command=command).grid(row=0, column=i, padx=5, pady=(0, 5))

        # 添加分割线
        separator = ttk.Separator(self.right_frame, orient='horizontal')
        separator.grid(row=9, column=0, columnspan=2, sticky='ew', pady=5)  # 修改：调整位置和跨度

        # 创建第二行按钮
        second_row_buttons = [
            ("查询可用资金", self.query_available_funds),
            ("查询持仓股票", self.query_positions),
            ("按标的计划下单", self.place_order_by_plan),
            ("查询历史订单", self.query_history_orders),
            ("开启实时通知", self.enable_real_time_notifications)
        ]

        for i, (text, command) in enumerate(second_row_buttons):
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=1, column=i, padx=5, pady=(5, 0))
            
    def create_api_widgets(self, parent_frame):
        """创建API选择组件"""
        api_frame = ttk.LabelFrame(parent_frame, text="API 选择")
        api_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        if not self.available_apis:
            logger.error("没有可用的 API")
            ttk.Label(api_frame, text="无可用 API").grid(row=0, column=0, sticky="w")
            return

        for i, api in enumerate(self.available_apis):
            display_name = "Yahoo" if api.lower() == "yahoo" else "Alpha Vantage"
            ttk.Radiobutton(api_frame, text=display_name, variable=self.api_choice, 
                            value=api, command=self.on_api_change).grid(row=i, column=0, sticky="w")

    def create_moomoo_settings(self, parent_frame):
        """创建Moomoo设置组件"""
        moomoo_frame = ttk.LabelFrame(parent_frame, text="Moomoo设置")
        moomoo_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)

        self.real_radio = ttk.Radiobutton(moomoo_frame, text="真实", variable=self.trade_mode_var, value="真实")
        self.real_radio.grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(moomoo_frame, text="模拟", variable=self.trade_mode_var, value="模拟").grid(row=0, column=1, sticky="w")

        ttk.Radiobutton(moomoo_frame, text="美股", variable=self.market_var, value="美股").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(moomoo_frame, text="港股", variable=self.market_var, value="港股").grid(row=1, column=1, sticky="w")

        ttk.Button(moomoo_frame, text="测试连接", command=self.test_moomoo_connection).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Button(moomoo_frame, text="切换强制模拟模式", command=self.toggle_force_simulate).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.update_moomoo_settings_state()

    def update_moomoo_settings_state(self):
        if hasattr(self, 'force_simulate') and self.force_simulate:
            self.real_radio.config(state="disabled")
            self.trade_mode_var.set("模拟")
        else:
            self.real_radio.config(state="normal")
                
    def test_moomoo_connection(self):
        if self.force_simulate:
            self.trade_env = TrdEnv.SIMULATE
        else:
            self.trade_env = TrdEnv.REAL if self.trade_mode_var.get() == "真实" else TrdEnv.SIMULATE
        
        self.update_moomoo_settings_state()
        
        self.market = TrdMarket.US if self.market_var.get() == "美股" else TrdMarket.HK

        env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
        market_str = "美股" if self.market == TrdMarket.US else "港股"
        
        # 更新状态为正在检测
        self.update_status("正在检测Moomoo网关，请等待...")
        
        # 重置停止标志
        self.stop_connection_attempts.clear()
        
        # 创建一个新线程来执行连接测试
        self.connection_thread = threading.Thread(target=self.connection_test, args=(env_str, market_str))
        self.connection_thread.start()

    def connection_test(self, env_str, market_str):
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            if self.stop_connection_attempts.is_set():
                return
            
            result = self.moomoo_api.test_moomoo_connection(self.trade_env, self.market)
            if result:
                success_message = f"Moomoo API 连接成功！\n已连接到{market_str}{env_str}账户。"
                self.display_results(success_message)
                self.update_status(f"Moomoo API 已连接 - {market_str}{env_str}账户")
                self.moomoo_connected = True
                self.last_connected_env = self.trade_env
                self.last_connected_market = self.market
                self.get_current_account()
                return
            else:
                if attempt < max_attempts:
                    self.update_status(f"连接尝试 {attempt}/{max_attempts} 失败，正在重试...")
                    time.sleep(2)  # 等待2秒后重试
        
        # 如果所有尝试都失败
        error_message = f"Moomoo API 连接失败！\n无法连接到{market_str}{env_str}账户，请检查以下内容：\n1. Moomoo OpenD网关是否已启动\n2. 网络连接是否正常\n3. API设置是否正确"
        self.display_results(error_message)
        self.update_status("Moomoo API 连接失败")
        self.moomoo_connected = False
        self.last_connected_env = None
        self.last_connected_market = None
        self.current_acc_id = None
    
    def run_calculation(self) -> None:
        logger.info("开始运行计算...")
        self.update_status("开始计算购买计划...")
        try:
            instruction = self.instruction_var.get().strip()
            default_instruction = "例：SOXL现价到37.5之间分批买，压力39+，止损36.8"
            logger.debug(f"交易指令: {instruction}")
            
            instruction_info = ""
            if instruction and instruction != default_instruction:
                logger.info("检测到交易指令，开始处理...")
                parsed_instruction = parse_trading_instruction(instruction)
                if self._validate_instruction(parsed_instruction):
                    instruction_info = self._display_instruction_results(instruction, parsed_instruction)
                    self._update_fields_from_instruction(parsed_instruction)
                else:
                    raise ValueError("指令中缺少必要的信息")
            
            self._run_normal_calculation(instruction_info)
            
            logger.debug(f"当前股票代码: {self.current_symbol}")
        except ValueError as ve:
            logger.error(f"输入错误: {str(ve)}")
            self.handle_calculation_error("输入错误", ve)
        except Exception as e:
            logger.error(f"计算过程中发生错误: {str(e)}", exc_info=True)
            self.handle_calculation_error("计算过程中发生错误", e)

    def handle_calculation_error(self, message: str, exception: Exception) -> None:
        """处理计算过程中的错误"""
        error_message = f"{message}: {str(exception)}"
        self.update_status(error_message)
        self.display_results(error_message)
        logger.error(error_message, exc_info=True)

    def _run_normal_calculation(self, instruction_info: str = "") -> None:
        try:
            input_values = self.get_input_values()
            
            # 验证输入
            error_message = validate_inputs(**input_values)
            if error_message:
                self.update_status(error_message)
                self.display_results(f"错误: {error_message}\n\n请调整输入参数后重试。")
                return

            total_funds = input_values['funds']
            result = instruction_info  # 添加指令信息（如果有的话）
            result += f"标的: {self.current_symbol}\n" if self.current_symbol else ""
            result += f"总资金: {total_funds:.2f}\n"
            result += f"可用资金: {total_funds:.2f}\n"
            result += f"初始价格: {input_values['initial_price']:.2f}\n"
            result += f"止损价格: {input_values['stop_loss_price']:.2f}\n"
            result += f"网格数量: {input_values['num_grids']}\n"
            
            # 运行计算逻辑...
            calculation_result = run_calculation(input_values)
            
            result += calculation_result
            
            self.display_results(result)
            self.update_status("计算完成")

        except Exception as e:
            error_message = f"计算过程中发生错误: {str(e)}"
            self.update_status(error_message)
            self.display_results(error_message)
            logger.exception("计算过程中发生未预期的错误")

    def calculate_with_reserve(self, reserve_percentage: int) -> None:
        self.update_status(f"开始计算（保留{reserve_percentage}%资金）...")
        try:
            instruction = self.instruction_var.get().strip()
            default_instruction = "例：SOXL现价到37.5之间分批买，压力39+，止损36.8"
            
            instruction_info = ""
            if instruction and instruction != default_instruction:
                logger.info("检测到交易指令，开始处理...")
                parsed_instruction = parse_trading_instruction(instruction)
                if self._validate_instruction(parsed_instruction):
                    instruction_info = self._display_instruction_results(instruction, parsed_instruction)
                    self._update_fields_from_instruction(parsed_instruction)
                else:
                    raise ValueError("指令中缺少必要的信息")
            
            input_values = self.get_input_values()
            total_funds = input_values['funds']
            reserve_amount = total_funds * (reserve_percentage / 100)
            available_funds = total_funds - reserve_amount
            
            result = instruction_info  # 添加指令信息（如果有的话）
            result += f"标的: {self.current_symbol}\n" if self.current_symbol else ""
            result += f"总资金: {total_funds:.2f}\n"
            result += f"保留资金: {reserve_amount:.2f}\n"
            result += f"可用资金: {available_funds:.2f}\n"
            result += f"初始价格: {input_values['initial_price']:.2f}\n"
            result += f"止损价格: {input_values['stop_loss_price']:.2f}\n"
            result += f"网格数量: {input_values['num_grids']}\n"
            
            # 使用可用资金进行计算
            input_values['funds'] = available_funds
            
            # 验证输入
            error_message = validate_inputs(**input_values)
            if error_message:
                self.update_status(error_message)
                self.display_results(f"错误: {error_message}\n\n请调整输入参数后重试。")
                return

            calculation_result = run_calculation(input_values)
            
            result += calculation_result
            
            self.display_results(result)
            self.update_status(f"计算完成（保留{reserve_percentage}%资金）")
        except ValueError as ve:
            error_message = f"输入错误: {str(ve)}"
            self.update_status(error_message)
            self.display_results(error_message)
            logger.error(error_message)
        except Exception as e:
            error_message = f"计算过程中发生错误: {str(e)}"
            self.update_status(error_message)
            self.display_results(error_message)
            logger.exception("计算过程中发生未预期的错误")

    def get_input_values(self) -> Dict[str, Any]:
        """获取输入值"""
        try:
            return {
                'funds': float(self.funds_var.get()),
                'initial_price': float(self.initial_price_var.get()),
                'stop_loss_price': float(self.stop_loss_price_var.get()),
                'num_grids': int(self.num_grids_var.get()),
                'allocation_method': int(self.allocation_method_var.get())
            }
        except ValueError as e:
            logger.error(f"输入值转换错误: {str(e)}")
            raise ValueError("请确保所有输入都是有效的数字") from e

    import logging

    def display_results(self, result: str) -> None:
        logging.debug(f"Input result to display_results: {result}")
        lines = result.split('\n')
        formatted_lines = self._format_result_lines(lines)
        formatted_result = '\n'.join(formatted_lines)
        
        logging.debug(f"Formatted result: {formatted_result}")
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, formatted_result)
        self.result_text.see("1.0")  # 滚动到顶部

    def _format_result_lines(self, lines: List[str]) -> List[str]:
        logging.debug(f"Input lines to _format_result_lines: {lines}")
        formatted_lines = []
        
        if not lines:
            logging.warning("Empty input to _format_result_lines")
            return formatted_lines  # 返回空列表而不是 None
        
        if lines[0].startswith("标的:"):
            formatted_lines.append(lines.pop(0))
        
        if lines and lines[0].startswith("当前连接:"):
            formatted_lines.extend(lines)
        else:
            formatted_lines.extend(self._format_trading_plan(lines))
        
        logging.debug(f"Formatted lines: {formatted_lines}")
        return formatted_lines

    def _format_trading_plan(self, lines: List[str]) -> List[str]:
        formatted_lines = []

        # 格式化资金信息
        funds_info = ' | '.join(line.strip() for line in lines[:3] if line.strip())
        formatted_lines.append(funds_info)
        
        # 格式化价格和网格信息
        price_grid_info = ' | '.join(line.strip() for line in lines[3:6] if line.strip())
        formatted_lines.append(price_grid_info)
        
        # 移除重复的信息
        unique_lines = [line for line in lines[6:] if line.strip() and not line.startswith(("总资金:", "初始价格:", "止损价格:", "网格数量:"))]
        
        # 处理分配方式信息
        allocation_info = ' | '.join(line.strip() for line in unique_lines[:3] if line.strip())
        formatted_lines.append(allocation_info)
        
        # 处理购买计划
        purchase_plan = [line for line in unique_lines if line.startswith("价格:")]
        if purchase_plan:
            formatted_lines.append("购买计划如下：")
            formatted_lines.extend(line.strip() for line in purchase_plan)
        
        # 处理总结信息
        summary_lines = [line for line in unique_lines if line.startswith(("总购买股数:", "总投资成本:", "平均购买价格:", "最大潜在亏损:", "最大亏损比例:"))]
        if len(summary_lines) >= 3:
            formatted_lines.append(" | ".join(summary_lines[:3]))
        if len(summary_lines) >= 5:
            formatted_lines.append(" | ".join(summary_lines[3:5]))

        return formatted_lines
    
    @exception_handler
    def save_to_csv(self) -> None:
        """保存结果为CSV文件"""
        content = self.result_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "没有可保存的结果")
            return

        file_path = self._get_save_file_path()
        if not file_path:
            return

        self._write_csv_file(file_path, content)
        messagebox.showinfo("成功", f"结果已保存到 {file_path}")

    def _get_save_file_path(self) -> str:
        """获取保存文件路径"""
        default_filename = f"grid_trading_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        initial_dir = os.path.join(get_project_root(), 'output')
        os.makedirs(initial_dir, exist_ok=True)
        return filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_filename,
            initialdir=initial_dir
        )

    def _write_csv_file(self, file_path: str, content: str) -> None:
        """写入CSV文件"""
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            for line in content.split('\n'):
                if line.strip():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        writer.writerow([key.strip(), value.strip()])
                    else:
                        writer.writerow([line.strip()])

    def reset_to_default(self) -> None:
        """重置所有设置到默认状态,但保留常用标的和Moomoo设置"""
        logger.info("用户重置为默认值")

        current_common_stocks = self.user_config.get('CommonStocks', {}) or self.system_config.get('DefaultCommonStocks', {})
        current_moomoo_settings = self.user_config.get('MoomooSettings', {})

        # 重新初始化 user_config
        self.user_config = {
            'API': {
                'choice': 'yahoo',
                'alpha_vantage_key': self.alpha_vantage_key.get()
            },
            'General': {
                'allocation_method': self.system_config.get('General', {}).get('default_allocation_method', '1'),
            },
            'RecentCalculations': {
                'funds': self.system_config.get('General', {}).get('default_funds', '10000'),
                'initial_price': self.system_config.get('General', {}).get('default_initial_price', '100'),
                'stop_loss_price': self.system_config.get('General', {}).get('default_stop_loss_price', '90'),
                'num_grids': self.system_config.get('General', {}).get('default_num_grids', '5')
            },
            'CommonStocks': current_common_stocks,  # 保留现有的常用标的
            'MoomooSettings': current_moomoo_settings,  # 保留现有的Moomoo设置
            'MoomooAPI': self.user_config.get('MoomooAPI', {})  # 保留MoomooAPI设置
        }

        self.save_user_settings()
        self.update_ui_from_config()

        reset_message = "除常用标的和Moomoo设置外,所有设置已重置为默认值"
        self.update_status(reset_message)
        self.display_results(reset_message)
        self.initialize_api_manager()

    def update_ui_from_config(self):
        """根据配置更新 UI 组件"""
        # 更新资金和网格设置
        self.funds_var.set(self.user_config['RecentCalculations'].get('funds', ''))
        self.initial_price_var.set(self.user_config['RecentCalculations'].get('initial_price', ''))
        self.stop_loss_price_var.set(self.user_config['RecentCalculations'].get('stop_loss_price', ''))
        self.num_grids_var.set(self.user_config['RecentCalculations'].get('num_grids', ''))

        # 更新分配方法
        self.allocation_method_var.set(self.user_config['General'].get('allocation_method', '1'))

        # 更新 API 选择
        self.api_choice.set(self.user_config['API'].get('choice', 'yahoo'))

        # 更新 Moomoo 设置
        self.trade_mode_var.set(self.user_config['MoomooSettings'].get('trade_mode', '模拟'))
        self.market_var.set(self.user_config['MoomooSettings'].get('market', '港股'))

        # 清空当前选中的标的和交易指令
        self.current_symbol = None
        self.instruction_var.set("")

        # 更新常用标的按钮
        self.update_common_stocks(self.user_config['CommonStocks'])

        # 更新状态栏
        self.update_status("UI 已根据配置更新")

    def on_api_change(self) -> None:
        """API选择变更处理"""
        new_api_choice = self.api_choice.get()
        if new_api_choice == 'alpha_vantage':
            self._handle_alpha_vantage_selection()
        else:
            self.initialize_api_manager()
        
        self.update_status(f"已切换到 {new_api_choice} API")
        self.save_user_settings()

    def _handle_alpha_vantage_selection(self) -> None:
        existing_key = self.alpha_vantage_key.get()
        if not existing_key:
            messagebox.showinfo("Alpha Vantage API 提示",
                                "请注意：Alpha Vantage 免费版 API 有每日请求次数限制。\n"
                                "建议仅在必要时使用，以避免达到限制。")
            self.prompt_for_alpha_vantage_key()
        else:
            messagebox.showinfo("Alpha Vantage API", f"使用已保存的 API Key: {existing_key[:5]}...")
            self.initialize_api_manager()

    def prompt_for_alpha_vantage_key(self) -> None:
        """提示输入Alpha Vantage API密钥"""
        new_key = simpledialog.askstring("Alpha Vantage API Key",
                                        "请输入您的 Alpha Vantage API Key:",
                                        initialvalue=self.alpha_vantage_key.get())
        if new_key:
            self.alpha_vantage_key.set(new_key)
            self.api_manager = APIManager('alpha_vantage', new_key)
            self.save_user_settings()
        else:
            # 如果用户取消输入且之前没有设置key，切换回Yahoo
            self.api_choice.set('yahoo')  # 修改：确保 GUI 中的选择也更新为 Yahoo
            self.api_manager = APIManager('yahoo', '')
            messagebox.showinfo("API 选择", "由于未提供 Alpha Vantage API Key，已切换回 Yahoo Finance API。")
            self.save_user_settings()
        
        # 更新状态栏显示
        self.update_status(f"已切换到 {self.api_choice.get()} API")  # 新增：更新状态栏

    def save_user_settings(self) -> None:
        """保存用户设置"""
        if self.is_closing:
            return

        try:
            # 更新用户配置
            self.user_config['API'] = {
                'choice': self.api_choice.get(),
                'alpha_vantage_key': self.alpha_vantage_key.get()
            }
            self.user_config['General'] = {
                'allocation_method': self.allocation_method_var.get(),
            }
            self.user_config['RecentCalculations'] = {
                'funds': self.funds_var.get(),
                'initial_price': self.initial_price_var.get(),
                'stop_loss_price': self.stop_loss_price_var.get(),
                'num_grids': self.num_grids_var.get()
            }
            self.user_config['CommonStocks'] = {
                f'stock{i+1}': btn['text'] for i, btn in enumerate(self.common_stocks_frame.winfo_children())
                if isinstance(btn, ttk.Button)
            }
            self.user_config['MoomooSettings'] = {
                'trade_mode': self.trade_mode_var.get(),
                'market': self.market_var.get()
            }

            logger.info(f"保存前的用户配置: {json.dumps(self.user_config, ensure_ascii=False)}")

            # 保存配置
            save_user_config(self.user_config)
            logger.info("用户设置已自动保存")

            # 加载保存后的配置进行比较
            loaded_config = load_user_config()
            logger.info(f"保存后的用户配置: {json.dumps(loaded_config, ensure_ascii=False)}")

            # 比较配置
            if self.user_config != loaded_config:
                logger.warning("保存的配置与加载的配置不匹配，可能存在保存问题")
                # 使用 json.dumps 来创建可比较的字符串
                original = json.dumps(self.user_config, sort_keys=True)
                loaded = json.dumps(loaded_config, sort_keys=True)
                logger.debug(f"原始配置: {original}")
                logger.debug(f"加载的配置: {loaded}")
                # 找出差异
                import difflib
                diff = list(difflib.unified_diff(original.splitlines(), loaded.splitlines()))
                logger.debug(f"配置差异:\n" + "\n".join(diff))
            
            # 更新UI
            self.update_status("用户设置已保存")
        except Exception as e:
            logger.error(f"保存用户设置时发生错误: {str(e)}", exc_info=True)
            self.update_status("保存用户设置时发生错误")

    def load_user_settings(self) -> None:
        """加载用户设置"""
        # 此方法已在 __init__ 中调用，不需要单独调用
        user_api_choice = self.user_config.get('API', {}).get('choice', self.available_apis[0])
        if user_api_choice in self.available_apis:
            self.api_choice.set(user_api_choice)
        else:
            self.api_choice.set(self.available_apis[0])
            logger.warning(f"无效的 API 选择: {user_api_choice}，使用默认值: {self.available_apis[0]}")

        self.alpha_vantage_key.set(self.user_config.get('API', {}).get('alpha_vantage_key', ''))
        self.allocation_method_var.set(self.user_config.get('General', {}).get('allocation_method', '1'))
        
        common_stocks = self.user_config.get('CommonStocks', {})
        self.update_common_stocks(common_stocks)
        
        if self.api_choice.get() == 'alpha_vantage' and not self.alpha_vantage_key.get():
            self.prompt_for_alpha_vantage_key()

    @exception_handler
    def set_stock_price(self, symbol: str) -> None:
        """设置股票价格"""
        if self.api_choice.get() != self.api_manager.api_choice:
            self.initialize_api_manager()

        try:
            current_price, api_used = self.api_manager.get_stock_price(symbol)
            self._update_price_fields(symbol, current_price, api_used)
        except (APIError, ValueError) as e:
            self.handle_api_error(str(e), symbol)
        except Exception as e:
            self.handle_api_error(f"获取股票价格时发生未知错误: {str(e)}", symbol)

    def _update_price_fields(self, symbol: str, current_price: float, api_used: str) -> None:
        if not current_price:
                raise ValueError(f"无法从 {api_used} 获取有效的价格数据")
            
        current_price = round(current_price, 2)
        stop_loss_price = round(current_price * 0.9, 2)
        self.initial_price_var.set(f"{current_price:.2f}")
        self.stop_loss_price_var.set(f"{stop_loss_price:.2f}")
        self.current_symbol = symbol
        status_message = f"已选择标的 {symbol}，当前价格为 {current_price:.2f} 元 (来自 {api_used})"
        self.update_status(status_message)
        result_message = (
            f"选中标的: {symbol}\n"
            f"当前价格: {current_price:.2f} 元 (来自 {api_used})\n"
            f"止损价格: {stop_loss_price:.2f} 元 (按90%当前价格计算)\n\n"
            f"初始价格和止损价格已更新。您可以直接点击\"计算购买计划\"按钮或调整其他参数。"
        )
        self.display_results(result_message)
    
    def handle_api_error(self, error_message: str, symbol: str):
        """处理API错误"""
        full_error_message = f"无法获取标的 {symbol} 的价格\n\n错误信息: {error_message}\n\n建议检查网络连接、API key 是否有效，或尝试切换到其他 API。"
        self.update_status(error_message)
        self.display_results(full_error_message)
        logger.error(error_message)
        self.current_symbol = symbol  # 即使获取价格失败，也设置当前标的

    def update_status(self, message: str) -> None:
        """更新状态栏信息"""
        if self.status_bar:
            # 截断长消息
            max_length = 100  # 可以根据需要调整
            if len(message) > max_length:
                message = message[:max_length] + "..."
            self.status_bar.config(text=message)
        else:
            print(f"Status: {message}")  # 如果状态栏还未创建，则打印到控制台

    def _update_status_impl(self, message: str) -> None:
            """实现 StatusManager 的 _update_status_impl 方法"""
            if self.status_bar:
                # 截断长消息
                max_length = 100  # 可以根据需要调整
                if len(message) > max_length:
                    message = message[:max_length] + "..."
                self.status_bar.config(text=message)
            else:
                print(f"Status: {message}")  # 如果状态栏还未创建，则打印到控制台

    def __del__(self) -> None:
        """析构函数，确保在程序退出时保存设置"""
        self.is_closing = True
        self.save_user_settings()

    @staticmethod
    def validate_float_input(action: str, value_if_allowed: str) -> bool:
        """验证输入是否为有效的浮点数"""
        if action == '1':  # insert
            if value_if_allowed == "":
                return True
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        return True

    @staticmethod
    def validate_int_input(action: str, value_if_allowed: str) -> bool:
        """验证输入是否为有效的整数"""
        if action == '1':  # insert
            if value_if_allowed == "":
                return True
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False
        return True

    def get_current_account(self):
        self.trade_env = TrdEnv.REAL if self.trade_mode_var.get() == "真实" else TrdEnv.SIMULATE
        self.market = TrdMarket.US if self.market_var.get() == "美股" else TrdMarket.HK
        logger.info(f"Current settings: trade_env={self.trade_env}, market={self.market}")
        acc_list = self.moomoo_api.get_acc_list(self.trade_env, self.market)
        if acc_list is not None and not acc_list.empty:
            self.current_acc_id = acc_list.iloc[0]['acc_id']
            logger.info(f"Selected account: {self.current_acc_id}")
        else:
            self.current_acc_id = None
            logger.warning("No accounts found")

    def query_available_funds(self) -> None:
        """查询可用资金"""
        if not self._validate_account_access():
            return
        
        info = self.moomoo_api.get_account_info(self.current_acc_id, self.trade_env, self.market)
        if info is not None and not info.empty:
            self._display_account_info(info)
        else:
            self.display_results("无法获取账户信息")

    def _validate_account_access(self) -> bool:
        if not self.check_moomoo_connection():
            return False
        if self.current_acc_id is None:
            self.display_results("无法获取账户信息")
            return False
        return True

    def _display_account_info(self, info: pd.DataFrame) -> None:
        env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
        market_str = "美股" if self.market == TrdMarket.US else "港股"
        result = f"当前连接: {market_str}{env_str}账户\n"
        result += f"账户 {self.current_acc_id} 资金情况:\n"
        
        # 使用安全的格式化方法
        def safe_format(value):
            try:
                return f"{float(value):.2f}" if value != 'N/A' else 'N/A'
            except ValueError:
                return str(value)
        
        result += f"总资产: ${safe_format(info['total_assets'].values[0])}\n"
        result += f"现金: ${safe_format(info['cash'].values[0])}\n"
        result += f"证券市值: ${safe_format(info['securities_assets'].values[0])}\n"
        result += f"购买力: ${safe_format(info['power'].values[0])}\n"
        result += f"最大购买力: ${safe_format(info['max_power_short'].values[0])}\n"
        result += f"币种: {info['currency'].values[0]}\n"
        
        self.display_results(result)
        self.update_status(f"Moomoo API - {market_str}{env_str}账户 - 资金查询完成")
    
    def enable_real_time_notifications(self):
        if not self.check_moomoo_connection():
            return
        message = "实时通知功能需要注册用户并付费开通。\n根据discord群的喊单记录直接调用解析指令并生成购买计划\n请联系作者了解更多信息。"
        self.display_results(message)
        messagebox.showinfo("实时通知", message)

    def place_order_by_plan(self):
        if self.force_simulate:
            self.trade_env = TrdEnv.SIMULATE
            self.display_results("注意：当前处于强制模拟模式，所有交易将在模拟环境中执行。")
        elif self.trade_env == TrdEnv.REAL:
            confirm = messagebox.askyesno("确认", "您即将在真实环境中下单，是否确认？")
            if not confirm:
                self.display_results("已取消在真实环境中下单。")
                return
            
        if not self.moomoo_connected:
            self.display_results("错误：请先在Moomoo设置中完成测试连接")
            self.update_status("Moomoo API 未连接")
            return

        current_result = self.result_text.get("1.0", tk.END).strip()
        if not current_result:
            self.display_results("错误：当前没有有效的购买计划。请先运行计算。")
            self.update_status("无效的购买计划")
            return

        # 检查是否有标的
        if "标的:" not in current_result:
            self.display_results("错误：当前购买计划中没有指定标的。请重新计算包含标的的购买计划。")
            self.update_status("无效的购买计划：缺少标的")
            return

        # 解析标的和计划细节
        lines = current_result.split('\n')
        self.current_symbol = lines[0].split(":")[1].strip()
        plan = []
        for line in lines:
            if "价格:" in line and "购买股数:" in line:
                parts = line.split(",")
                if len(parts) >= 2:
                    price = float(parts[0].split(":")[1].strip())
                    quantity = int(parts[1].split("购买股数:")[1].strip())
                    plan.append({"price": price, "quantity": quantity})

        if not plan:
            self.display_results("错误：无法解析购买计划。请确保已正确计算并显示计划。")
            self.update_status("购买计划解析失败")
            return

        # 获取账户列表
        acc_list = self.moomoo_api.get_acc_list(self.trade_env, self.market)
        if acc_list is None or acc_list.empty:
            self.display_results("错误：无法获取账户列表")
            self.update_status("账户列表获取失败")
            return

        # 选择账户
        if len(acc_list) == 1:
            selected_acc_id = acc_list.iloc[0]['acc_id']
        else:
            options = [f"{acc['acc_id']} - {acc['acc_type']}" for _, acc in acc_list.iterrows()]
            choice = simpledialog.askstring("选择账户", "请选择要使用的账户：", initialvalue=options[0])
            if choice is None:
                self.update_status("账户选择已取消")
                return
            selected_acc_id = int(choice.split(' - ')[0])

        # 确认下单
        env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
        market_str = "美股" if self.market == TrdMarket.US else "港股"
        message = f"准备按计划为标的 {self.current_symbol} 下单。\n"
        message += f"当前连接: {market_str}{env_str}账户\n"
        message += f"选择的账户ID: {selected_acc_id}\n"
        message += "注意：这将执行实际的交易操作。\n\n"
        message += "当前计划：\n"
        for item in plan:
            message += f"  价格: {item['price']:.2f}, 数量: {item['quantity']}\n"

        self.display_results(message)
        if messagebox.askyesno("确认下单", "是否确认执行上述下单计划？"):
            for item in plan:
                result = self.moomoo_api.place_order(
                    acc_id=selected_acc_id,
                    trade_env=self.trade_env,
                    market=self.market,
                    code=self.current_symbol,
                    price=item['price'],
                    qty=item['quantity'],
                    trd_side=TrdSide.BUY
                )
                if result is not None:
                    self.display_results(f"下单成功：价格 {item['price']:.2f}, 数量 {item['quantity']}")
                else:
                    self.display_results(f"下单失败：价格 {item['price']:.2f}, 数量 {item['quantity']}")

            self.update_status(f"Moomoo API - {market_str}{env_str}账户 - 下单完成")
        else:
            self.update_status(f"Moomoo API - {market_str}{env_str}账户 - 已取消下单")

    def query_positions(self):
        if not self.check_moomoo_connection():
            return
        if self.current_acc_id is None:
            self.display_results("无法获取账户信息")
            return
        
        positions = self.moomoo_api.get_positions(self.current_acc_id, self.trade_env, self.market)
        if positions is not None and not positions.empty:
            logger.info(f"User queried positions for account {self.current_acc_id}")
            
            env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
            market_str = "美股" if self.market == TrdMarket.US else "港股"
            result = f"当前连接: {market_str}{env_str}账户\n"
            result += f"查询账户 {self.current_acc_id} 持仓:\n"
            result += f"持仓股票数: {len(positions)}\n"
            result += "{:<5}{:<10}{:<12}{:<15}{:<15}{:<15}\n".format(
                "序号", "代码", "数量", "市值($)", "成本价", "盈亏比例(%)"
            )
            result += "-" * 80 + "\n"
            
            # 按市值降序排序
            positions_sorted = positions.sort_values(by='market_val', ascending=False)
            
            for index, row in positions_sorted.iterrows():
                result += "{:<5}{:<10}{:<12,.2f}{:<15,.2f}{:<15,.2f}{:<15,.2f}\n".format(
                    index+1,
                    row['code'],
                    row['qty'],
                    row['market_val'],
                    row['cost_price'],
                    row['pl_ratio']
                )
            self.display_results(result)
            self.update_status(f"Moomoo API - {market_str}{env_str}账户 - 持仓查询完成")
        else:
            self.display_results("无法获取持仓信息或没有持仓")

    def query_history_orders(self):
        if not self.check_moomoo_connection():
            return
        if self.current_acc_id is None:
            self.display_results("无法获取账户信息")
            return
        
        orders = self.moomoo_api.get_history_orders(self.current_acc_id, self.trade_env, self.market)
        if orders is not None and not orders.empty:
            logger.info(f"User queried history orders for account {self.current_acc_id}")
            
            env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
            market_str = "美股" if self.market == TrdMarket.US else "港股"
            result = f"当前连接: {market_str}{env_str}账户\n"
            result += f"查询账户 {self.current_acc_id} 历史订单:\n"
            result += f"总订单数: {len(orders)}\n"
            result += "最近10笔订单:\n"
            result += "{:<5}{:<10}{:<8}{:<12}{:<15}{:<15}\n".format(
                "序号", "代码", "方向", "数量", "价格", "创建日期"
            )
            result += "-" * 80 + "\n"
            
            for index, row in orders.head(10).iterrows():
                create_time = row['create_time']
                if isinstance(create_time, str):
                    try:
                        create_time = datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        try:
                            create_time = datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            pass
                
                formatted_date = create_time.strftime('%Y-%m-%d') if isinstance(create_time, datetime) else str(create_time)
                
                result += "{:<5}{:<10}{:<8}{:<12,.2f}{:<15,.2f}{:<15}\n".format(
                    index+1,
                    row['code'],
                    row['trd_side'],
                    row['qty'],
                    row['price'],
                    formatted_date
                )
            self.display_results(result)
            self.update_status(f"Moomoo API - {market_str}{env_str}账户 - 历史订单查询完成")
        else:
            self.display_results("无法获取历史订单信息或没有历史订单")

    def check_moomoo_connection(self) -> bool:
        # 检查Moomoo连接状态
        current_env = TrdEnv.REAL if self.trade_mode_var.get() == "真实" else TrdEnv.SIMULATE
        current_market = TrdMarket.US if self.market_var.get() == "美股" else TrdMarket.HK

        if not self.moomoo_connected or self.last_connected_env != current_env or self.last_connected_market != current_market:
            messagebox.showwarning("未连接", "请先在Moomoo设置中完成测试连接")
            return False
        return True

    def calculate_total_profit(self):
        if not self.check_moomoo_connection():
            return
        self.display_results("计算总体利润功能尚未实现")

    def check_for_updates(self) -> None:
        """检查更新"""
        current_version = self.version
        latest_version = get_latest_version()
        
        if latest_version and compare_versions(current_version, latest_version):
            response = messagebox.askyesno(
                "更新可用",
                f"发现新版本 {latest_version}。是否现在更新？"
            )
            if response:
                self.start_update(latest_version)

    def start_update(self, version: str) -> None:
        """开始更新过程（待实现）"""
        # 实现更新逻辑
        pass

    def setup_layout(self) -> None:
        """设置主窗口布局"""
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)  # 修改：给上半部分更多空间
        self.main_frame.grid_rowconfigure(1, weight=2)  # 修改：给结果显示区域更多空间
        
        self.right_frame.grid_columnconfigure(1, weight=1)
        for i in range(10):
            self.right_frame.grid_rowconfigure(i, weight=0)

    from typing import Dict, Any

    def process_instruction(self, instruction: str) -> None:
        """处理交易指令"""
        logger.info(f"开始处理交易指令: {instruction}")
        try:
            parsed_instruction = parse_trading_instruction(instruction)
            logger.debug(f"解析后的指令: {parsed_instruction}")
            if self._validate_instruction(parsed_instruction):
                logger.info("指令验证通过，更新字段并执行计算...")
                self._update_fields_from_instruction(parsed_instruction)
                self._run_normal_calculation()
                self._display_instruction_results(instruction, parsed_instruction)
            else:
                logger.warning("指令验证失败")
                raise ValueError("指令中缺少必要的信息")
        except Exception as e:
            logger.error(f"处理指令时发生错误: {str(e)}", exc_info=True)
            self._handle_instruction_error(str(e))

    def _validate_instruction(self, parsed_instruction: Dict[str, Any]) -> bool:
        """验证解析后的指令是否包含所有必要信息"""
        logger.debug(f"验证解析后的指令: {parsed_instruction}")
        required_fields = ['symbol', 'current_price', 'stop_loss']
        is_valid = all(parsed_instruction.get(field) is not None for field in required_fields)
        logger.info(f"指令验证结果: {'通过' if is_valid else '失败'}")
        return is_valid

    def _update_fields_from_instruction(self, parsed_instruction: Dict[str, Any]) -> None:
        """根据解析后的指令更新相关字段"""
        logger.info("根据解析的指令更新字段")
        self.current_symbol = parsed_instruction['symbol']
        self.initial_price_var.set(str(parsed_instruction['current_price']))
        self.stop_loss_price_var.set(str(parsed_instruction['stop_loss']))
        # 可能需要更新其他字段，比如 funds_var 和 num_grids_var
        logger.debug(f"更新后的字段: symbol={self.current_symbol}, initial_price={self.initial_price_var.get()}, stop_loss={self.stop_loss_price_var.get()}")
    
    
    def _display_instruction_results(self, original_instruction: str, parsed_instruction: Dict[str, Any]) -> None:
        """显示指令处理结果"""
        logger.info("显示指令处理结果")
        instruction_info = f"原始指令: {original_instruction}\n"
        instruction_info += f"解析结果: 标的={parsed_instruction['symbol']}, " \
                            f"当前价格={parsed_instruction['current_price']:.2f}, " \
                            f"止损价格={parsed_instruction['stop_loss']:.2f}\n"
        
        self.current_symbol = parsed_instruction['symbol']
        self.initial_price_var.set(f"{parsed_instruction['current_price']:.2f}")
        self.stop_loss_price_var.set(f"{parsed_instruction['stop_loss']:.2f}")
        
        logger.debug(f"指令解析结果: {instruction_info}")
        # 不在这里直接显示结果，而是返回解析信息
        return instruction_info

    def _handle_instruction_error(self, error_message: str) -> None:
        """处理指令处理过程中的错误"""
        full_error_message = f"处理指令时出错: {error_message}"
        self.update_status(full_error_message)
        self.display_results(full_error_message)
        logger.error(full_error_message, exc_info=True)

    def initialize_api_manager(self):
        """初始化或更新API管理器"""
        self.api_manager = APIManager(self.api_choice.get(), self.alpha_vantage_key.get())
        logger.info(f"API管理器已初始化为 {self.api_choice.get()}")

    def setup_window_properties(self):
        """设置窗口属性"""
        self.master.geometry("750x750")  # 修改：增加窗口高度
        self.master.minsize(750, 750)
        self.master.maxsize(750, 750)
        self.master.resizable(False, False)

    def on_closing(self):
        """窗口关闭时的处理"""
        self.stop_connection_attempts.set()
        if self.connection_thread:
            self.connection_thread.join(timeout=5)  # 等待连接线程结束，最多等待5秒
        self.is_closing = True
        self.save_user_settings()
        self.master.destroy()

    def toggle_force_simulate(self):
        self.force_simulate = not self.force_simulate
        self.update_moomoo_settings_state()
        status = "启用" if self.force_simulate else "禁用"
        self.display_results(f"强制模拟模式已{status}")
        self.update_status(f"强制模拟模式: {status}")

    def ensure_attributes(self):
        if not hasattr(self, 'force_simulate'):
            self.force_simulate = True
        if not hasattr(self, 'real_radio'):
            self.real_radio = None
    

class UserConfigWindow(tk.Toplevel):
    def __init__(self, parent, user_config):
        super().__init__(parent)
        self.title("用户配置")
        self.user_config = user_config
        
        self.api_var = tk.StringVar(value=user_config.get('API', {}).get('choice', 'yahoo'))
        self.api_key_var = tk.StringVar(value=user_config.get('API', {}).get('alpha_vantage_key', ''))
        self.allocation_var = tk.StringVar(value=user_config.get('General', {}).get('allocation_method', '1'))
        
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="API 选择:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(self, text="Yahoo", variable=self.api_var, value="yahoo").grid(row=1, column=0, sticky="w", padx=20)
        ttk.Radiobutton(self, text="Alpha Vantage", variable=self.api_var, value="alpha_vantage").grid(row=2, column=0, sticky="w", padx=20)

        ttk.Label(self, text="API Key:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self, textvariable=self.api_key_var).grid(row=4, column=0, padx=20, pady=5)

        ttk.Label(self, text="分配方法:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(self, text="等金额", variable=self.allocation_var, value="0").grid(row=6, column=0, sticky="w", padx=20)
        ttk.Radiobutton(self, text="等比例", variable=self.allocation_var, value="1").grid(row=7, column=0, sticky="w", padx=20)
        ttk.Radiobutton(self, text="线性加权", variable=self.allocation_var, value="2").grid(row=8, column=0, sticky="w", padx=20)

        ttk.Button(self, text="保存", command=self.save_config).grid(row=9, column=0, pady=10)

    def save_config(self):
        self.user_config['API'] = {
            'choice': self.api_var.get(),
            'alpha_vantage_key': self.api_key_var.get()
        }
        if 'General' not in self.user_config:
            self.user_config['General'] = {}
        self.user_config['General']['allocation_method'] = self.allocation_var.get()
        save_user_config(self.user_config)
        self.destroy()