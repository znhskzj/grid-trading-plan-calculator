# grid_trading_app.py

from version import VERSION, AUTHOR, DATE

f"""
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
from src.config import load_system_config

# 确保日志目录存在
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

# 设置日志格式以包含模块名
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'grid_trading.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

logger = logging.getLogger(__name__)


def main():
    """主函数，初始化并运行应用程序。"""
    try:
        logger.info("程序启动")
        
        config = load_system_config()
        logger.info("配置加载完成")
        
        # 确保 'General' 键存在于配置中
        if 'General' not in config:
            raise KeyError("配置文件中缺少 'General' 部分")
        
        root = tk.Tk()
        app = App(root, config, VERSION)
        logger.info("GUI 初始化完成")
        
        root.protocol("WM_DELETE_WINDOW", app.on_closing)  # 设置窗口关闭事件
        root.mainloop()
    except Exception as e:
        logger.error(f"程序运行时发生错误: {str(e)}", exc_info=True)
        messagebox.showerror("错误", f"程序运行时发生错误: {str(e)}")
    finally:
        logger.info("程序结束")

if __name__ == "__main__":
    main()