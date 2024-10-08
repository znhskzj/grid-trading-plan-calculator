# grid_trading_app.py

import os
import sys
import tkinter as tk
from tkinter import messagebox
from src.gui.main_window import MainWindow
from src.config.config_manager import ConfigManager
from src.utils.logger import setup_logger
from src.utils.error_handler import ConfigurationError, GUIError
from version import VERSION, AUTHOR, DATE
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

__doc__ = f"""
Grid Trading Tool
Version: {VERSION}
Author: {AUTHOR}
Date: {DATE}
"""

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# 设置日志
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
logger = setup_logger(__name__, os.path.join(LOG_DIR, 'grid_trading.log'))

def initialize_config() -> dict:
    """初始化配置"""
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config('General', {})
        if not config:
            raise ConfigurationError("配置文件中缺少 'General' 部分或为空")
        logger.info("配置加载完成")
        return config
    except Exception as e:
        logger.error(f"加载配置时发生错误: {str(e)}", exc_info=True)
        raise

def initialize_gui(config: dict, version: str) -> tuple[tk.Tk, MainWindow]:
    """初始化GUI"""
    try:
        root = tk.Tk()
        main_window = MainWindow(root, version)
        logger.info("GUI 初始化完成")
        return root, main_window
    except Exception as e:
        logger.error(f"初始化 GUI 时发生错误: {str(e)}", exc_info=True)
        raise GUIError(f"GUI 初始化失败: {str(e)}")

def main() -> None:
    """主函数，初始化并运行应用程序。"""
    try:
        logger.info("程序启动")
        
        config = initialize_config()
        root, main_window = initialize_gui(config, VERSION)
        
        root.protocol("WM_DELETE_WINDOW", main_window.on_closing)  # 设置窗口关闭事件
        root.mainloop()
    except ConfigurationError as ce:
        logger.error(f"配置错误: {str(ce)}", exc_info=True)
        messagebox.showerror("配置错误", str(ce))
    except GUIError as ge:
        logger.error(f"GUI 错误: {str(ge)}", exc_info=True)
        messagebox.showerror("GUI 错误", str(ge))
    except Exception as e:
        logger.error(f"程序运行时发生未知错误: {str(e)}", exc_info=True)
        messagebox.showerror("错误", f"程序运行时发生未知错误: {str(e)}")
    finally:
        logger.info("程序结束")

if __name__ == "__main__":
    main()