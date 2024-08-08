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


def install_dependencies():
    logging.info("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install dependencies: {e}")
        sys.exit(1)


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
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['Grid Trading Tool.spec']
    for dir in dirs_to_clean:
        if os.path.exists(dir):
            shutil.rmtree(dir)
    for file in files_to_clean:
        if os.path.exists(file):
            os.remove(file)


def build_exe():
    logging.info("Building executable...")
    exe_name = f"Grid Trading Tool-{VERSION}"
    pyinstaller_command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        "--add-data=assets/icons/app_icon.ico;assets/icons",
        "--icon=assets/icons/app_icon.ico",
        "--add-data=src;src",
        "grid_trading_app.py"
    ]
    try:
        subprocess.check_call(pyinstaller_command)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error building executable: {e}")
        sys.exit(1)

def update_readme():
    subprocess.run([sys.executable, "scripts/update_readme.py"], check=True)

def run_tests():
    logging.info("Running tests...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest"])
    except subprocess.CalledProcessError as e:
        logging.error(f"Tests failed: {e}")
        sys.exit(1)

def main():
    check_tkinter()
    install_dependencies()
    run_tests()
    update_readme()
    clean_build()
    build_exe()
    logging.info("Build complete. Executable can be found in the 'dist' folder.")

if __name__ == "__main__":
    main()
