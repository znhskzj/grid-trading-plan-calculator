import tkinter as tk
from tkinter import ttk
import logging
from .components.left_frame import LeftFrame
from .components.right_frame import RightFrame
from .components.result_frame import ResultFrame
from .components.status_bar import StatusBar
from .controllers.main_controller import MainController
from src.config.config_manager import ConfigManager

class MainWindow:
    def __init__(self, master, version):
        self.master = master
        self.version = version
        self.config_manager = ConfigManager()
        self.controller = MainController(self)
        
        self.setup_window_properties()
        self.create_widgets()
        self.setup_layout()
    
    def setup_window_properties(self):
        """设置窗口属性"""
        window_config = self.config_manager.get_config('GUI', {})
        width = int(window_config.get('window_width', 750))
        height = int(window_config.get('window_height', 750))
        self.master.geometry(f"{width}x{height}")
        self.master.minsize(width, height)
        self.master.maxsize(width, height)
        self.master.resizable(False, False)
    
    def create_widgets(self):
        self.create_main_frame()
        self.create_status_bar()
        self.create_left_frame()
        self.create_right_frame()
        self.create_result_frame()
    
    def create_main_frame(self):
        """创建主框架"""
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)
    
    def create_status_bar(self):
        self.status_bar = StatusBar(self.master)
    
    def create_left_frame(self):
        self.left_frame = LeftFrame(self.main_frame, self.controller)
    
    def create_right_frame(self):
        self.right_frame = RightFrame(self.main_frame, self.controller)
    
    def create_result_frame(self):
        self.result_frame = ResultFrame(self.main_frame, self.controller)
    
    def setup_layout(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.left_frame.grid(row=0, column=0, sticky="ns")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.result_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        
        self.master.update_idletasks()
        self.check_widget_visibility()
    
    def check_widget_visibility(self):
        if not hasattr(self.result_frame, 'result_text'):
            logging.error("result_text widget not found in ResultFrame")
            return
        
        logging.debug(f"Main window geometry: {self.master.winfo_geometry()}")
        logging.debug(f"Main frame geometry: {self.main_frame.winfo_geometry()}")
        logging.debug(f"Result frame geometry: {self.result_frame.winfo_geometry()}")
        logging.debug(f"Result text geometry: {self.result_frame.result_text.winfo_geometry()}")
        
        if not self.result_frame.result_text.winfo_viewable():
            logging.warning("Result text widget is not visible")
        else:
            logging.debug("Result text widget is visible")
        
        if not self.result_frame.winfo_viewable():
            logging.warning("Result frame is not visible")
        else:
            logging.debug("Result frame is visible")
        
        # 检查是否有其他组件覆盖了结果文本框
        overlapping_widgets = [w for w in self.main_frame.winfo_children() if w.winfo_viewable() and w != self.result_frame]
        if overlapping_widgets:
            logging.warning(f"Potentially overlapping widgets: {overlapping_widgets}")
            for widget in overlapping_widgets:
                logging.debug(f"Overlapping widget info: {widget.winfo_class()}, {widget.winfo_geometry()}")
        
        # 检查结果框架的布局信息
        layout_info = self.result_frame.grid_info()
        logging.debug(f"Result frame layout info: {layout_info}")