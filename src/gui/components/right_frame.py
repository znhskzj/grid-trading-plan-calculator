# src/gui/components/right_frame.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from src.utils.gui_helpers import validate_float_input, validate_int_input

logger = logging.getLogger(__name__)

class RightFrame(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.initialize_variables()
        self.create_widgets()
        self.connect_controller()

    def initialize_variables(self):
        self.funds_var = tk.StringVar()
        self.initial_price_var = tk.StringVar()
        self.stop_loss_price_var = tk.StringVar()
        self.num_grids_var = tk.StringVar()
        self.instruction_var = tk.StringVar()
        self.allocation_method_var = tk.StringVar(value="0")
        self.api_choice = tk.StringVar(value="yahoo")
        self.trade_mode_var = tk.StringVar(value="模拟")
        self.market_var = tk.StringVar(value="美股")
        self.alpha_vantage_key = tk.StringVar()
        self.available_apis = ["yahoo", "alpha_vantage"]  # 这应该从配置或API管理器获取
        self.force_simulate = False

    def create_widgets(self):
        self.create_input_fields()
        self.create_option_frame()
        self.create_allocation_method_widgets()
        self.create_buttons()
        self.create_api_widgets()
        self.create_moomoo_settings()

    def create_input_fields(self):
        labels = ["可用资金:", "初始价格:", "止损价格:", "网格数量:", "交易指令:"]
        vars = [self.funds_var, self.initial_price_var, self.stop_loss_price_var, self.num_grids_var, self.instruction_var]

        for i, (label, var) in enumerate(zip(labels, vars)):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky="e", pady=2)
            entry = ttk.Entry(self, textvariable=var, width=20)
            entry.grid(row=i, column=1, sticky="ew", padx=(5, 0), pady=2)
            
            if label == "可用资金:" or label == "初始价格:" or label == "止损价格:":
                entry.config(validate="key", validatecommand=(self.register(validate_float_input), '%d', '%P'))
            elif label == "网格数量:":
                entry.config(validate="key", validatecommand=(self.register(validate_int_input), '%d', '%P'))
            
            if label == "交易指令:":
                entry.config(width=50)
                entry.grid(columnspan=2)
                
                entry.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
                entry.config(foreground="gray")
                
                entry.bind('<FocusIn>', self.on_entry_click)
                entry.bind('<FocusOut>', self.on_focusout)

    def create_option_frame(self):
        option_frame = ttk.Frame(self)
        option_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        option_frame.grid_columnconfigure(0, weight=2)
        option_frame.grid_columnconfigure(1, weight=1)
        option_frame.grid_columnconfigure(2, weight=1)
        
        self.create_allocation_method_widgets(option_frame)
        self.create_api_widgets(option_frame)
        self.create_moomoo_settings(option_frame)

    def create_allocation_method_widgets(self, parent_frame):
        allocation_frame = ttk.LabelFrame(parent_frame, text="分配方式")
        allocation_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        methods = [("等金额分配", "0", "均匀分配资金"),
                   ("等比例分配", "1", "指数增长分配"),
                   ("线性加权", "2", "线性增长分配")]

        for i, (text, value, desc) in enumerate(methods):
            ttk.Radiobutton(allocation_frame, text=text, variable=self.allocation_method_var, value=value).grid(row=i, column=0, sticky="w")
            ttk.Label(allocation_frame, text=desc).grid(row=i, column=1, sticky="w", padx=(10, 0))

    def create_buttons(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=8, column=0, columnspan=2, pady=(10, 0), sticky='ew')

        buttons = [
            ("计算购买计划", self.controller.run_calculation),
            ("保留10%计算", lambda: self.controller.calculate_with_reserve(10)),
            ("保留20%计算", lambda: self.controller.calculate_with_reserve(20)),
            ("保存为CSV", self.controller.save_to_csv),
            ("重置为默认值", self.controller.reset_to_default)
        ]

        for i, (text, command) in enumerate(buttons):
            ttk.Button(button_frame, text=text, command=command).grid(row=0, column=i, padx=5, pady=(0, 5))

        separator = ttk.Separator(self, orient='horizontal')
        separator.grid(row=9, column=0, columnspan=2, sticky='ew', pady=5)

        second_row_buttons = [
            ("查询可用资金", self.controller.query_available_funds),
            ("查询持仓股票", self.controller.query_positions),
            ("按标的计划下单", self.controller.place_order_by_plan),
            ("查询历史订单", self.controller.query_history_orders),
            ("开启实时通知", self.controller.enable_real_time_notifications)
        ]

        for i, (text, command) in enumerate(second_row_buttons):
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=1, column=i, padx=5, pady=(5, 0))
            
    def create_api_widgets(self, parent_frame):
        api_frame = ttk.LabelFrame(parent_frame, text="API 选择")
        api_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        if not self.available_apis:
            logger.error("没有可用的 API")
            ttk.Label(api_frame, text="无可用 API").grid(row=0, column=0, sticky="w")
            return

        for i, api in enumerate(self.available_apis):
            display_name = "Yahoo" if api.lower() == "yahoo" else "Alpha Vantage"
            ttk.Radiobutton(api_frame, text=display_name, variable=self.api_choice, 
                            value=api, command=self.on_api_change).grid(row=i, column=0, sticky="w")

    def create_moomoo_settings(self, parent_frame):
        moomoo_frame = ttk.LabelFrame(parent_frame, text="Moomoo设置")
        moomoo_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0), pady=5)

        self.real_radio = ttk.Radiobutton(moomoo_frame, text="真实", variable=self.trade_mode_var, value="真实")
        self.real_radio.grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(moomoo_frame, text="模拟", variable=self.trade_mode_var, value="模拟").grid(row=0, column=1, sticky="w")

        ttk.Radiobutton(moomoo_frame, text="美股", variable=self.market_var, value="美股").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(moomoo_frame, text="港股", variable=self.market_var, value="港股").grid(row=1, column=1, sticky="w")

        ttk.Button(moomoo_frame, text="测试连接", command=self.controller.test_moomoo_connection).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Button(moomoo_frame, text="切换强制模拟模式", command=self.toggle_force_simulate).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.update_moomoo_settings_state()

    def update_moomoo_settings_state(self):
        if self.force_simulate:
            self.real_radio.config(state="disabled")
            self.trade_mode_var.set("模拟")
        else:
            self.real_radio.config(state="normal")

    def on_api_change(self):
        new_api_choice = self.api_choice.get()
        if new_api_choice == 'alpha_vantage':
            self._handle_alpha_vantage_selection()
        else:
            self.controller.initialize_api_manager()
        
        self.controller.update_status(f"已切换到 {new_api_choice} API")
        self.controller.save_user_settings()

    def _handle_alpha_vantage_selection(self):
        existing_key = self.alpha_vantage_key.get()
        if not existing_key:
            messagebox.showinfo("Alpha Vantage API 提示",
                                "请注意：Alpha Vantage 免费版 API 有每日请求次数限制。\n"
                                "建议仅在必要时使用，以避免达到限制。")
            self.prompt_for_alpha_vantage_key()
        else:
            messagebox.showinfo("Alpha Vantage API", f"使用已保存的 API Key: {existing_key[:5]}...")
            self.controller.initialize_api_manager()

    def prompt_for_alpha_vantage_key(self):
        new_key = simpledialog.askstring("Alpha Vantage API Key",
                                        "请输入您的 Alpha Vantage API Key:",
                                        initialvalue=self.alpha_vantage_key.get())
        if new_key:
            self.alpha_vantage_key.set(new_key)
            self.controller.initialize_api_manager('alpha_vantage', new_key)
            self.controller.save_user_settings()
        else:
            self.api_choice.set('yahoo')
            self.controller.initialize_api_manager('yahoo', '')
            messagebox.showinfo("API 选择", "由于未提供 Alpha Vantage API Key，已切换回 Yahoo Finance API。")
            self.controller.save_user_settings()
        
        self.controller.update_status(f"已切换到 {self.api_choice.get()} API")

    def on_entry_click(self, event):
        if event.widget.get() == "例：SOXL现价到37.5之间分批买，压力39+，止损36.8":
            event.widget.delete(0, "end")
            event.widget.config(foreground="black")

    def on_focusout(self, event):
        if event.widget.get() == "":
            event.widget.insert(0, "例：SOXL现价到37.5之间分批买，压力39+，止损36.8")
            event.widget.config(foreground="gray")

    def toggle_force_simulate(self):
        self.force_simulate = not self.force_simulate
        self.update_moomoo_settings_state()

    def connect_controller(self):
        # 如果有任何需要直接连接到控制器的方法，可以在这里进行
        pass