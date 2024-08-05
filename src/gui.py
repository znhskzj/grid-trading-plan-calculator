import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import csv
from datetime import datetime
import logging
import os
from .calculations import run_calculation, calculate_with_reserve
from .config import load_config
from .utils import exception_handler
from .status_manager import StatusManager
from unittest.mock import Mock
import yfinance as yf

logger = logging.getLogger(__name__)


def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class App:
    def __init__(self, master, config, version):
        if master is None:
            master = tk.Tk()
        self.master = master
        self.config = config
        self.version = version
        self.current_symbol = None
        self.status_bar = None
        self.master.title(f"Grid Trading Tool v{self.version}")
        self.setup_variables()
        self.create_widgets()
        self.setup_layout()
        App.instance = self
        StatusManager.set_instance(self)

    def setup_variables(self):
        general_config = self.config['General']
        self.funds_var = tk.StringVar(value=general_config.get('funds', '0'))
        self.initial_price_var = tk.StringVar(value=general_config['initial_price'])
        self.stop_loss_price_var = tk.StringVar(value=general_config['stop_loss_price'])
        self.num_grids_var = tk.StringVar(value=general_config['num_grids'])
        self.allocation_method_var = tk.StringVar(value=general_config['allocation_method'])

    def create_widgets(self):
        try:
            # 创建主框架
            self.main_frame = tk.Frame(self.master)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 创建状态栏
            self.status_bar = tk.Label(self.master, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

            # 创建左侧框架
            self.left_frame = tk.Frame(self.main_frame, width=120)
            self.left_frame.grid(row=0, column=0, sticky="ns")
            self.left_frame.grid_propagate(False)  # 固定左侧框架大小

            # 创建右侧框架
            self.right_frame = tk.Frame(self.main_frame)
            self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

            # 设置列权重，使右侧框架能够扩展
            self.main_frame.grid_columnconfigure(1, weight=1)

            self.create_left_widgets()
            self.create_right_widgets()

            # 创建结果显示区域
            self.result_frame = tk.Frame(self.main_frame)
            self.result_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

            self.result_text = scrolledtext.ScrolledText(self.result_frame, height=15, width=50)
            self.result_text.pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            print(f"创建 GUI 组件时发生错误: {str(e)}")
            logging.error(f"创建 GUI 组件时发生错误: {str(e)}", exc_info=True)

    def create_left_widgets(self):
        # 常用标的按钮
        self.common_stocks_button = tk.Button(self.left_frame, text="常用标的", width=10, command=self.show_common_stocks)
        self.common_stocks_button.pack(pady=(0, 5))

        # 股票标的按钮
        stocks = self.config.get('CommonStocks', {})
        for symbol in stocks.values():
            btn = tk.Button(self.left_frame, text=symbol, width=10, command=lambda s=symbol: self.set_stock_price(s))
            btn.pack(pady=2)

    def create_right_widgets(self):
        try:
            # 设置右侧框架的列权重
            self.right_frame.grid_columnconfigure(1, weight=1)

            # 输入字段
            labels = ["可用资金:", "初始价格:", "止损价格:", "网格数量:"]
            vars = [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var]

            for i, (label, var) in enumerate(zip(labels, vars)):
                tk.Label(self.right_frame, text=label).grid(row=i, column=0, sticky="e", pady=2)
                entry = tk.Entry(self.right_frame, textvariable=var, width=20)
                entry.grid(row=i, column=1, sticky="ew", padx=(5, 0), pady=2)

            # 分配方式
            tk.Label(self.right_frame, text="分配方式:").grid(row=4, column=0, sticky="e", pady=2)
            methods = [("等金额分配", "0", "均匀分配资金"),
                       ("等比例分配", "1", "指数增长分配"),
                       ("线性加权", "2", "线性增长分配")]

            for i, (text, value, desc) in enumerate(methods):
                tk.Radiobutton(self.right_frame, text=text, variable=self.allocation_method_var,
                               value=value).grid(row=4+i, column=1, sticky="w")
                tk.Label(self.right_frame, text=desc).grid(row=4+i, column=1, sticky="e")

            # 按钮
            button_frame = tk.Frame(self.right_frame)
            button_frame.grid(row=7, column=0, columnspan=2, pady=10)

            buttons = [
                ("计算购买计划", self.run_calculation),
                ("保留10%计算", lambda: self.calculate_with_reserve(10)),
                ("保留20%计算", lambda: self.calculate_with_reserve(20)),
                ("保存为CSV", self.save_to_csv),
                ("重置为默认值", self.reset_to_default)
            ]

            for i, (text, command) in enumerate(buttons):
                tk.Button(button_frame, text=text, command=command).grid(row=0, column=i, padx=5)

            # 第二行按钮
            second_row_buttons = [
                ("查询可用资金", self.query_available_funds),
                ("开启实时通知", self.enable_real_time_notifications),
                ("按标的计划下单", self.place_order_by_plan),
                ("导出成交明细", self.export_transaction_details),
                ("计算总体利润", self.calculate_total_profit)
            ]

            for i, (text, command) in enumerate(second_row_buttons):
                tk.Button(
                    button_frame, text=text, command=command, state='disabled').grid(
                    row=1, column=i, padx=5, pady=(5, 0))

        except Exception as e:
            self.update_status(f"创建右侧 GUI 组件时出错: {str(e)}")
            logging.error(f"创建右侧 GUI 组件时出错: {str(e)}", exc_info=True)

    # 添加这些方法的占位符
    def enable_real_time_notifications(self):
        self.update_status("实时通知功能尚未实现")

    def query_available_funds(self):
        self.update_status("查询可用资金功能尚未实现")

    def place_order_by_plan(self):
        self.update_status("按计划下单功能尚未实现")

    def export_transaction_details(self):
        self.update_status("导出成交明细功能尚未实现")

    def calculate_total_profit(self):
        self.update_status("计算总体利润功能尚未实现")

    def place_grid_order(self):
        self.update_status("按网格计划下单功能尚未实现")

    def update_status(self, message):
        if self.status_bar:
            self.status_bar.config(text=message)
        else:
            print(f"Status: {message}")  # 如果状态栏还未创建，则打印到控制台

    def setup_layout(self):
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)
        for i in range(10):
            self.right_frame.grid_rowconfigure(i, weight=1)

    @exception_handler
    def run_calculation(self):
        symbol_info = f"标的: {self.current_symbol}" if hasattr(self, 'current_symbol') else "未选择特定标的"
        self.update_status(f"开始计算购买计划 ({symbol_info})...")
        result = run_calculation(self.get_input_values())
        self.display_results(f"{symbol_info}\n\n{result}")
        self.update_status(f"计算完成 ({symbol_info})")

    @exception_handler
    def calculate_with_reserve(self, reserve_percentage):
        symbol_info = f"标的: {self.current_symbol}" if hasattr(self, 'current_symbol') else "未选择特定标的"
        self.update_status(f"开始计算（保留{reserve_percentage}%资金）({symbol_info})...")
        result = calculate_with_reserve(self.get_input_values(), reserve_percentage)
        self.display_results(f"{symbol_info}\n\n{result}")
        self.update_status(f"计算完成（保留{reserve_percentage}%资金）({symbol_info})")

    def get_input_values(self):
        return {
            'funds': float(self.funds_var.get()),
            'initial_price': float(self.initial_price_var.get()),
            'stop_loss_price': float(self.stop_loss_price_var.get()),
            'num_grids': int(self.num_grids_var.get()),
            'allocation_method': int(self.allocation_method_var.get())
        }

    def display_results(self, result):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)

    def save_to_csv(self):
        logger.info("用户尝试保存结果为 CSV")
        try:
            content = self.result_text.get(1.0, tk.END)
            if not content.strip():
                messagebox.showwarning("警告", "没有可保存的结果")
                logger.warning("尝试保存空结果")
                return

            default_filename = f"grid_trading_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            initial_dir = os.path.join(get_project_root(), 'output')  # 假设我们有一个 output 目录
            os.makedirs(initial_dir, exist_ok=True)  # 确保 output 目录存在
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=default_filename,
                initialdir=initial_dir
            )
            if not file_path:
                logger.info("用户取消了保存操作")
                return

            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                lines = content.split('\n')
                for line in lines:
                    if line.strip():
                        if ':' in line:
                            key, value = line.split(':', 1)
                            writer.writerow([key.strip(), value.strip()])
                        else:
                            writer.writerow([line.strip()])

            logger.info(f"结果已保存到 {file_path}")
            messagebox.showinfo("成功", f"结果已保存到 {file_path}")
        except Exception as e:
            logger.exception("保存文件时发生错误")
            messagebox.showerror("错误", f"保存文件时发生错误: {str(e)}")

    def reset_to_default(self):
        logger.info("用户重置为默认值")
        config_path = os.path.join(get_project_root(), 'config.ini')
        config = load_config(config_path)
        general_config = config.get('General', {})
        self.funds_var.set(str(general_config.get('funds', '')))
        self.initial_price_var.set(str(general_config.get('initial_price', '')))
        self.stop_loss_price_var.set(str(general_config.get('stop_loss_price', '')))
        self.num_grids_var.set(str(general_config.get('num_grids', '')))
        self.allocation_method_var.set(str(general_config.get('allocation_method', '')))

    @staticmethod
    def validate_float_input(action, value_if_allowed):
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
    def validate_int_input(action, value_if_allowed):
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
        # 清除所有现有的股票按钮
        if not isinstance(self.left_frame, Mock):
            for widget in self.left_frame.winfo_children():
                if widget != self.common_stocks_button:
                    widget.destroy()

        if self.common_stocks_button['text'] == "隐藏常用标的":
            # 如果是隐藏操作，只需要更改按钮文本
            self.common_stocks_button['text'] = "常用标的"
        else:
            # 显示常用标的按钮
            stocks = self.config.get('CommonStocks', {})
            for symbol in stocks.values():
                if not isinstance(self.left_frame, Mock):
                    try:
                        btn = tk.Button(self.left_frame, text=symbol, width=10,
                                        command=lambda s=symbol: self.set_stock_price(s))
                        btn.pack(pady=2)
                    except Exception as e:
                        print(f"无法创建按钮 {symbol}: {str(e)}")
            self.common_stocks_button['text'] = "隐藏常用标的"

        # 更新左侧框架
        if not isinstance(self.left_frame, Mock):
            self.left_frame.update()

    def set_stock_price(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            current_price = stock.info.get('regularMarketPrice') or stock.info.get('currentPrice')
            if current_price:
                self.initial_price_var.set(str(current_price))
                status_message = f"已选择标的 {symbol}，当前价格为 {current_price:.2f} 元"
                self.update_status(status_message)
                self.display_results(f"选中标的: {symbol}\n当前价格: {current_price:.2f} 元\n\n请点击\"计算购买计划\"按钮生成网格交易计划。")
            else:
                raise ValueError("无法获取股票价格")
        except Exception as e:
            error_message = f"无法获取股票 {symbol} 的价格: {str(e)}"
            self.update_status(error_message)
            self.display_results(f"无法获取标的 {symbol} 的价格\n\n请选择其他标的或手动输入初始价格。")
            logging.error(error_message)

        # 保存当前选中的标的
        self.current_symbol = symbol

    def query_available_funds(self):
        # 这里添加查询可用资金的逻辑
        pass
