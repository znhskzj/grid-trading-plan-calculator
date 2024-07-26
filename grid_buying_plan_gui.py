"""
Grid Trading Plan Calculator
Version: 1.0.0
Author: (discord)zzann
Date: July 26, 2024

This program calculates and visualizes grid trading plans.
For more information, please refer to the README.md file.

License: MIT License
"""
import tkinter as tk
from tkinter import messagebox, filedialog
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


def calculate_weights(prices, method):
    if method == 0:  # 等金额分配
        return [1] * len(prices)
    elif method == 1:  # 等比例分配 - 指数增长策略
        return [np.exp(-price) for price in prices]
    elif method == 2:  # 线性加权 - 低价格更高权重
        return list(range(1, len(prices) + 1))
    else:
        raise ValueError("无效的分配方式")


def calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids=10, allocation_method=0):
    validate_inputs(funds, initial_price, stop_loss_price, num_grids, allocation_method)

    logging.info(
        f"计算购买计划: 资金={funds}, 初始价格={initial_price}, 止损价格={stop_loss_price}, 网格数量={num_grids}, 分配方式={allocation_method}")

    max_price = initial_price
    min_price = stop_loss_price

    price_step = (max_price - min_price) / num_grids
    max_shares = int(funds / max_price)
    buy_prices = np.linspace(max_price, min_price, num_grids)
    weights = calculate_weights(buy_prices, allocation_method)

    total_weight = sum(weights)
    buy_quantities = [int(max_shares * (weight / total_weight)) for weight in weights]
    buy_plan = [(round(price, 1), int(round(quantity, -1))) for price, quantity in zip(buy_prices, buy_quantities)]

    logging.info(f"购买计划计算完成: {buy_plan}")
    return buy_plan


def run_calculation():
    try:
        funds = float(funds_entry.get())
        initial_price = float(initial_price_entry.get())
        stop_loss_price = float(stop_loss_price_entry.get())
        num_grids = int(num_grids_entry.get())
        allocation_method = int(allocation_method_var.get())

        buy_plan = calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids, allocation_method)

        result_text.delete(1.0, tk.END)
        result_text.insert(
            tk.END, f"总资金: {funds:.2f}, 初始价格: {initial_price:.1f}, 止损价格: {stop_loss_price:.1f}, 网格数量: {num_grids}\n")
        result_text.insert(tk.END, f"选择的分配方式: {['等金额分配', '等比例分配', '线性加权'][allocation_method]}\n")
        result_text.insert(tk.END, "购买计划如下：\n")
        for price, quantity in buy_plan:
            result_text.insert(tk.END, f"价格: {price:.1f}, 购买股数: {quantity}\n")

        # 保存当前配置
        current_config = {
            "funds": funds,
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

        # 生成默认文件名，使用当前时间戳
        default_filename = f"grid_trading_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_filename
        )
        if not file_path:
            return

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    writer.writerow(line.split(': '))

        logging.info(f"结果已保存到 {file_path}")
        messagebox.showinfo("成功", f"结果已保存到 {file_path}")
    except Exception as e:
        logging.exception("保存文件时发生错误")
        messagebox.showerror("错误", f"保存文件时发生错误: {str(e)}")


# 创建主窗口
root = tk.Tk()
root.title("网格交易购买计划")

# 加载配置
config = load_config()

# 创建输入框和标签
tk.Label(root, text="总资金:").grid(row=0, column=0)
funds_entry = tk.Entry(root)
funds_entry.insert(0, str(config['funds']))
funds_entry.grid(row=0, column=1)

tk.Label(root, text="初始价格:").grid(row=1, column=0)
initial_price_entry = tk.Entry(root)
initial_price_entry.insert(0, str(config['initial_price']))
initial_price_entry.grid(row=1, column=1)

tk.Label(root, text="止损价格:").grid(row=2, column=0)
stop_loss_price_entry = tk.Entry(root)
stop_loss_price_entry.insert(0, str(config['stop_loss_price']))
stop_loss_price_entry.grid(row=2, column=1)

tk.Label(root, text="网格数量:").grid(row=3, column=0)
num_grids_entry = tk.Entry(root)
num_grids_entry.insert(0, str(config['num_grids']))
num_grids_entry.grid(row=3, column=1)

tk.Label(root, text="分配方式:").grid(row=4, column=0)
allocation_method_var = tk.StringVar(value=str(config['allocation_method']))
tk.Radiobutton(root, text="等金额分配", variable=allocation_method_var, value="0").grid(row=4, column=1)
tk.Radiobutton(root, text="等比例分配", variable=allocation_method_var, value="1").grid(row=5, column=1)
tk.Radiobutton(root, text="线性加权", variable=allocation_method_var, value="2").grid(row=6, column=1)

# 创建计算按钮
calculate_button = tk.Button(root, text="计算", command=run_calculation)
calculate_button.grid(row=7, column=0, columnspan=2)

# 创建保存按钮
save_button = tk.Button(root, text="保存为CSV", command=save_to_csv)
save_button.grid(row=8, column=0, columnspan=2)

# 创建结果显示区域
result_text = tk.Text(root, height=20, width=50)
result_text.grid(row=9, column=0, columnspan=2)

root.mainloop()
