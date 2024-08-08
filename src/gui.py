# src/gui.py

import csv
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any

import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, simpledialog

from src.api_manager import APIManager
from src.calculations import (
    calculate_buy_plan, 
    run_calculation, 
    calculate_with_reserve,
    parse_trading_instruction, 
    calculate_grid_from_instruction,
    validate_inputs 
)
from src.config import save_user_config, load_user_config
from src.status_manager import StatusManager
from src.utils import exception_handler, compare_versions, get_latest_version

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
        self.config = config
        self.version = version
        self.current_symbol = None
        self.status_bar = None
        self.master.title(f"Grid Trading Tool v{self.version}")

        self.is_closing = False  # 添加这一行

        self.user_config = load_user_config()
        self.available_apis = config.get('AvailableAPIs', {}).get('apis', ['yahoo', 'alpha_vantage'])
        self.api_choice = tk.StringVar(value='yahoo')
        self.alpha_vantage_key = tk.StringVar(value=config.get('API', {}).get('alpha_vantage_key', ''))
        self.setup_variables()
        self.instruction_var = tk.StringVar()
        self.create_widgets()
        self.setup_layout()
        self.load_user_settings()

        self.api_manager = APIManager(self.api_choice.get(), self.alpha_vantage_key.get())
        
        App.instance = self
        StatusManager.set_instance(self)
        
        self.master.geometry("800x650")  # 设置固定窗口大小
        self.master.minsize(800, 650)    # 设置最小大小
        self.master.maxsize(800, 650)    # 设置最大大小
        self.master.resizable(False, False)  # 禁止调整窗口大小
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_variables(self) -> None:
        """设置GUI变量"""
        general_config = self.config['General']
        self.funds_var = tk.StringVar(value=general_config.get('funds', '0'))
        self.initial_price_var = tk.StringVar(value=general_config['initial_price'])
        self.stop_loss_price_var = tk.StringVar(value=general_config['stop_loss_price'])
        self.num_grids_var = tk.StringVar(value=general_config['num_grids'])
        self.allocation_method_var = tk.StringVar(value=general_config['allocation_method'])

    def create_widgets(self) -> None:
        """创建并布局所有GUI组件"""
        try:
            self.create_main_frame()
            self.create_status_bar()
            self.create_left_frame()
            self.create_right_frame()
            self.create_result_frame()
        except Exception as e:
            logger.error(f"创建 GUI 组件时发生错误: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"创建 GUI 组件时发生错误: {str(e)}")

    def create_main_frame(self) -> None:
        """创建主框架"""
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)

    def create_status_bar(self) -> None:
        """创建状态栏"""
        self.status_bar = tk.Label(self.master, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))  # 添加一些上边距

    def create_left_frame(self) -> None:
        """创建左侧框架"""
        self.left_frame = tk.Frame(self.main_frame, width=120)
        self.left_frame.grid(row=0, column=0, sticky="ns")
        self.left_frame.grid_propagate(False)
        self.create_left_widgets()

    def create_right_frame(self) -> None:
        """创建右侧框架"""
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.right_frame.grid_columnconfigure(1, weight=1)
        self.create_right_widgets()

    def create_result_frame(self) -> None:
        """创建结果显示区域"""
        self.result_frame = tk.Frame(self.main_frame, bd=1, relief=tk.SUNKEN)  # 添加边框
        self.result_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 10), padx=10)  # 增加边距
        
        # 创建一个带滚动条的文本区域
        text_container = tk.Frame(self.result_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)  # 添加内部边距
        
        self.result_text = tk.Text(text_container, height=10, wrap=tk.WORD)  # 减少高度
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_text.yview)

    def create_left_widgets(self) -> None:
        """创建左侧组件"""
        self.common_stocks_button = tk.Button(self.left_frame, text="常用标的", width=10, command=self.show_common_stocks)
        self.common_stocks_button.pack(pady=(0, 5))

        stocks = self.config.get('CommonStocks', {})
        for symbol in stocks.values():
            btn = tk.Button(self.left_frame, text=symbol, width=10,
                            command=lambda s=symbol: self.set_stock_price(s))
            btn.pack(pady=2)

    def create_right_widgets(self) -> None:
        """创建右侧组件"""
        self.create_input_fields()
        
        # 创建一个框架来容纳分配方式和API选择
        option_frame = tk.Frame(self.right_frame)
        option_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 10))  # 增加上下边距
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_columnconfigure(1, weight=1)
        
        # 在左侧创建分配方式
        self.create_allocation_method_widgets(option_frame)
        
        # 在右侧创建API选择
        self.create_api_widgets(option_frame)
        
        self.create_buttons()

    def create_input_fields(self) -> None:
        labels = ["可用资金:", "初始价格:", "止损价格:", "网格数量:", "交易指令:"]
        vars = [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var, self.instruction_var]

        for i, (label, var) in enumerate(zip(labels, vars)):
            tk.Label(self.right_frame, text=label).grid(row=i, column=0, sticky="e", pady=2)
            entry = tk.Entry(self.right_frame, textvariable=var, width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=(5, 0), pady=2)

    def create_allocation_method_widgets(self, parent_frame) -> None:
        """创建分配方式组件"""
        allocation_frame = tk.LabelFrame(parent_frame, text="分配方式")
        allocation_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        methods = [("等金额分配", "0", "均匀分配资金"),
                ("等比例分配", "1", "指数增长分配"),
                ("线性加权", "2", "线性增长分配")]

        for i, (text, value, desc) in enumerate(methods):
            rb = tk.Radiobutton(allocation_frame, text=text, variable=self.allocation_method_var, value=value)
            rb.grid(row=i, column=0, sticky="w")
            tk.Label(allocation_frame, text=desc).grid(row=i, column=1, sticky="w", padx=(10, 0))

    def create_buttons(self) -> None:
        """创建按钮"""
        button_frame = tk.Frame(self.right_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10)

        buttons = [
            ("计算购买计划", self.run_calculation),
            ("保留10%计算", lambda: self.calculate_with_reserve(10)),
            ("保留20%计算", lambda: self.calculate_with_reserve(20)),
            ("保存为CSV", self.save_to_csv),
            ("重置为默认值", self.reset_to_default)
        ]

        for i, (text, command) in enumerate(buttons):
            tk.Button(button_frame, text=text, command=command).grid(row=0, column=i, padx=5)

        self.create_second_row_buttons(button_frame)

    def create_second_row_buttons(self, button_frame: tk.Frame) -> None:
        """创建第二行按钮"""
        second_row_buttons = [
            ("查询可用资金", self.query_available_funds),
            ("开启实时通知", self.enable_real_time_notifications),
            ("按标的计划下单", self.place_order_by_plan),
            ("导出成交明细", self.export_transaction_details),
            ("计算总体利润", self.calculate_total_profit)
        ]

        for i, (text, command) in enumerate(second_row_buttons):
            tk.Button(button_frame, text=text, command=command, state='disabled').grid(
                row=1, column=i, padx=5, pady=(5, 0))
            
    @exception_handler
    def run_calculation(self) -> None:
        instruction = self.instruction_var.get().strip()
        if instruction:
            self.process_instruction(instruction)
        else:
            self._run_normal_calculation()

    @exception_handler
    def calculate_with_reserve(self, reserve_percentage: int) -> None:
        """执行保留部分资金的计算"""
        input_values = self.get_input_values()
        
        if self.current_symbol:
            symbol_info = f"标的: {self.current_symbol}"
            self.update_status(f"开始计算（保留{reserve_percentage}%资金）({symbol_info})...")
        else:
            self.update_status(f"开始计算（保留{reserve_percentage}%资金）...")
        
        result = calculate_with_reserve(input_values, reserve_percentage)
        
        if self.current_symbol:
            self.display_results(f"{symbol_info}\n\n{result}")
        else:
            self.display_results(result)
        
        self.update_status(f"计算完成（保留{reserve_percentage}%资金）")

    def get_input_values(self) -> Dict[str, Any]:
        """获取输入值"""
        return {
            'funds': float(self.funds_var.get()),
            'initial_price': float(self.initial_price_var.get()),
            'stop_loss_price': float(self.stop_loss_price_var.get()),
            'num_grids': int(self.num_grids_var.get()),
            'allocation_method': int(self.allocation_method_var.get())
        }

    def display_results(self, result: str) -> None:
        """显示计算结果"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)
        self.result_text.see(tk.END)  # 滚动到最后

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
        """重置所有设置到默认状态"""
        logger.info("用户重置为默认值")
        self.api_choice.set('yahoo')
        self.allocation_method_var.set(self.config['General']['allocation_method'])
        self.funds_var.set(self.config['General']['funds'])
        self.initial_price_var.set(self.config['General']['initial_price'])
        self.stop_loss_price_var.set(self.config['General']['stop_loss_price'])
        self.num_grids_var.set(self.config['General']['num_grids'])
        self.update_common_stocks(self.config.get('CommonStocks', {}).values())
        self.current_symbol = None  # 重置当前选中的标的
        self.instruction_var.set("") # 清空交易指令输入框
        
        # 保留 Alpha Vantage API key
        alpha_vantage_key = self.alpha_vantage_key.get()
        self.user_config = {}
        if alpha_vantage_key:
            self.user_config['API'] = {'alpha_vantage_key': alpha_vantage_key}
        
        self.save_user_settings()
        reset_message = "所有设置已重置为默认值"
        self.update_status(reset_message)
        self.display_results(reset_message)

    def create_api_widgets(self, parent_frame) -> None:
        """创建API选择组件"""
        api_frame = tk.LabelFrame(parent_frame, text="API 选择")
        api_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)

        for i, api in enumerate(self.available_apis):
            tk.Radiobutton(api_frame, text=api.capitalize(), variable=self.api_choice, 
                        value=api, command=self.on_api_change).grid(row=i, column=0, sticky="w")

    def on_api_change(self) -> None:
        """API选择变更处理"""
        if self.api_choice.get() == 'alpha_vantage':
            messagebox.showinfo("Alpha Vantage API 提示", 
                                "请注意：Alpha Vantage 免费版 API 有每日请求次数限制。\n"
                                "建议仅在必要时使用，以避免达到限制。")
            if not self.alpha_vantage_key.get():
                self.prompt_for_alpha_vantage_key()
        
        # 只有在 API 真正改变时才更新
        if self.api_manager.api_choice != self.api_choice.get() or \
           (self.api_choice.get() == 'alpha_vantage' and 
            self.api_manager.alpha_vantage_key != self.alpha_vantage_key.get()):
            self.api_manager = APIManager(self.api_choice.get(), self.alpha_vantage_key.get())
            self.save_user_settings()
            self.update_status(f"已切换到 {self.api_choice.get()} API")

    def prompt_for_alpha_vantage_key(self) -> None:
        """提示输入Alpha Vantage API密钥"""
        new_key = simpledialog.askstring("Alpha Vantage API Key",
                                        "请输入您的 Alpha Vantage API Key:",
                                        initialvalue=self.alpha_vantage_key.get())
        if new_key:
            self.alpha_vantage_key.set(new_key)
            self.save_user_settings()
        elif not self.alpha_vantage_key.get():
            # 如果用户取消输入且之前没有设置key，切换回Yahoo
            self.api_choice.set('yahoo')
            messagebox.showinfo("API 选择", "由于未提供 Alpha Vantage API Key，已切换回 Yahoo Finance API。")
            self.save_user_settings()

    def save_user_settings(self) -> None:
        """保存用户设置"""
        if self.is_closing:
            return
        
        # 保存 API 选择
        self.user_config['API'] = {
            'choice': self.api_choice.get(),
        }
        
        # 无论当前选择的是哪个 API，都保存 Alpha Vantage key（如果存在）
        alpha_vantage_key = self.alpha_vantage_key.get()
        if alpha_vantage_key:
            self.user_config['API']['alpha_vantage_key'] = alpha_vantage_key
        
        self.user_config['allocation_method'] = self.allocation_method_var.get()
        self.user_config['common_stocks'] = [btn['text'] for btn in self.left_frame.winfo_children() if isinstance(btn, tk.Button) and btn != self.common_stocks_button]
        
        save_user_config(self.user_config)
        logger.info("用户设置已自动保存")

    def load_user_settings(self) -> None:
        """加载用户设置"""
        if 'API' in self.user_config:
            self.api_choice.set(self.user_config['API'].get('choice', 'yahoo'))
            # 如果存在 Alpha Vantage key，总是加载它
            if 'alpha_vantage_key' in self.user_config['API']:
                self.alpha_vantage_key.set(self.user_config['API']['alpha_vantage_key'])
        
        if 'allocation_method' in self.user_config:
            self.allocation_method_var.set(self.user_config['allocation_method'])
        
        if 'common_stocks' in self.user_config:
            self.update_common_stocks(self.user_config['common_stocks'])
        
        # 如果选择了 Alpha Vantage 但没有 API key，提示用户输入
        if self.api_choice.get() == 'alpha_vantage' and not self.alpha_vantage_key.get():
            self.prompt_for_alpha_vantage_key()

    def update_common_stocks(self, stocks: list[str]) -> None:
        """更新常用股票列表"""
        for widget in self.left_frame.winfo_children():
            if widget != self.common_stocks_button:
                widget.destroy()
        
        for symbol in stocks:
            btn = tk.Button(self.left_frame, text=symbol, width=10,
                            command=lambda s=symbol: self.set_stock_price(s))
            btn.pack(pady=2)

    def set_stock_price(self, symbol: str) -> None:
        api = self.api_choice.get()
        try:
            self.api_manager = APIManager(api, self.alpha_vantage_key.get())
            current_price, api_used = self.api_manager.get_stock_price(symbol)
            if current_price:
                current_price = round(current_price, 2)  # 将价格四舍五入到两位小数
                stop_loss_price = round(current_price * 0.9, 2)
                self.initial_price_var.set(f"{current_price:.2f}")  # 使用字符串格式化确保显示两位小数
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
            else:
                raise ValueError(f"无法从 {api_used} 获取有效的价格数据")
        except Exception as e:
            error_message = f"使用 {api} 获取股票 {symbol} 的价格失败: {str(e)}"
            self.update_status(error_message)
            self.display_results(f"无法获取标的 {symbol} 的价格\n\n错误信息: {error_message}\n\n请检查网络连接、API key 是否有效，或者股票代码是否正确。")
            logger.error(error_message, exc_info=True)
        
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

    def show_common_stocks(self):
        if self.common_stocks_button['text'] == "隐藏常用标的":
            self.common_stocks_button['text'] = "常用标的"
            for widget in self.left_frame.winfo_children():
                if widget != self.common_stocks_button:
                    widget.destroy()
        else:
            # 清除现有的标的按钮
            for widget in self.left_frame.winfo_children():
                if widget != self.common_stocks_button:
                    widget.destroy()
            
            stocks = self.config.get('CommonStocks', {})
            for symbol in stocks.values():
                btn = tk.Button(self.left_frame, text=symbol, width=10,
                                command=lambda s=symbol: self.set_stock_price(s))
                btn.pack(pady=2)
            self.common_stocks_button['text'] = "隐藏常用标的"
        
        self.left_frame.update()

    def query_available_funds(self) -> None:
        """查询可用资金（待实现）"""
        self.update_status("查询可用资金功能尚未实现")

    def enable_real_time_notifications(self) -> None:
        """启用实时通知（待实现）"""
        self.update_status("实时通知功能尚未实现")

    def place_order_by_plan(self) -> None:
        """按计划下单（待实现）"""
        self.update_status("按计划下单功能尚未实现")

    def export_transaction_details(self) -> None:
        """导出交易明细（待实现）"""
        self.update_status("导出成交明细功能尚未实现")

    def calculate_total_profit(self) -> None:
        """计算总体利润（待实现）"""
        self.update_status("计算总体利润功能尚未实现")

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
        self.main_frame.grid_rowconfigure(0, weight=3)  # 给上半部分更多空间
        self.main_frame.grid_rowconfigure(1, weight=1)  # 给结果显示区域一些空间
        
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
            else:
                raise ValueError("指令中缺少必要的信息")
        except Exception as e:
            error_message = f"处理指令时出错: {str(e)}"
            self.update_status(error_message)
            self.display_results(error_message)
            logger.error(error_message, exc_info=True)

    def _run_normal_calculation(self) -> None:
        input_values = self.get_input_values()
        
        # 验证输入
        error_message = validate_inputs(**input_values)
        if error_message:
            self.update_status(error_message)
            self.display_results(f"错误: {error_message}\n\n请调整输入参数后重试。")
            return

        if self.current_symbol:
            symbol_info = f"标的: {self.current_symbol}"
            self.update_status(f"开始计算购买计划 ({symbol_info})...")
            result = run_calculation(input_values)
            self.display_results(f"{symbol_info}\n\n{result}")
        else:
            self.update_status("开始计算购买计划...")
            result = run_calculation(input_values)
            self.display_results(result)
        
        self.update_status("计算完成")

    def on_closing(self):
        self.is_closing = True
        self.save_user_settings()
        self.master.destroy()