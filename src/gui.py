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
import yfinance as yf

logger = logging.getLogger(__name__)


def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class App:
    def __init__(self, master, config, version):
        self.master = master
        self.config = config
        self.version = version
        master.title(f"Grid Trading Tool v{self.version}")
        self.setup_variables()
        self.create_widgets()
        self.setup_layout()
        App.instance = self
        StatusManager.set_instance(self)

    def setup_variables(self):
        general_config = self.config['General']
        self.funds_var = tk.StringVar(value=general_config['funds'])
        self.initial_price_var = tk.StringVar(value=general_config['initial_price'])
        self.stop_loss_price_var = tk.StringVar(value=general_config['stop_loss_price'])
        self.num_grids_var = tk.StringVar(value=general_config['num_grids'])
        self.allocation_method_var = tk.StringVar(value=general_config['allocation_method'])

    def create_widgets(self):
        # 创建主框架
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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

        # 创建状态栏
        self.status_bar = tk.Label(self.master, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

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

        # API 相关按钮（禁用状态）
        api_frame = tk.Frame(self.right_frame)
        api_frame.grid(row=8, column=0, columnspan=2, pady=5)

        tk.Button(api_frame, text="查询可用资金", state='disabled').grid(row=0, column=0, padx=5)
        tk.Button(api_frame, text="按计划下单", state='disabled').grid(row=0, column=1, padx=5)

    def update_status(self, message):
        self.status_bar.config(text=message)

    def setup_layout(self):
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)
        for i in range(10):
            self.right_frame.grid_rowconfigure(i, weight=1)

    @exception_handler
    def run_calculation(self):
        result = run_calculation(self.get_input_values())
        self.display_results(result)

    @exception_handler
    def calculate_with_reserve(self, reserve_percentage):
        result = calculate_with_reserve(self.get_input_values(), reserve_percentage)
        self.display_results(result)

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
        # 如果常用标的按钮已经显示，就隐藏它们
        if self.common_stocks_button['text'] == "隐藏常用标的":
            for widget in self.left_frame.winfo_children():
                if widget != self.common_stocks_button:
                    widget.pack_forget()
            self.common_stocks_button['text'] = "常用标的"
        else:
            # 否则，显示常用标的按钮
            stocks = self.config.get('CommonStocks', {})
            for symbol in stocks.values():
                btn = tk.Button(self.left_frame, text=symbol, width=10,
                                command=lambda s=symbol: self.set_stock_price(s))
                btn.pack(pady=2)
            self.common_stocks_button['text'] = "隐藏常用标的"

    def set_stock_price(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            current_price = stock.info.get('regularMarketPrice') or stock.info.get('currentPrice')
            if current_price:
                self.initial_price_var.set(str(current_price))
            else:
                raise ValueError("无法获取股票价格")
        except Exception as e:
            messagebox.showerror("错误", f"无法获取股票 {symbol} 的价格: {str(e)}")

    def query_available_funds(self):
        # 这里添加查询可用资金的逻辑
        pass

    def place_grid_order(self):
        # 这里添加按计划下单的逻辑
        pass

    # @classmethod
    # def update_calculation_status(cls, message):
    #     if hasattr(cls, 'instance') and cls.instance:
    #         cls.instance.update_status(message)
