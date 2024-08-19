# src/gui.py

import csv
import logging
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
from datetime import datetime
from typing import Dict, Any, Callable
from moomoo import TrdEnv, TrdMarket

from src.api_manager import AlphaVantageError, APIManager
from src.calculations import (
    run_calculation, 
    calculate_with_reserve,
    parse_trading_instruction, 
    validate_inputs 
)
from src.config import save_user_config, load_user_config, load_system_config, DEFAULT_USER_CONFIG
from src.status_manager import StatusManager
from src.utils import exception_handler, compare_versions, get_latest_version
from src.api_interface import (
    test_moomoo_connection,
    get_history_orders,
    get_acc_list,
    select_account,
    get_account_info,
    get_positions
)

logger = logging.getLogger(__name__)

def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class App:
    """
    Grid Trading Tool 的主应用类。
    管理GUI界面和用户交互。
    """

    def __init__(self, master: tk.Tk, config: Dict[str, Any], version: str):
        """
        初始化应用。

        :param master: Tkinter 主窗口
        :param config: 应用配置
        :param version: 应用版本
        """
        self.master = master or tk.Tk()
        self.system_config = config
        self.version = version
        self.current_symbol = None
        self.status_bar = None
        self.master.title(f"Grid Trading Tool v{self.version}")

        self.is_closing = False

        self.load_configurations()
        self.setup_variables()
        self.create_widgets()
        self.setup_layout()
        self.initialize_api_manager()

        App.instance = self
        self.status_manager = StatusManager()
        StatusManager.set_instance(self)
        
        self.setup_window_properties()
        self.load_user_settings()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.trade_env = None
        self.market = None
        self.current_symbol = None
        self.moomoo_connected = False
        self.last_connected_env = None
        self.last_connected_market = None

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
        self.trade_mode_var = tk.StringVar(value=self.user_config.get('MoomooSettings', {}).get('trade_mode', "模拟"))
        self.market_var = tk.StringVar(value=self.user_config.get('MoomooSettings', {}).get('market', "港股"))

        general_config = self.user_config['General']
        recent_calc = self.user_config.get('RecentCalculations', general_config)

        self.funds_var = tk.StringVar(value=recent_calc.get('funds', general_config['funds']))
        self.initial_price_var = tk.StringVar(value=recent_calc.get('initial_price', general_config['initial_price']))
        self.stop_loss_price_var = tk.StringVar(value=recent_calc.get('stop_loss_price', general_config['stop_loss_price']))
        self.num_grids_var = tk.StringVar(value=recent_calc.get('num_grids', general_config['num_grids']))
        self.allocation_method_var = tk.StringVar(value=general_config['allocation_method'])

    def open_user_config(self):
        UserConfigWindow(self.master, self.user_config)

    def create_widgets(self):
        """创建并布局所有GUI组件"""
        try:
            self.create_main_frame()
            self.create_status_bar()
            self.create_left_frame()
            self.create_right_frame()
            self.create_result_frame()
        except Exception as e:
            # self.handle_gui_error("创建 GUI 组件时发生错误", e)
            print(f"创建 GUI 组件时发生错误: {str(e)}")

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

    def create_right_widgets(self):
        """创建右侧组件"""
        self.create_input_fields()
        self.create_option_frame()
        self.create_buttons()

    def create_input_fields(self):
        """创建输入字段"""
        labels = ["可用资金:", "初始价格:", "止损价格:", "网格数量:", "交易指令:"]
        vars = [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var, self.instruction_var]

        for i, (label, var) in enumerate(zip(labels, vars)):
            ttk.Label(self.right_frame, text=label).grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(self.right_frame, textvariable=var, width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=(5, 0), pady=2)

    def create_option_frame(self):
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

    def create_buttons(self):
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

        ttk.Radiobutton(moomoo_frame, text="真实", variable=self.trade_mode_var, value="真实").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(moomoo_frame, text="模拟", variable=self.trade_mode_var, value="模拟").grid(row=0, column=1, sticky="w")

        ttk.Radiobutton(moomoo_frame, text="美股", variable=self.market_var, value="美股").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(moomoo_frame, text="港股", variable=self.market_var, value="港股").grid(row=1, column=1, sticky="w")

        ttk.Button(moomoo_frame, text="测试连接", command=self.test_moomoo_connection).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

    def test_moomoo_connection(self):
        self.trade_env = TrdEnv.REAL if self.trade_mode_var.get() == "真实" else TrdEnv.SIMULATE
        self.market = TrdMarket.US if self.market_var.get() == "美股" else TrdMarket.HK
        
        env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
        market_str = "美股" if self.market == TrdMarket.US else "港股"
        
        result = test_moomoo_connection(self.trade_env, self.market)
        if result:
            success_message = f"Moomoo API 连接成功！\n已连接到{market_str}{env_str}账户。"
            self.display_results(success_message)
            self.update_status(f"Moomoo API 已连接 - {market_str}{env_str}账户")
            self.moomoo_connected = True
            self.last_connected_env = self.trade_env
            self.last_connected_market = self.market
            self.get_current_account()
        else:
            error_message = f"Moomoo API 连接失败！\n无法连接到{market_str}{env_str}账户，请检查设置。"
            self.display_results(error_message)
            self.update_status("Moomoo API 连接失败")
            self.moomoo_connected = False
            self.last_connected_env = None
            self.last_connected_market = None
            self.current_acc_id = None
        return result
    
    def run_calculation(self) -> None:
        self.update_status("开始计算购买计划...")
        try:
            instruction = self.instruction_var.get().strip()
            if instruction:
                self.process_instruction(instruction)
            else:
                self._run_normal_calculation()
            self.current_symbol = self.symbol_var.get() if hasattr(self, 'symbol_var') else None
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

    def _run_normal_calculation(self) -> None:
        try:
            input_values = self.get_input_values()
            
            # 验证输入
            error_message = validate_inputs(**input_values)
            if error_message:
                self.update_status(error_message)
                self.display_results(f"错误: {error_message}\n\n请调整输入参数后重试。")
                return

            total_funds = input_values['funds']
            result = f"总资金: {total_funds:.2f}\n"
            result += f"可用资金: {total_funds:.2f}\n"
            result += f"初始价格: {input_values['initial_price']:.2f}\n"
            result += f"止损价格: {input_values['stop_loss_price']:.2f}\n"
            result += f"网格数量: {input_values['num_grids']}\n"
            
            # 运行计算逻辑...
            calculation_result = run_calculation(input_values)
            
            result += calculation_result
            
            if self.current_symbol:
                symbol_info = f"标的: {self.current_symbol}\n"
                self.display_results(f"{symbol_info}\n{result}")
            else:
                self.display_results(result)
            
            self.update_status("计算完成")
            self.current_symbol = self.symbol_var.get() if hasattr(self, 'symbol_var') else None

        except Exception as e:
            error_message = f"计算过程中发生错误: {str(e)}"
            self.update_status(error_message)
            self.display_results(error_message)
            logger.exception("计算过程中发生未预期的错误")

    def calculate_with_reserve(self, reserve_percentage: int) -> None:
        self.update_status(f"开始计算（保留{reserve_percentage}%资金）...")
        try:
            input_values = self.get_input_values()
            total_funds = input_values['funds']
            reserve_amount = total_funds * (reserve_percentage / 100)
            available_funds = total_funds - reserve_amount
            
            result = f"总资金: {total_funds:.2f}\n"
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
            
            if self.current_symbol:
                symbol_info = f"标的: {self.current_symbol}\n"
                self.display_results(f"{symbol_info}\n{result}")
            else:
                self.display_results(result)
            
            self.update_status(f"计算完成（保留{reserve_percentage}%资金）")
            self.current_symbol = self.symbol_var.get() if hasattr(self, 'symbol_var') else None
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
        return {
            'funds': float(self.funds_var.get()),
            'initial_price': float(self.initial_price_var.get()),
            'stop_loss_price': float(self.stop_loss_price_var.get()),
            'num_grids': int(self.num_grids_var.get()),
            'allocation_method': int(self.allocation_method_var.get())
        }

    def display_results(self, result):
        lines = result.split('\n')
        formatted_lines = []
        
        # 处理标的信息（如果有）
        if lines and lines[0].startswith("标的:"):
            formatted_lines.append(lines.pop(0))
        
        # 检查是否为持仓信息
        if lines and lines[0].startswith("当前连接:"):
            # 对于持仓信息，保持原格式
            formatted_lines.extend(lines)
        else:
            # 格式化资金信息
            funds_info = ' | '.join(line.strip() for line in lines[:3] if line.strip())
            formatted_lines.append(funds_info)
            
            # 格式化价格和网格信息
            price_grid_info = ' | '.join(line.strip() for line in lines[3:6] if line.strip())
            formatted_lines.append(price_grid_info)
            
            # 移除重复的信息
            lines = [line for line in lines[6:] if line.strip() and not line.startswith("总资金:") and not line.startswith("初始价格:") and not line.startswith("止损价格:") and not line.startswith("网格数量:")]
            
            # 处理分配方式信息
            allocation_info = ' | '.join(line.strip() for line in lines[:3] if line.strip())
            formatted_lines.append(allocation_info)
            
            # 处理购买计划
            purchase_plan = [line for line in lines if line.startswith("价格:")]
            if purchase_plan:
                formatted_lines.append("购买计划如下：")
                for line in purchase_plan:
                    formatted_lines.append(line.strip())
            
            # 处理总结信息
            summary_lines = [line for line in lines if line.startswith(("总购买股数:", "总投资成本:", "平均购买价格:", "最大潜在亏损:", "最大亏损比例:"))]
            if len(summary_lines) >= 3:
                formatted_lines.append(" | ".join(summary_lines[:3]))
            if len(summary_lines) >= 5:
                formatted_lines.append(" | ".join(summary_lines[3:5]))
        
        formatted_result = '\n'.join(formatted_lines)
    
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, formatted_result)
        self.result_text.see("1.0")  # 滚动到顶部

    def save_to_csv(self) -> None:
        """保存结果为CSV文件"""
        logger.info("用户尝试保存结果为 CSV")
        try:
            content = self.result_text.get(1.0, tk.END)
            if not content.strip():
                messagebox.showwarning("警告", "没有可保存的结果")
                logger.warning("尝试保存空结果")
                return

            file_path = self._get_save_file_path()
            if not file_path:
                logger.info("用户取消了保存操作")
                return

            self._write_csv_file(file_path, content)
            logger.info(f"结果已保存到 {file_path}")
            messagebox.showinfo("成功", f"结果已保存到 {file_path}")
        except Exception as e:
            logger.exception("保存文件时发生错误")
            messagebox.showerror("错误", f"保存文件时发生错误: {str(e)}")

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
        
        # 保存当前的常用标的和Moomoo设置
        current_common_stocks = self.user_config.get('CommonStocks', {})
        current_moomoo_settings = self.user_config.get('MoomooSettings', {})
        
        logger.info(f"重置前的常用标的: {current_common_stocks}")  # 添加日志
        logger.info(f"重置前的Moomoo设置: {current_moomoo_settings}")  # 添加日志
        
        self.api_choice.set('yahoo')
        self.funds_var.set(self.system_config.get('General', {}).get('default_funds', '10000'))
        self.allocation_method_var.set(self.system_config.get('General', {}).get('default_allocation_method', '1'))
        self.initial_price_var.set(self.system_config.get('General', {}).get('default_initial_price', '100'))
        self.stop_loss_price_var.set(self.system_config.get('General', {}).get('default_stop_loss_price', '90'))
        self.num_grids_var.set(self.system_config.get('General', {}).get('default_num_grids', '5'))
        
        # 新增代码开始
        if not current_common_stocks:
            current_common_stocks = self.system_config.get('DefaultCommonStocks', {})
            logger.info(f"使用默认常用标的: {current_common_stocks}")  # 添加日志
        # 新增代码结束
        
        self.update_common_stocks(current_common_stocks)
        
        self.current_symbol = None  # 重置当前选中的标的
        self.instruction_var.set("")  # 清空交易指令输入框
        
        # 使用现有的Moomoo设置,如果没有则使用默认值
        self.trade_mode_var.set(current_moomoo_settings.get('trade_mode', '模拟'))
        self.market_var.set(current_moomoo_settings.get('market', '港股'))
        
        # 重新初始化 user_config
        self.user_config = {
            'API': {'choice': 'yahoo', 'alpha_vantage_key': self.alpha_vantage_key.get()},
            'General': {
                'allocation_method': self.allocation_method_var.get(),
                'funds': self.funds_var.get(),
                'initial_price': self.initial_price_var.get(),
                'stop_loss_price': self.stop_loss_price_var.get(),
                'num_grids': self.num_grids_var.get()
            },
            'CommonStocks': current_common_stocks,  # 保留现有的常用标的
            'MoomooSettings': current_moomoo_settings  # 保留现有的Moomoo设置
        }
        
        logger.info(f"重置后的常用标的: {self.user_config['CommonStocks']}")  # 添加日志
        logger.info(f"重置后的Moomoo设置: {self.user_config['MoomooSettings']}")  # 添加日志
        
        self.save_user_settings()
        reset_message = "除常用标的和Moomoo设置外,所有设置已重置为默认值"
        self.update_status(reset_message)
        self.display_results(reset_message)
        self.initialize_api_manager()

    def on_api_change(self) -> None:
        """API选择变更处理"""
        new_api_choice = self.api_choice.get()
        if new_api_choice == 'alpha_vantage':
            existing_key = self.alpha_vantage_key.get()
            if not existing_key:
                messagebox.showinfo("Alpha Vantage API 提示", 
                                    "请注意：Alpha Vantage 免费版 API 有每日请求次数限制。\n"
                                    "建议仅在必要时使用，以避免达到限制。")
                self.prompt_for_alpha_vantage_key()
            else:
                messagebox.showinfo("Alpha Vantage API", f"使用已保存的 API Key: {existing_key[:5]}...")
                self.initialize_api_manager()
        else:  # Yahoo API
            self.initialize_api_manager()
        
        # 确保状态栏显示正确的 API 选择
        self.update_status(f"已切换到 {self.api_choice.get()} API")  # 修改：使用 self.api_choice.get() 而不是 new_api_choice
        self.save_user_settings()

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
        
        self.user_config['API'] = {
            'choice': self.api_choice.get(),
            'alpha_vantage_key': self.alpha_vantage_key.get()
        }
        self.user_config['General'] = {
            'allocation_method': self.allocation_method_var.get(),
            'funds': self.funds_var.get(),
            'initial_price': self.initial_price_var.get(),
            'stop_loss_price': self.stop_loss_price_var.get(),
            'num_grids': self.num_grids_var.get()
        }
        
        # 修改：总是更新 CommonStocks，不管之前是否存在
        self.user_config['CommonStocks'] = {f'stock{i+1}': btn['text'] for i, btn in 
                                            enumerate(self.common_stocks_frame.winfo_children()) 
                                            if isinstance(btn, ttk.Button)}  # 修改：使用 ttk.Button 而不是 tk.Button
        
        self.user_config['MoomooSettings'] = {
            'trade_mode': self.trade_mode_var.get(),
            'market': self.market_var.get()
        }
        
        logger.info(f"保存前的用户配置: {self.user_config}") 
        
        save_user_config(self.user_config)
        logger.info("用户设置已自动保存")
        
        loaded_config = load_user_config()
        logger.info(f"保存后的用户配置: {loaded_config}") 
        
        # 添加：检查保存是否成功
        if self.user_config != loaded_config:
            logger.warning("保存的配置与加载的配置不匹配，可能存在保存问题")
            logger.debug(f"差异: {set(self.user_config.items()) ^ set(loaded_config.items())}")

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

    def set_stock_price(self, symbol: str) -> None:
        """设置股票价格"""
        if self.api_choice.get() != self.api_manager.api_choice:
            self.initialize_api_manager()

        try:
            current_price, api_used = self.api_manager.get_stock_price(symbol)
            if not current_price:
                raise ValueError(f"无法从 {api_used} 获取有效的价格数据")
            
            current_price = round(current_price, 2)
            stop_loss_price = round(current_price * 0.9, 2)
            self.initial_price_var.set(f"{current_price:.2f}")
            self.stop_loss_price_var.set(f"{stop_loss_price:.2f}")
            self.current_symbol = symbol
            status_message = f"已选择标的 {symbol}，当前价格为 {current_price:.2f} 元 (来自 {api_used})"
            self.update_status(status_message)
            self.display_results(
                f"选中标的: {symbol}\n"
                f"当前价格: {current_price:.2f} 元 (来自 {api_used})\n"
                f"止损价格: {stop_loss_price:.2f} 元 (按90%当前价格计算)\n\n"
                f"初始价格和止损价格已更新。您可以直接点击\"计算购买计划\"按钮或调整其他参数。"
            )
        except (AlphaVantageError, ValueError) as e:
            self.handle_api_error(str(e), symbol)
        except Exception as e:
            self.handle_api_error(f"获取股票价格时发生未知错误: {str(e)}", symbol)
        
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
        acc_list = get_acc_list(self.trade_env, self.market)
        if acc_list is not None and not acc_list.empty:
            self.current_acc_id = acc_list.iloc[0]['acc_id']
            logger.info(f"Selected account: {self.current_acc_id}")
        else:
            self.current_acc_id = None
            logger.warning("No accounts found")

    def query_available_funds(self):
        if not self.check_moomoo_connection():
            return
        if self.current_acc_id is None:
            self.display_results("无法获取账户信息")
            return
        
        logger.info(f"Querying funds for account: {self.current_acc_id}, env: {self.trade_env}, market: {self.market}")
        info = get_account_info(self.current_acc_id, self.trade_env, self.market)
        logger.info(f"Account info received: {info}")
        
        info = get_account_info(self.current_acc_id, self.trade_env, self.market)
        if info is not None and not info.empty:
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
        else:
            self.display_results("无法获取账户信息")

    def enable_real_time_notifications(self):
        if not self.check_moomoo_connection():
            return
        message = "实时通知功能需要注册用户并付费开通。\n根据discord群的喊单记录直接调用解析指令并生成购买计划\n请联系作者了解更多信息。"
        self.display_results(message)
        messagebox.showinfo("实时通知", message)

    def place_order_by_plan(self):
        if not self.check_moomoo_connection():
            return
        
        current_result = self.result_text.get("1.0", tk.END).strip()
        
        if not current_result or "错误" in current_result:
            message = "当前没有有效的购买计划。请先运行计算。"
            self.display_results(message)
            return
        
        # 从计算结果中提取标的
        lines = current_result.split('\n')
        symbol_line = next((line for line in lines if line.startswith("标的:")), None)
        if symbol_line:
            self.current_symbol = symbol_line.split(":")[1].strip()
        
        if not self.current_symbol:
            message = "无法识别当前标的。请确保已正确计算并显示计划。"
            self.display_results(message)
            return
        
        # 解析计算结果以获取计划细节
        plan = []
        for line in lines:
            if "价格:" in line and "购买股数:" in line:
                parts = line.split(",")
                if len(parts) >= 2:
                    price = float(parts[0].split(":")[1].strip())
                    quantity = int(parts[1].split(":")[1].strip())
                    plan.append({"price": price, "quantity": quantity})
        
        if not plan:
            message = "无法解析购买计划。请确保已正确计算并显示计划。"
            self.display_results(message)
            return
        
        env_str = "真实" if self.trade_env == TrdEnv.REAL else "模拟"
        market_str = "美股" if self.market == TrdMarket.US else "港股"
        message = f"当前连接: {market_str}{env_str}账户\n"
        message += f"准备按计划为标的 {self.current_symbol} 下单。\n"
        message += "注意：这是在模拟系统中进行的测试，实际下单风险自负。\n\n"
        message += "当前计划：\n"
        message += f"标的：{self.current_symbol}\n"
        message += "购买计划：\n"
        for item in plan:
            message += f"  价格: {item['price']:.2f}, 数量: {item['quantity']}\n"
        
        message += "\n是否确认按此计划下单？"
        
        if messagebox.askyesno("确认下单", message):
            # 这里应该是实际下单的逻辑，目前我们只是显示一个确认消息
            self.display_results(f"模拟下单成功！实际环境中，订单将按计划执行。\n当前连接: {market_str}{env_str}账户")
            self.update_status(f"Moomoo API - {market_str}{env_str}账户 - 模拟下单完成")
        else:
            self.display_results(f"已取消下单。\n当前连接: {market_str}{env_str}账户")

    def query_positions(self):
        if not self.check_moomoo_connection():
            return
        if self.current_acc_id is None:
            self.display_results("无法获取账户信息")
            return
        
        positions = get_positions(self.current_acc_id, self.trade_env, self.market)
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
        
        orders = get_history_orders(self.current_acc_id, self.trade_env, self.market)
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

    def check_moomoo_connection(self):
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

    def process_instruction(self, instruction: str) -> None:
        try:
            parsed_instruction = parse_trading_instruction(instruction)
            if parsed_instruction['symbol'] and parsed_instruction['current_price'] and parsed_instruction['stop_loss']:
                self.current_symbol = parsed_instruction['symbol']
                self.initial_price_var.set(str(parsed_instruction['current_price']))
                self.stop_loss_price_var.set(str(parsed_instruction['stop_loss']))
                
                self._run_normal_calculation()
                
                instruction_info = f"原始指令: {instruction}\n"
                instruction_info += f"解析结果: 标的={parsed_instruction['symbol']}, "
                instruction_info += f"当前价格={parsed_instruction['current_price']:.2f}, "
                instruction_info += f"止损价格={parsed_instruction['stop_loss']:.2f}\n\n"
                
                current_result = self.result_text.get("1.0", tk.END)
                self.display_results(instruction_info + current_result)
                self.current_symbol = self.symbol_var.get() if hasattr(self, 'symbol_var') else None
            else:
                raise ValueError("指令中缺少必要的信息")
        except Exception as e:
            error_message = f"处理指令时出错: {str(e)}"
            self.update_status(error_message)
            self.display_results(error_message)
            logger.error(error_message, exc_info=True)

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
        self.is_closing = True
        self.save_user_settings()
        self.master.destroy()

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