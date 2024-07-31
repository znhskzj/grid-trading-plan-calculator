import os
import subprocess
import sys
import tkinter as tk  # 添加这行来检查 tkinter 是否可用


def install_dependencies():
    print("Installing required packages...")
    packages = ["pyinstaller", "numpy"]  # 移除 "tkinter"
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def check_tkinter():
    try:
        tk.Tk()
        print("Tkinter is available.")
    except:
        print("Error: Tkinter is not properly installed.")
        print("Please ensure you have Tkinter installed with your Python distribution.")
        sys.exit(1)


def build_exe():
    print("Building executable...")
    pyinstaller_command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=Grid Trading Plan Calculator",
        "--add-data=app_icon.ico;.",
        "--icon=app_icon.ico",
        "grid_buying_plan_gui.py"
    ]
    subprocess.check_call(pyinstaller_command)


def main():
    check_tkinter()  # 添加这行来检查 tkinter
    install_dependencies()
    build_exe()
    print("Build complete. Executable can be found in the 'dist' folder.")


if __name__ == "__main__":
    main()
