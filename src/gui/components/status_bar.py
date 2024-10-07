# src/gui/components/status_bar.py
import tkinter as tk

class StatusBar(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X)

    def set(self, format_string, *args):
        self.label.config(text=format_string % args)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()