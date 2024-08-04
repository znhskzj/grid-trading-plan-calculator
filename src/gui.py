import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import csv
from datetime import datetime
import logging
import os
from .calculations import run_calculation, calculate_with_reserve
from .config import load_config
from .utils import exception_handler

logger = logging.getLogger(__name__)


def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class App:
    def __init__(self, master, config):
        self.master = master
        self.config = config
        self.setup_variables()
        self.create_widgets()
        self.setup_layout()

    def setup_variables(self):
        self.funds_var = tk.StringVar(value=self.config['funds'])
        self.initial_price_var = tk.StringVar(value=self.config['initial_price'])
        self.stop_loss_price_var = tk.StringVar(value=self.config['stop_loss_price'])
        self.num_grids_var = tk.StringVar(value=self.config['num_grids'])
        self.allocation_method_var = tk.StringVar(value=self.config['allocation_method'])

    def create_widgets(self):
        # 创建输入框和标签
        tk.Label(self.master, text="总资金:").grid(row=0, column=0, sticky="e")
        self.funds_entry = tk.Entry(self.master, textvariable=self.funds_var, validate="key",
                                    validatecommand=(self.master.register(self.validate_float_input), '%d', '%P'))
        self.funds_entry.grid(row=0, column=1, sticky="ew")

        tk.Label(self.master, text="初始价格:").grid(row=1, column=0, sticky="e")
        self.initial_price_entry = tk.Entry(
            self.master, textvariable=self.initial_price_var, validate="key",
            validatecommand=(self.master.register(self.validate_float_input),
                             '%d', '%P'))
        self.initial_price_entry.grid(row=1, column=1, sticky="ew")

        tk.Label(self.master, text="止损价格:").grid(row=2, column=0, sticky="e")
        self.stop_loss_price_entry = tk.Entry(
            self.master, textvariable=self.stop_loss_price_var, validate="key",
            validatecommand=(self.master.register(self.validate_float_input),
                             '%d', '%P'))
        self.stop_loss_price_entry.grid(row=2, column=1, sticky="ew")

        tk.Label(self.master, text="网格数量:").grid(row=3, column=0, sticky="e")
        self.num_grids_entry = tk.Entry(self.master, textvariable=self.num_grids_var, validate="key",
                                        validatecommand=(self.master.register(self.validate_int_input), '%d', '%P'))
        self.num_grids_entry.grid(row=3, column=1, sticky="ew")

        tk.Label(self.master, text="分配方式:").grid(row=4, column=0, sticky="e")
        tk.Radiobutton(self.master, text="等金额分配", variable=self.allocation_method_var,
                       value="0").grid(row=4, column=1, sticky="w")
        tk.Label(self.master, text="均匀分配资金").grid(row=4, column=2, sticky="w")
        tk.Radiobutton(self.master, text="等比例分配", variable=self.allocation_method_var,
                       value="1").grid(row=5, column=1, sticky="w")
        tk.Label(self.master, text="指数增长分配").grid(row=5, column=2, sticky="w")
        tk.Radiobutton(self.master, text="线性加权", variable=self.allocation_method_var,
                       value="2").grid(row=6, column=1, sticky="w")
        tk.Label(self.master, text="线性增长分配").grid(row=6, column=2, sticky="w")

        # 创建按钮
        self.button_frame = tk.Frame(self.master)
        self.button_frame.grid(row=7, column=0, columnspan=3, pady=5)

        self.calculate_button = tk.Button(self.button_frame, text="不保留资金计算", command=self.run_calculation)
        self.calculate_button.grid(row=0, column=0, padx=5)

        self.reserve_10_button = tk.Button(self.button_frame, text="保留10%计算",
                                           command=lambda: self.calculate_with_reserve(10))
        self.reserve_10_button.grid(row=0, column=1, padx=5)

        self.reserve_20_button = tk.Button(self.button_frame, text="保留20%计算",
                                           command=lambda: self.calculate_with_reserve(20))
        self.reserve_20_button.grid(row=0, column=2, padx=5)

        self.save_button = tk.Button(self.master, text="保存为CSV", command=self.save_to_csv)
        self.save_button.grid(row=8, column=1, pady=5)

        self.reset_button = tk.Button(self.master, text="重置为默认值", command=self.reset_to_default)
        self.reset_button.grid(row=8, column=2, pady=5)

        # 创建结果显示区域
        self.result_text = scrolledtext.ScrolledText(self.master, height=20, width=50)
        self.result_text.grid(row=9, column=0, columnspan=3, sticky="nsew")

    def setup_layout(self):
        for i in range(3):
            self.master.grid_columnconfigure(i, weight=1)
        for i in range(10):
            self.master.grid_rowconfigure(i, weight=1)

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
        config = load_config(config_path)  # 假设 load_config 函数在 config.py 中定义
        self.funds_var.set(str(config['funds']))
        self.initial_price_var.set(str(config['initial_price']))
        self.stop_loss_price_var.set(str(config['stop_loss_price']))
        self.num_grids_var.set(str(config['num_grids']))
        self.allocation_method_var.set(str(config['allocation_method']))

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
