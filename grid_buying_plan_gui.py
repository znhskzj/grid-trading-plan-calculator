"""
Grid Trading Plan Calculator
Version: 1.1.0
Author: (discord)zzann
Date: July 30, 2024

This program calculates and visualizes grid trading plans.
For more information, please refer to the README.md file.

License: MIT License
"""
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import numpy as np
import csv
import json
import logging
import os
from datetime import datetime

# 设置日志
logging.basicConfig(filename='grid_trading.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class InvalidInputError(Exception):
    pass


def load_config():
    config_file = 'config.json'
    default_config = {
        "funds": 50000,
        "initial_price": 26.7,
        "stop_loss_price": 25.5,
        "num_grids": 10,
        "allocation_method": 0
    }
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error(f"配置文件 {config_file} 格式错误，使用默认配置")
    else:
        logging.info(f"配置文件 {config_file} 不存在，使用默认配置")
    return default_config


def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    logging.info("配置已保存")


def validate_inputs(funds, initial_price, stop_loss_price, num_grids, allocation_method):
    if not isinstance(funds, (int, float)) or funds <= 0:
        raise InvalidInputError("总资金必须是正数")
    if not isinstance(initial_price, (int, float)) or initial_price <= 0:
        raise InvalidInputError("初始价格必须是正数")
    if not isinstance(stop_loss_price, (int, float)) or stop_loss_price <= 0:
        raise InvalidInputError("止损价格必须是正数")
    if not isinstance(num_grids, int) or num_grids <= 0:
        raise InvalidInputError("网格数量必须是正整数")
    if not isinstance(allocation_method, int) or allocation_method not in [0, 1, 2]:
        raise InvalidInputError("分配方式必须是0、1或2")
    if stop_loss_price >= initial_price:
        raise InvalidInputError("止损价格必须小于初始价格")
    if funds < initial_price:
        raise InvalidInputError("总资金必须大于初始价格")


def calculate_weights(prices, method, max_shares):
    if method == 0:  # 等金额分配
        weights = [1] * len(prices)
    elif method == 1:  # 等比例分配 - 指数增长策略
        weights = [np.exp(-price) for price in prices]
    elif method == 2:  # 线性加权 - 低价格更高权重
        weights = list(range(1, len(prices) + 1))
    else:
        raise ValueError("无效的分配方式")

    # 确保每个网格至少分配1股
    total_weight = sum(weights)
    min_shares = [max(1, int(max_shares * (weight / total_weight))) for weight in weights]

    return min_shares


def calculate_with_reserve(reserve_percentage):
    funds = float(funds_entry.get())
    reserved_funds = funds * (reserve_percentage / 100)
    available_funds = funds - reserved_funds
    run_calculation(available_funds, reserved_funds)


def calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids=10, allocation_method=0):
    validate_inputs(funds, initial_price, stop_loss_price, num_grids, allocation_method)

    logging.info(
        f"计算购买计划: 资金={funds}, 初始价格={initial_price}, 止损价格={stop_loss_price}, 网格数量={num_grids}, 分配方式={allocation_method}")

    max_price = initial_price
    min_price = stop_loss_price

    price_step = (max_price - min_price) / num_grids
    max_shares = int(funds / min_price)  # 使用最低价格计算最大可购买股数

    if max_shares < num_grids:
        num_grids = max_shares
        logging.warning(f"资金不足以分配到所有网格，已减少网格数量至 {num_grids}")

    buy_prices = np.linspace(max_price, min_price, num_grids)
    buy_quantities = calculate_weights(buy_prices, allocation_method, max_shares)

    # 调整购买数量，确保总金额不超过可用资金
    total_cost = sum(price * quantity for price, quantity in zip(buy_prices, buy_quantities))
    if total_cost > funds:
        scale_factor = funds / total_cost
        buy_quantities = [max(1, int(quantity * scale_factor)) for quantity in buy_quantities]

    buy_plan = [(round(price, 2), int(quantity)) for price, quantity in zip(buy_prices, buy_quantities)]

    # 检查是否有过多的1股购买
    single_share_count = sum(1 for _, quantity in buy_plan if quantity == 1)
    warning_message = ""
    if single_share_count > num_grids // 2:  # 如果超过一半的网格只买1股
        warning_message = "\n警告：当前参数可能不够合理，多个价位只购买1股。建议减少网格数量或增加总资金。"

    return buy_plan, warning_message


def run_calculation(available_funds=None, reserved_funds=0):
    try:
        total_funds = float(funds_entry.get())
        if available_funds is None:
            available_funds = total_funds
        initial_price = float(initial_price_entry.get())
        stop_loss_price = float(stop_loss_price_entry.get())
        num_grids = int(num_grids_entry.get())
        allocation_method = int(allocation_method_var.get())

        buy_plan, warning_message = calculate_buy_plan(
            available_funds, initial_price, stop_loss_price, num_grids, allocation_method)

        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"总资金: {total_funds:.2f}\n")
        if reserved_funds > 0:
            result_text.insert(tk.END, f"保留资金: {reserved_funds:.2f}\n")
            result_text.insert(tk.END, f"可用资金: {available_funds:.2f}\n")
        result_text.insert(tk.END, f"初始价格: {initial_price:.2f}\n")
        result_text.insert(tk.END, f"止损价格: {stop_loss_price:.2f}\n")
        result_text.insert(tk.END, f"网格数量: {len(buy_plan)}\n")
        result_text.insert(tk.END, f"选择的分配方式: {['等金额分配', '等比例分配', '线性加权'][allocation_method]}\n")
        result_text.insert(tk.END, "购买计划如下：\n")

        total_shares = 0
        total_cost = 0
        for price, quantity in buy_plan:
            result_text.insert(tk.END, f"价格: {price:.2f}, 购买股数: {quantity}\n")
            total_shares += quantity
            total_cost += price * quantity

        average_price = total_cost / total_shares if total_shares > 0 else 0

        result_text.insert(tk.END, f"\n总购买股数: {total_shares}\n")
        result_text.insert(tk.END, f"总投资成本: {total_cost:.2f}\n")
        result_text.insert(tk.END, f"平均购买价格: {average_price:.2f}\n")

        max_loss = total_cost - (stop_loss_price * total_shares)
        result_text.insert(tk.END, f"\n最大潜在亏损: {max_loss:.2f} (达到止损价时)\n")
        result_text.insert(tk.END, f"最大亏损比例: {(max_loss / total_funds) * 100:.2f}%\n")

        if warning_message:
            result_text.insert(tk.END, f"\n警告: {warning_message}\n")

        # 保存当前配置
        current_config = {
            "funds": total_funds,
            "initial_price": initial_price,
            "stop_loss_price": stop_loss_price,
            "num_grids": num_grids,
            "allocation_method": allocation_method
        }
        save_config(current_config)

    except InvalidInputError as e:
        logging.error(f"输入错误: {str(e)}")
        messagebox.showerror("输入错误", str(e))
    except Exception as e:
        logging.exception("发生未预期的错误")
        messagebox.showerror("错误", f"发生未预期的错误: {str(e)}")


def save_to_csv():
    try:
        content = result_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("警告", "没有可保存的结果")
            return

        default_filename = f"grid_trading_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_filename
        )
        if not file_path:
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

        logging.info(f"结果已保存到 {file_path}")
        messagebox.showinfo("成功", f"结果已保存到 {file_path}")
    except Exception as e:
        logging.exception("保存文件时发生错误")
        messagebox.showerror("错误", f"保存文件时发生错误: {str(e)}")


# 创建主窗口
root = tk.Tk()
root.title("网格交易购买计划")
root.iconbitmap('app_icon.ico')
root.geometry("400x600")

# 加载配置
config = load_config()

# 创建输入框和标签
tk.Label(root, text="总资金:").grid(row=0, column=0, sticky="e")
funds_entry = tk.Entry(root)
funds_entry.insert(0, str(config['funds']))
funds_entry.grid(row=0, column=1, sticky="ew")

tk.Label(root, text="初始价格:").grid(row=1, column=0, sticky="e")
initial_price_entry = tk.Entry(root)
initial_price_entry.insert(0, str(config['initial_price']))
initial_price_entry.grid(row=1, column=1, sticky="ew")

tk.Label(root, text="止损价格:").grid(row=2, column=0, sticky="e")
stop_loss_price_entry = tk.Entry(root)
stop_loss_price_entry.insert(0, str(config['stop_loss_price']))
stop_loss_price_entry.grid(row=2, column=1, sticky="ew")

tk.Label(root, text="网格数量:").grid(row=3, column=0, sticky="e")
num_grids_entry = tk.Entry(root)
num_grids_entry.insert(0, str(config['num_grids']))
num_grids_entry.grid(row=3, column=1, sticky="ew")

tk.Label(root, text="分配方式:").grid(row=4, column=0, sticky="e")
allocation_method_var = tk.StringVar(value="1")  # 默认选择"等比例分配"
tk.Radiobutton(root, text="等金额分配", variable=allocation_method_var, value="0").grid(row=4, column=1, sticky="w")
tk.Label(root, text="每个网格分配相同金额").grid(row=4, column=2, sticky="w")
tk.Radiobutton(root, text="等比例分配", variable=allocation_method_var, value="1").grid(row=5, column=1, sticky="w")
tk.Label(root, text="低价位分配更多资金").grid(row=5, column=2, sticky="w")
tk.Radiobutton(root, text="线性加权", variable=allocation_method_var, value="2").grid(row=6, column=1, sticky="w")
tk.Label(root, text="价格越低分配越多资金").grid(row=6, column=2, sticky="w")

# 创建按钮
# 创建按钮
button_frame = tk.Frame(root)
button_frame.grid(row=7, column=0, columnspan=3, pady=5)

calculate_button = tk.Button(button_frame, text="不保留资金计算", command=lambda: run_calculation())
calculate_button.grid(row=0, column=0, padx=5)

reserve_10_button = tk.Button(button_frame, text="保留10%计算", command=lambda: calculate_with_reserve(10))
reserve_10_button.grid(row=0, column=1, padx=5)

reserve_20_button = tk.Button(button_frame, text="保留20%计算", command=lambda: calculate_with_reserve(20))
reserve_20_button.grid(row=0, column=2, padx=5)

save_button = tk.Button(root, text="保存为CSV", command=save_to_csv)
save_button.grid(row=8, column=1, pady=5)

# 创建结果显示区域
result_text = scrolledtext.ScrolledText(root, height=20, width=50)
result_text.grid(row=9, column=0, columnspan=3, sticky="nsew")

# 配置网格布局
for i in range(3):
    root.grid_columnconfigure(i, weight=1)
for i in range(10):
    root.grid_rowconfigure(i, weight=1)

# 绑定回车键和空格键到计算函数
root.bind('<Return>', run_calculation)
root.bind('<space>', run_calculation)

root.mainloop()
