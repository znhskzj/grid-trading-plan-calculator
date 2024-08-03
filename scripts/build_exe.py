import os
import subprocess
import sys
import tkinter as tk


def install_dependencies():
    print("Installing required packages...")
    packages = ["pyinstaller", "numpy", "pyyaml", "structlog", "pytest", "pylint", "black"]
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
        "--name=Grid Trading Tool",
        "--add-data=app_icon.ico;.",
        "--icon=app_icon.ico",
        "grid_trading_app.py"
    ]
    subprocess.check_call(pyinstaller_command)


def main():
    check_tkinter()
    install_dependencies()
    build_exe()
    print("Build complete. Executable can be found in the 'dist' folder.")


if __name__ == "__main__":
    main()
