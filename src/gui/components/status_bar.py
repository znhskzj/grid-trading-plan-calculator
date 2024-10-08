# src/gui/components/status_bar.py

import tkinter as tk
from typing import Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class StatusBar(tk.Frame):
    def __init__(self, master: tk.Widget):
        super().__init__(master)
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X)
        logger.debug("状态栏初始化完成")

    def set(self, format_string: str, *args: Any) -> None:
        try:
            self.label.config(text=format_string % args)
            self.label.update_idletasks()
            logger.debug(f"状态栏更新: {format_string % args}")
        except Exception as e:
            logger.error(f"更新状态栏时发生错误: {str(e)}")

    def clear(self) -> None:
        try:
            self.label.config(text="")
            self.label.update_idletasks()
            logger.debug("状态栏已清空")
        except Exception as e:
            logger.error(f"清空状态栏时发生错误: {str(e)}")