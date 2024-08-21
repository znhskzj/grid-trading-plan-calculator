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
BUILD_DIR = 'build'
SPEC_FILE = os.path.join(BUILD_DIR, f'{APP_NAME}.spec')

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
    for item in ['dist', SPEC_FILE]:
        if os.path.isdir(item):
            shutil.rmtree(item)
        elif os.path.isfile(item):
            os.remove(item)

def build_exe():
    logging.info("Building executable...")
    if not os.path.exists(SPEC_FILE):
        # Generate spec file if it doesn't exist
        pyinstaller_command = [
            "pyinstaller",
            "--name", APP_NAME,
            "--specpath", BUILD_DIR,
            "--add-data", "assets/icons/app_icon.ico;assets/icons",
            "--icon", "assets/icons/app_icon.ico",
            "--add-data", "src;src",
            "grid_trading_app.py"
        ]
        run_command(pyinstaller_command, "Error generating spec file")

    # Build using the spec file
    build_command = [
        "pyinstaller",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name={EXE_NAME}",
        SPEC_FILE
    ]
    run_command(build_command, "Error building executable")

def main():
    check_tkinter()
    install_dependencies()
    clean_build()
    build_exe()
    logging.info(f"Build complete. Executable '{EXE_NAME}' can be found in the 'dist' folder.")

if __name__ == "__main__":
    main()