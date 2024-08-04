# grid_trading_app.py
from version import VERSION, AUTHOR, DATE
"""
Grid Trading Tool
Version: {VERSION}
Author: {AUTHOR}
Date: {DATE}
"""

import os
import tkinter as tk
from tkinter import messagebox
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

logger = logging.getLogger(__name__)


def main():
    try:
        logger.info("程序启动")

        # 首次运行时转换 JSON 配置到 INI
        convert_json_to_ini()
        logger.info("配置转换完成")

        config = load_config()
        logger.info("配置加载完成")

        # 确保 'General' 键存在于配置中
        if 'General' not in config:
            raise KeyError("配置文件中缺少 'General' 部分")

        root = tk.Tk()
        app = App(root, config, VERSION)  # 传递整个 config 字典
        logger.info("GUI 初始化完成")

        root.mainloop()
    except Exception as e:
        logger.error(f"程序运行时发生错误: {str(e)}", exc_info=True)
        messagebox.showerror("错误", f"程序运行时发生错误: {str(e)}")
    finally:
        logger.info("程序结束")


if __name__ == "__main__":
    main()
