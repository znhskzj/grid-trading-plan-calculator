# /src/gui/main_window.py

import tkinter as tk
import logging
from tkinter import ttk
from tkinter import messagebox
from typing import Dict, Any

from src.utils.logger import setup_logger
from src.utils.error_handler import ConfigurationError as ConfigError, GUIError
from .components.left_frame import LeftFrame
from .components.right_frame import RightFrame
from .components.result_frame import ResultFrame
from .components.status_bar import StatusBar
from .controllers.main_controller import MainController
from src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self, master: tk.Tk, version: str):
        self.master = master
        self.version = version
        self.master.title(f"网格交易计算器 v{version}")
        self.config_manager = ConfigManager()
        self.controller = MainController(self)
        
        self.setup_window_properties()
        self.create_widgets()
        self.setup_layout()
        
        # 更新常用标的
        common_stocks = self.config_manager.get_config('CommonStocks', {})
        self.left_frame.update_common_stocks(common_stocks)
        
        # 确保所有组件都已更新
        self.master.update_idletasks()
        
        # 添加一个小延迟来检查可见性
        self.master.after(100, self.check_widget_visibility)
        default_config = self.config_manager.get_config('RecentCalculations', {})
        self.right_frame.set_initial_values(
            funds=default_config.get('funds', '50000'),
            initial_price=default_config.get('initial_price', '100'),
            stop_loss_price=default_config.get('stop_loss_price', '90'),
            num_grids=default_config.get('num_grids', '10'),
            allocation_method=default_config.get('allocation_method', '0')
        )
    
    def setup_window_properties(self) -> None:
        """设置窗口属性"""
        try:
            window_config = self.config_manager.get_config('GUI', {})
            width = int(window_config.get('window_width', 750))
            height = int(window_config.get('window_height', 750))
            self.set_window_size(width, height)
        except (ValueError, ConfigError) as e:
            logger.error(f"设置窗口属性时发生错误: {str(e)}")
            # 使用默认值
            self.set_window_size(750, 750)
    
    def set_window_size(self, width: int, height: int) -> None:
        """设置窗口大小和限制"""
        self.master.geometry(f"{width}x{height}")
        self.master.minsize(width, height)
        self.master.maxsize(width, height)
        self.master.resizable(False, False)
        logger.info(f"窗口大小设置为 {width}x{height}")
    
    def create_widgets(self) -> None:
        """创建所有窗口组件"""
        self.create_main_frame()
        self.create_status_bar()
        self.create_left_frame()
        self.create_right_frame()
        self.create_result_frame()
        self.create_status_bar()
        logger.info("所有窗口组件创建完成")
    
    def create_main_frame(self) -> None:
        """创建主框架"""
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        logger.debug("主框架创建完成")
    
    def create_left_frame(self) -> None:
        self.left_frame = LeftFrame(self.main_frame, self.controller)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        logger.debug("左侧框架创建完成")
    
    def create_right_frame(self) -> None:
        self.right_frame = RightFrame(self.main_frame, self.controller)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        logger.debug("右侧框架创建完成")
    
    def create_result_frame(self) -> None:
        self.result_frame = ResultFrame(self.main_frame, self.controller)
        self.result_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        logger.debug("结果框架创建完成")
    
    def create_status_bar(self) -> None:
        self.status_bar = StatusBar(self.master)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        logger.debug("状态栏创建完成")
    
    def setup_layout(self) -> None:
        """设置布局"""
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.main_frame.grid_rowconfigure(0, weight=3)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.master.grid_rowconfigure(2, weight=1) 
        self.master.grid_columnconfigure(0, weight=1)
        
        self.result_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5) 
        self.master.after(100, self.check_widget_visibility)
        
        logger.info("布局设置完成")
    
    def setup_grid_config(self) -> None:
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.main_frame.grid(sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=3)  # 给右侧更多空间
        self.main_frame.grid_rowconfigure(0, weight=3)
        self.main_frame.grid_rowconfigure(1, weight=1)
    
    def place_frames(self) -> None:
        """放置各个框架"""
        self.left_frame.grid(row=0, column=0, sticky="nw", padx=(10, 5), pady=10)
        self.right_frame.grid(row=0, column=1, sticky="ne", padx=(5, 10), pady=10)
        self.result_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        
    def check_widget_visibility(self) -> None:
        """检查组件可见性"""
        if not hasattr(self.result_frame, 'result_text'):
            logger.warning("ResultFrame 中未找到 result_text 组件")
            return
        
        logger.debug(f"主窗口几何信息: {self.master.winfo_geometry()}")
        logger.debug(f"主框架几何信息: {self.main_frame.winfo_geometry()}")
        logger.debug(f"左侧框架几何信息: {self.left_frame.winfo_geometry()}")
        logger.debug(f"右侧框架几何信息: {self.right_frame.winfo_geometry()}")
        logger.debug(f"结果框架几何信息: {self.result_frame.winfo_geometry()}")
        
        if not self.result_frame.winfo_viewable():
            logger.warning("结果框架不可见")
        else:
            logger.debug("结果框架可见")
        
        if not self.result_frame.result_text.winfo_viewable():
            logger.warning("结果文本组件不可见")
        else:
            logger.debug("结果文本组件可见")
        
        self.check_overlapping_widgets()
    
    def check_overlapping_widgets(self) -> None:
        """检查是否有重叠的组件"""
        all_widgets = self.main_frame.winfo_children()
        for i, widget1 in enumerate(all_widgets):
            for widget2 in all_widgets[i+1:]:
                if widget1.winfo_viewable() and widget2.winfo_viewable():
                    x1, y1, w1, h1 = widget1.winfo_x(), widget1.winfo_y(), widget1.winfo_width(), widget1.winfo_height()
                    x2, y2, w2, h2 = widget2.winfo_x(), widget2.winfo_y(), widget2.winfo_width(), widget2.winfo_height()
                    if (x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2):
                        logger.warning(f"可能重叠的组件: {widget1} 和 {widget2}")

    def update_status_bar(self, message: str) -> None:
        if hasattr(self, 'status_bar'):
            self.status_bar.config(text=message)
        else:
            print(f"Status: {message}")  # 如果状态栏还未创建,则打印到控制台

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message)

    def on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            # 执行任何必要的清理操作
            if hasattr(self, 'controller'):
                # 保存配置
                self.controller.save_config()
                # 关闭任何打开的连接
                if hasattr(self.controller, 'api_manager'):
                    self.controller.api_manager.close_all_connections()
            
            # 销毁窗口
            self.master.destroy()