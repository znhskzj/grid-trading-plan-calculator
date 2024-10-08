# /src/gui/main_window.py

import tkinter as tk
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

logger = setup_logger('main_window', 'logs/main_window.log')

class MainWindow:
    def __init__(self, master: tk.Tk, version: str):
        self.master = master
        self.version = version
        self.config_manager = ConfigManager()
        self.controller = MainController(self)
        
        self.setup_window_properties()
        self.create_widgets()
        self.setup_layout()
    
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
        logger.info("所有窗口组件创建完成")
    
    def create_main_frame(self) -> None:
        """创建主框架"""
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)
        logger.debug("主框架创建完成")
    
    def create_status_bar(self) -> None:
        self.status_bar = StatusBar(self.master)
        logger.debug("状态栏创建完成")
    
    def create_left_frame(self) -> None:
        self.left_frame = LeftFrame(self.main_frame, self.controller)
        logger.debug("左侧框架创建完成")
    
    def create_right_frame(self) -> None:
        self.right_frame = RightFrame(self.main_frame, self.controller)
        logger.debug("右侧框架创建完成")
    
    def create_result_frame(self) -> None:
        self.result_frame = ResultFrame(self.main_frame, self.controller)
        logger.debug("结果框架创建完成")
    
    def setup_layout(self) -> None:
        """设置布局"""
        self.setup_grid_config()
        self.place_frames()
        self.master.update_idletasks()
        self.check_widget_visibility()
        logger.info("布局设置完成")
    
    def setup_grid_config(self) -> None:
        """设置网格配置"""
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
    
    def place_frames(self) -> None:
        """放置各个框架"""
        self.left_frame.grid(row=0, column=0, sticky="ns")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.result_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
    
    def check_widget_visibility(self) -> None:
        """检查组件可见性"""
        if not hasattr(self.result_frame, 'result_text'):
            logger.error("ResultFrame 中未找到 result_text 组件")
            return
        
        self.log_widget_geometries()
        self.check_result_frame_visibility()
        self.check_overlapping_widgets()
    
    def log_widget_geometries(self) -> None:
        """记录各个组件的几何信息"""
        logger.debug(f"主窗口几何信息: {self.master.winfo_geometry()}")
        logger.debug(f"主框架几何信息: {self.main_frame.winfo_geometry()}")
        logger.debug(f"结果框架几何信息: {self.result_frame.winfo_geometry()}")
        logger.debug(f"结果文本几何信息: {self.result_frame.result_text.winfo_geometry()}")
    
    def check_result_frame_visibility(self) -> None:
        """检查结果框架的可见性"""
        if not self.result_frame.result_text.winfo_viewable():
            logger.warning("结果文本组件不可见")
        else:
            logger.debug("结果文本组件可见")
        
        if not self.result_frame.winfo_viewable():
            logger.warning("结果框架不可见")
        else:
            logger.debug("结果框架可见")
    
    def check_overlapping_widgets(self) -> None:
        """检查是否有重叠的组件"""
        overlapping_widgets = [w for w in self.main_frame.winfo_children() 
                               if w.winfo_viewable() and w != self.result_frame]
        if overlapping_widgets:
            logger.warning(f"可能重叠的组件: {overlapping_widgets}")
            for widget in overlapping_widgets:
                logger.debug(f"重叠组件信息: {widget.winfo_class()}, {widget.winfo_geometry()}")
        
        layout_info = self.result_frame.grid_info()
        logger.debug(f"结果框架布局信息: {layout_info}")

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