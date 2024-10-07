# src/gui/components/input_fields.py
import tkinter as tk
from tkinter import ttk

class InputFields(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        self.create_input_fields()

    def create_input_fields(self) -> None:
        """创建输入字段"""
        labels = ["可用资金:", "初始价格:", "止损价格:", "网格数量:", "交易指令:"]
        vars = [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var, self.instruction_var]

        for i, (label, var) in enumerate(zip(labels, vars)):
            ttk.Label(self.right_frame, text=label).grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(self.right_frame, textvariable=var, width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=(5, 0), pady=2)
            
            # 为交易指令输入框增加特性
            if label == "交易指令:":
                entry.config(width=50)  # 增加宽度
                entry.grid(columnspan=2)  # 跨两列
                
                # 添加提示信息
                entry.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
                entry.config(foreground="gray")
                
                def on_entry_click(event):
                    if entry.get() == "例：SOXL现价到37.5之间分批买，压力39+，止损36.8":
                        entry.delete(0, "end")
                        entry.config(foreground="black")
                
                def on_focusout(event):
                    if entry.get() == "":
                        entry.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
                        entry.config(foreground="gray")
                
                entry.bind('<FocusIn>', on_entry_click)
                entry.bind('<FocusOut>', on_focusout)
