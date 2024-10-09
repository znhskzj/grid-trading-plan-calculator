# src/gui/components/left_frame.py

import tkinter as tk
import logging
from typing import Dict, Any
from tkinter import ttk
from src.utils.error_handler import GUIError

logger = logging.getLogger(__name__)

class LeftFrame(tk.Frame):
    def __init__(self, master: Any, controller: Any):
        super().__init__(master)
        self.controller = controller
        self.create_widgets()
    
    def create_widgets(self) -> None:
        """创建并布局所有GUI组件"""
        try:
            self.create_common_stocks_button()
            self.create_common_stocks_frame()
        except Exception as e:
            self.handle_gui_error("创建GUI组件时发生错误", e)
    
    def create_common_stocks_frame(self) -> None:
        self.common_stocks_frame = ttk.Frame(self)
        self.common_stocks_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.common_stocks_frame.grid_remove()  # 初始时隐藏
    
    def create_common_stocks_button(self) -> None:
        self.common_stocks_button = ttk.Button(self, text="常用标的", command=self.toggle_common_stocks)
        self.common_stocks_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    
    def toggle_common_stocks(self) -> None:
        """切换常用标的的显示状态"""
        if self.common_stocks_frame.winfo_viewable():
            self.common_stocks_frame.grid_remove()
            self.common_stocks_button.config(text="常用标的")
        else:
            self.common_stocks_frame.grid()
            self.common_stocks_button.config(text="隐藏标的")
        logger.debug("切换了常用标的的可见性")

    def update_common_stocks(self, stocks: Dict[str, str]) -> None:
        """更新常用股票列表"""
        try:
            for widget in self.common_stocks_frame.winfo_children():
                widget.destroy()
            
            for i, (key, symbol) in enumerate(stocks.items()):
                if symbol and symbol.strip():
                    btn = ttk.Button(self.common_stocks_frame, text=symbol.strip(), width=10,
                                     command=lambda s=symbol.strip(): self.controller.set_stock_price(s))
                    btn.grid(row=i, column=0, pady=2)
            
            # 确保常用标的按钮显示正确的文本
            if self.common_stocks_frame.winfo_children():
                self.common_stocks_button.config(text="隐藏标的")
            else:
                self.common_stocks_button.config(text="显示标的")
            logger.info(f"更新了常用标的: {stocks}")
        except Exception as e:
            self.handle_gui_error("更新常用标的时发生错误", e)

    def handle_gui_error(self, message: str, exception: Exception) -> None:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
        raise GUIError(f"{message}: {str(exception)}")

    def get_input_values(self) -> Dict[str, Any]:
        return {
            "funds": float(self.funds_var.get()),
            "initial_price": float(self.initial_price_var.get()),
            "stop_loss_price": float(self.stop_loss_price_var.get()),
            "num_grids": int(self.num_grids_var.get())
        }

    def reset_inputs(self) -> None:
        for field in ['funds', 'initial_price', 'stop_loss_price', 'num_grids']:
            getattr(self, f"{field}_var").set('')
        self.controller.reset_calculation()

    def update_fields(self, values: Dict[str, Any]) -> None:
        for field, value in values.items():
            if hasattr(self, f"{field}_var"):
                getattr(self, f"{field}_var").set(str(value))