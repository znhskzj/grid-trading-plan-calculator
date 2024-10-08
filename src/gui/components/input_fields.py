# src/gui/components/input_fields.py

import tkinter as tk
from tkinter import ttk
from typing import Any, List, Tuple
from src.utils.logger import setup_logger
from src.utils.gui_helpers import validate_float_input, validate_int_input
from src.utils.error_handler import GUIError

logger = setup_logger(__name__)

class InputFields(tk.Frame):
    def __init__(self, master: tk.Widget, controller: Any):
        super().__init__(master)
        self.controller = controller
        self.initialize_variables()
        self.create_widgets()

    def initialize_variables(self) -> None:
        self.funds_var = tk.StringVar()
        self.initial_price_var = tk.StringVar()
        self.stop_loss_price_var = tk.StringVar()
        self.num_grids_var = tk.StringVar()
        self.instruction_var = tk.StringVar()

    def create_widgets(self) -> None:
        try:
            self.create_input_fields()
        except Exception as e:
            self.handle_gui_error("创建输入字段时发生错误", e)

    def create_input_fields(self) -> None:
        labels: List[str] = ["可用资金:", "初始价格:", "止损价格:", "网格数量:", "交易指令:"]
        vars: List[tk.StringVar] = [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var, self.instruction_var]

        for i, (label, var) in enumerate(zip(labels, vars)):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(self, textvariable=var, width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=(5, 0), pady=2)
            
            if label in ["可用资金:", "初始价格:", "止损价格:"]:
                entry.config(validate="key", validatecommand=(self.register(validate_float_input), '%d', '%P'))
            elif label == "网格数量:":
                entry.config(validate="key", validatecommand=(self.register(validate_int_input), '%d', '%P'))
            
            if label == "交易指令:":
                self.setup_instruction_entry(entry)

    def setup_instruction_entry(self, entry: ttk.Entry) -> None:
        entry.config(width=50)
        entry.grid(columnspan=2)
        
        entry.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
        entry.config(foreground="gray")
        
        entry.bind('<FocusIn>', self.on_entry_click)
        entry.bind('<FocusOut>', self.on_focusout)

    def on_entry_click(self, event: tk.Event) -> None:
        if event.widget.get() == "例：SOXL现价到37.5之间分批买，压力39+，止损36.8":
            event.widget.delete(0, "end")
            event.widget.config(foreground="black")

    def on_focusout(self, event: tk.Event) -> None:
        if event.widget.get() == "":
            event.widget.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
            event.widget.config(foreground="gray")

    def get_input_values(self) -> dict[str, Any]:
        return {
            "funds": float(self.funds_var.get()),
            "initial_price": float(self.initial_price_var.get()),
            "stop_loss_price": float(self.stop_loss_price_var.get()),
            "num_grids": int(self.num_grids_var.get()),
            "instruction": self.instruction_var.get()
        }

    def set_input_values(self, values: dict[str, Any]) -> None:
        for key, value in values.items():
            if hasattr(self, f"{key}_var"):
                getattr(self, f"{key}_var").set(str(value))

    def clear_inputs(self) -> None:
        for var in [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var]:
            var.set("")
        self.instruction_var.set("例：SOXL现价到37.5之间分批买，压力39+，止损36.8")

    def handle_gui_error(self, message: str, exception: Exception) -> None:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
        raise GUIError(f"{message}: {str(exception)}")