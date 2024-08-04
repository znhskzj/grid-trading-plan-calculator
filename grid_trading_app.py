"""
Grid Trading Tool
Version: 1.4.1
Author: Rong Zhu
Date: August 4, 2024
"""

import os
import tkinter as tk
import logging
from src.gui import App
from src.config import load_config, convert_json_to_ini

# 确保日志目录存在
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# 设置日志格式以包含模块名
logging.basicConfig(
    filename=os.path.join(log_dir, 'grid_trading.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    encoding='utf-8'
)


def main():
    # 首次运行时转换 JSON 配置到 INI
    convert_json_to_ini()

    config = load_config()
    # 将字符串值转换为适当的类型
    funds = float(config['funds'])
    initial_price = float(config['initial_price'])
    stop_loss_price = float(config['stop_loss_price'])
    num_grids = int(config['num_grids'])
    allocation_method = int(config['allocation_method'])

    root = tk.Tk()
    root.title("Grid Trading Tool")
    app = App(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
