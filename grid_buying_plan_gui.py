"""
Grid Trading Plan Calculator
Version: 1.3.3
Author: (discord)zzann
Date: August 1, 2024

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
import sys
import threading
import time
from datetime import datetime

# 设置日志
logging.basicConfig(filename='grid_trading.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')

# Get the logger
logger = logging.getLogger(__name__)


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
    if not os.path.exists(config_file):
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=4)
        logging.info(f"创建了新的配置文件 {config_file}")
        return default_config

    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"配置文件 {config_file} 格式错误，使用默认配置")
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
    if num_grids > 100:
        raise InvalidInputError("网格数量不能超过100")


def calculate_weights(prices, method, max_shares):
    print(f"开始计算权重: 方法={method}, 最大股数={max_shares}")
    if method == 0:  # 等金额分配
        weights = [1] * len(prices)
    elif method == 1:  # 等比例分配 - 指数增长策略
        max_price = max(prices)
        weights = [np.exp((max_price - price) / max_price) for price in prices]
    elif method == 2:  # 线性加权 - 低价格更高权重
        weights = list(range(1, len(prices) + 1))
    else:
        raise ValueError("无效的分配方式")

    print(f"计算得到的权重: {weights}")

    # 计算初始股数分配
    total_weight = sum(weights)
    initial_shares = [max(1, int(max_shares * (weight / total_weight))) for weight in weights]

    print(f"计算得到的初始股数: {initial_shares}")
    return initial_shares


def calculate_with_reserve(reserve_percentage):
    try:
        funds = float(funds_var.get() or config['funds'])
        reserved_funds = funds * (reserve_percentage / 100)
        available_funds = funds - reserved_funds
        run_calculation(available_funds=available_funds, reserved_funds=reserved_funds)
    except ValueError:
        messagebox.showerror("输入错误", "总资金必须是有效的数字")


def calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids=10, allocation_method=0):
    print("开始执行 calculate_buy_plan 函数")
    validate_inputs(funds, initial_price, stop_loss_price, num_grids, allocation_method)

    print(f"计算购买计划: 资金={funds}, 初始价格={initial_price}, 止损价格={stop_loss_price}, 网格数量={num_grids}, 分配方式={allocation_method}")

    max_price = initial_price
    min_price = stop_loss_price

    max_shares = int(funds / min_price)  # 使用最低价格计算最大可购买股数
    print(f"最大可购买股数: {max_shares}")

    if max_shares < num_grids:
        num_grids = max_shares
        print(f"资金不足以分配到所有网格，已减少网格数量至 {num_grids}")

    buy_prices = np.linspace(max_price, min_price, num_grids)
    print(f"生成的价格网格: {buy_prices}")

    if allocation_method == 0:  # 等金额分配
        target_amount_per_grid = funds / num_grids
        buy_quantities = [max(1, int(target_amount_per_grid / price)) for price in buy_prices]
    else:
        buy_quantities = calculate_weights(buy_prices, allocation_method, max_shares)

    print(f"初始购买数量: {buy_quantities}")

    # 调整购买数量，确保总金额不超过可用资金
    total_cost = sum(price * quantity for price, quantity in zip(buy_prices, buy_quantities))
    if total_cost > funds:
        scale_factor = funds / total_cost
        buy_quantities = [max(1, int(quantity * scale_factor)) for quantity in buy_quantities]
        print(f"调整后的购买数量: {buy_quantities}")

    # 分配剩余资金
    remaining_funds = funds - sum(price * quantity for price, quantity in zip(buy_prices, buy_quantities))
    print(f"剩余资金: {remaining_funds}")

    start_time = time.time()
    loop_count = 0
    while remaining_funds > min(buy_prices) and loop_count < 1000:  # 添加最大循环次数限制
        for i in range(num_grids):
            if remaining_funds >= buy_prices[i]:
                buy_quantities[i] += 1
                remaining_funds -= buy_prices[i]
                break  # 每次只增加一个股数，然后重新开始
        loop_count += 1
        if time.time() - start_time > 5:  # 如果执行时间超过5秒，退出循环
            print("分配剩余资金时间过长，提前退出循环")
            break

    print(f"剩余资金分配后的购买数量: {buy_quantities}")
    print(f"最终剩余资金: {remaining_funds:.2f}")

    buy_plan = [(round(price, 2), int(quantity)) for price, quantity in zip(buy_prices, buy_quantities)]
    print(f"最终购买计划: {buy_plan}")

    # 检查是否有过多的1股购买
    single_share_count = sum(1 for _, quantity in buy_plan if quantity == 1)
    warning_message = ""
    if single_share_count > num_grids // 2:  # 如果超过一半的网格只买1股
        warning_message = "\n警告：当前参数可能不够合理，多个价位只购买1股。建议减少网格数量或增加总资金。"

    print("calculate_buy_plan 函数执行完毕")
    return buy_plan, warning_message


calculation_in_progress = False
calculation_timer = None
calculation_complete = threading.Event()


def run_calculation(event=None, available_funds=None, reserved_funds=0):
    logging.info(f"用户启动计算 - 分配方式: {allocation_method_var.get()}, 保留资金: {reserved_funds}")
    global calculation_in_progress, calculation_timer, calculation_complete, calculation_start_time
    if calculation_in_progress:
        print("计算已在进行中，忽略新的计算请求")
        return
    calculation_in_progress = True
    calculation_complete.clear()
    calculation_start_time = time.time()
    print(f"开始计算 - 分配方式: {allocation_method_var.get()}")

    def calculate():
        global calculation_timer
        nonlocal available_funds
        try:
            print("计算线程开始执行")
            total_funds = float(funds_var.get() or config['funds'])
            if available_funds is None:
                available_funds = total_funds
            initial_price = float(initial_price_var.get() or config['initial_price'])
            stop_loss_price = float(stop_loss_price_var.get() or config['stop_loss_price'])
            num_grids = int(num_grids_var.get() or config['num_grids'])
            allocation_method = int(allocation_method_var.get())

            print(f"计算参数: 总资金={total_funds}, 可用资金={available_funds}, 初始价格={initial_price}, "
                  f"止损价格={stop_loss_price}, 网格数量={num_grids}, 分配方式={allocation_method}")

            start_time = time.time()
            buy_plan, warning_message = calculate_buy_plan(
                available_funds, initial_price, stop_loss_price, num_grids, allocation_method)
            end_time = time.time()

            if end_time - start_time > 30:  # 如果计算时间超过30秒
                raise TimeoutError("计算时间过长，可能存在无限循环")

            print(f"计算完成，耗时: {end_time - start_time:.2f} 秒")
            print(f"计算结果: buy_plan={buy_plan}, warning_message={warning_message}")
            calculation_complete.set()  # 在这里设置完成标志
            root.after(0, lambda: display_results(total_funds, available_funds, reserved_funds,
                                                  initial_price, stop_loss_price, num_grids, allocation_method, buy_plan, warning_message))
        except Exception as e:
            print(f"计算时发生错误: {str(e)}")
            root.after(0, lambda: messagebox.showerror("错误", f"计算时发生错误: {str(e)}"))
        finally:
            if calculation_timer:
                calculation_timer.cancel()
            print("计算线程结束")
            root.after(0, end_calculation)

    def end_calculation():
        global calculation_in_progress, calculation_timer, calculation_complete
        calculation_in_progress = False
        calculation_complete.clear()
        if calculation_timer:
            calculation_timer.cancel()
        enable_buttons()
        print("计算状态重置，按钮已启用")

    disable_buttons()
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "计算中，请稍候...\n")

    calculation_timer = threading.Timer(30.0, handle_timeout)
    calculation_timer.start()

    calculation_thread = threading.Thread(target=calculate)
    calculation_thread.start()

    root.after(100, check_calculation_status)


def check_calculation_status():
    global calculation_in_progress
    if calculation_complete.is_set():
        print("计算已完成")
        calculation_in_progress = False
        enable_buttons()
    elif calculation_in_progress:
        print("计算仍在进行中...")
        if time.time() - calculation_start_time > 60:  # 如果超过60秒
            print("计算超时，强制结束")
            calculation_in_progress = False
            root.after(0, lambda: messagebox.showerror("错误", "计算超时，请检查输入参数或重试"))
            enable_buttons()
        else:
            root.after(100, check_calculation_status)
    else:
        print("计算已停止")


# 在 run_calculation 函数开始处添加：
global calculation_start_time
calculation_start_time = time.time()


def handle_timeout():
    global calculation_in_progress
    print("计算超时，准备在主线程中处理")
    if calculation_in_progress and not calculation_complete.is_set():
        root.after(0, handle_timeout_gui)
    else:
        print("计算已完成，不需要处理超时")


def handle_timeout_gui():
    global calculation_in_progress
    if calculation_in_progress and not calculation_complete.is_set():
        print("在GUI中处理计算超时")
        calculation_in_progress = False
        enable_buttons()
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "计算超时，请检查输入参数或重试。\n")
    else:
        print("计算已完成，不需要处理超时")


def display_results(
        total_funds, available_funds, reserved_funds, initial_price, stop_loss_price, num_grids, allocation_method,
        buy_plan, warning_message):
    def update_gui():
        global calculation_in_progress
        if not calculation_in_progress:
            print("计算已经结束，不更新GUI")
            return
        print("开始更新GUI")
        try:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"总资金: {total_funds:.2f}\n")
            if reserved_funds > 0:
                result_text.insert(tk.END, f"保留资金: {reserved_funds:.2f}\n")
                result_text.insert(tk.END, f"可用资金: {available_funds:.2f}\n")
            result_text.insert(tk.END, f"初始价格: {initial_price:.2f}\n")
            result_text.insert(tk.END, f"止损价格: {stop_loss_price:.2f}\n")
            result_text.insert(tk.END, f"网格数量: {len(buy_plan)}\n")

            # 显示分配方式的详细信息
            if allocation_method == 0:
                actual_amounts = [price * quantity for price, quantity in buy_plan]
                avg_amount = sum(actual_amounts) / len(actual_amounts)
                result_text.insert(tk.END, f"选择的分配方式: 等金额分配 (每个网格平均约 {avg_amount:.0f}元)\n")
                result_text.insert(tk.END, "分配特点: 每个价格点分配相同金额\n")
            elif allocation_method == 1:
                result_text.insert(tk.END, "选择的分配方式: 等比例分配（指数分配）\n")
                result_text.insert(tk.END, "分配特点: 价格越低，分配资金呈指数增长\n")
                result_text.insert(tk.END, "效果: 在最低价位分配最多资金，资金分配差异大\n")
            else:
                result_text.insert(tk.END, "选择的分配方式: 线性加权分配\n")
                result_text.insert(tk.END, "分配特点: 价格越低，分配资金线性增加\n")
                result_text.insert(tk.END, f"效果: 低价位分配更多资金，但增长相对平缓（最低价格网格权重为最高价格网格的 {num_grids} 倍）\n")

            result_text.insert(tk.END, "购买计划如下：\n")

            total_shares = 0
            total_cost = 0
            for price, quantity in buy_plan:
                buy_amount = price * quantity
                result_text.insert(tk.END, f"价格: {price:.2f}, 购买股数: {quantity}, 购买金额: 约{buy_amount:.0f}元\n")
                total_shares += quantity
                total_cost += buy_amount

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
            print("GUI更新完成")
        except Exception as e:
            print(f"显示结果时发生错误: {str(e)}")
            logging.exception("显示结果时发生错误")
            messagebox.showerror("错误", f"显示结果时发生错误: {str(e)}")
        finally:
            calculation_in_progress = False
            enable_buttons()
            print("按钮已启用")

    root.after(0, update_gui)


def disable_buttons():
    calculate_button.config(state=tk.DISABLED)
    reserve_10_button.config(state=tk.DISABLED)
    reserve_20_button.config(state=tk.DISABLED)
    save_button.config(state=tk.DISABLED)
    reset_button.config(state=tk.DISABLED)


def enable_buttons():
    calculate_button.config(state=tk.NORMAL)
    reserve_10_button.config(state=tk.NORMAL)
    reserve_20_button.config(state=tk.NORMAL)
    save_button.config(state=tk.NORMAL)
    reset_button.config(state=tk.NORMAL)


def save_to_csv():
    logging.info("用户尝试保存结果为 CSV")
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


def reset_to_default():
    logging.info("用户重置为默认值")
    funds_var.set(str(config['funds']))
    initial_price_var.set(str(config['initial_price']))
    stop_loss_price_var.set(str(config['stop_loss_price']))
    num_grids_var.set(str(config['num_grids']))
    allocation_method_var.set(str(config['allocation_method']))


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


# 创建主窗口
root = tk.Tk()
root.title("网格交易购买计划")

# 尝试设置图标
try:
    icon_path = 'app_icon.ico'
    if hasattr(sys, '_MEIPASS'):  # 检查是否在 PyInstaller 环境中
        icon_path = os.path.join(sys._MEIPASS, 'app_icon.ico')
    root.iconbitmap(icon_path)
except Exception as e:
    print(f"Warning: Could not load icon: {e}")

root.geometry("400x600")

# 加载配置
config = load_config()

# 创建和配置StringVar
funds_var = tk.StringVar(value=str(config['funds']))
initial_price_var = tk.StringVar(value=str(config['initial_price']))
stop_loss_price_var = tk.StringVar(value=str(config['stop_loss_price']))
num_grids_var = tk.StringVar(value=str(config['num_grids']))
allocation_method_var = tk.StringVar(value=str(config['allocation_method']))

# 创建输入框和标签
tk.Label(root, text="总资金:").grid(row=0, column=0, sticky="e")
funds_entry = tk.Entry(root, textvariable=funds_var, validate="key",
                       validatecommand=(root.register(validate_float_input), '%d', '%P'))
funds_entry.grid(row=0, column=1, sticky="ew")

tk.Label(root, text="初始价格:").grid(row=1, column=0, sticky="e")
initial_price_entry = tk.Entry(root, textvariable=initial_price_var, validate="key",
                               validatecommand=(root.register(validate_float_input), '%d', '%P'))
initial_price_entry.grid(row=1, column=1, sticky="ew")

tk.Label(root, text="止损价格:").grid(row=2, column=0, sticky="e")
stop_loss_price_entry = tk.Entry(root, textvariable=stop_loss_price_var, validate="key",
                                 validatecommand=(root.register(validate_float_input), '%d', '%P'))
stop_loss_price_entry.grid(row=2, column=1, sticky="ew")

tk.Label(root, text="网格数量:").grid(row=3, column=0, sticky="e")
num_grids_entry = tk.Entry(root, textvariable=num_grids_var, validate="key",
                           validatecommand=(root.register(validate_int_input), '%d', '%P'))
num_grids_entry.grid(row=3, column=1, sticky="ew")

tk.Label(root, text="分配方式:").grid(row=4, column=0, sticky="e")
tk.Radiobutton(root, text="等金额分配", variable=allocation_method_var, value="0").grid(row=4, column=1, sticky="w")
tk.Label(root, text="均匀分配资金").grid(row=4, column=2, sticky="w")
tk.Radiobutton(root, text="等比例分配", variable=allocation_method_var, value="1").grid(row=5, column=1, sticky="w")
tk.Label(root, text="指数增长分配").grid(row=5, column=2, sticky="w")
tk.Radiobutton(root, text="线性加权", variable=allocation_method_var, value="2").grid(row=6, column=1, sticky="w")
tk.Label(root, text="线性增长分配").grid(row=6, column=2, sticky="w")

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

reset_button = tk.Button(root, text="重置为默认值", command=reset_to_default)
reset_button.grid(row=8, column=2, pady=5)

# 创建结果显示区域
result_text = scrolledtext.ScrolledText(root, height=20, width=50)
result_text.grid(row=9, column=0, columnspan=3, sticky="nsew")

# 配置网格布局
for i in range(3):
    root.grid_columnconfigure(i, weight=1)
for i in range(10):
    root.grid_rowconfigure(i, weight=1)


def on_closing():
    print("窗口正在关闭...")
    # root.quit()
    root.destroy()


# 绑定回车键和空格键到计算函数
root.bind('<Return>', run_calculation)
root.bind('<space>', run_calculation)
root.protocol("WM_DELETE_WINDOW", on_closing)
print("程序启动...")
# sys.stdout.flush()
root.mainloop()
print("程序结束")  # 这行通常不会执行，除非窗口被关闭
try:
    root.destroy()
except:
    pass
sys.exit(0)
