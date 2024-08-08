# script/build_exe.py

import sys
import os
import subprocess
import tkinter as tk
import shutil
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from version import VERSION

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_NAME = os.environ.get('APP_NAME', 'Grid Trading Tool')
EXE_NAME = f"{APP_NAME}-{VERSION}"

def run_command(command, error_message):
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        logging.error(f"{error_message}: {e}")
        sys.exit(1)

def install_dependencies():
    logging.info("Installing required packages...")
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "Failed to install dependencies")

def check_tkinter():
    try:
        tk.Tk()
        logging.info("Tkinter is available.")
    except:
        logging.error("Tkinter is not properly installed.")
        logging.error("Please ensure you have Tkinter installed with your Python distribution.")
        sys.exit(1)

def clean_build():
    logging.info("Cleaning old build files...")
    for item in ['build', 'dist', f'{APP_NAME}.spec']:
        if os.path.isdir(item):
            shutil.rmtree(item)
        elif os.path.isfile(item):
            os.remove(item)

def build_exe():
    logging.info("Building executable...")
    pyinstaller_command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name={EXE_NAME}",
        "--add-data=assets/icons/app_icon.ico;assets/icons",
        "--icon=assets/icons/app_icon.ico",
        "--add-data=src;src",
        "grid_trading_app.py"
    ]
    run_command(pyinstaller_command, "Error building executable")

def update_readme():
    run_command([sys.executable, "scripts/update_readme.py"], "Failed to update README")

def run_tests():
    logging.info("Running tests...")
    run_command([sys.executable, "-m", "pytest"], "Tests failed")

def main():
    check_tkinter()
    install_dependencies()
    run_tests()
    update_readme()
    clean_build()
    build_exe()
    logging.info(f"Build complete. Executable '{EXE_NAME}' can be found in the 'dist' folder.")

if __name__ == "__main__":
    main()