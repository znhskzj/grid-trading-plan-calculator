"""
Grid Trading Tool
Version: 1.3.5
Author: Rong Zhu
Date: August 3, 2024
"""

import tkinter as tk
import logging
from gui import App
from config import load_config

logging.basicConfig(
    filename='grid_trading.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


def main():
    config = load_config()
    root = tk.Tk()
    root.title("Grid Trading Tool")
    app = App(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
