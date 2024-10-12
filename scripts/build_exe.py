import sys
import os
import subprocess
import tkinter as tk
import shutil
import logging
import time
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, 'build_log.txt')

sys.path.append(project_root)
from version import VERSION

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=log_file_path, filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

APP_NAME = os.environ.get('APP_NAME', 'Grid Trading Tool')
EXE_NAME = f"{APP_NAME}-{VERSION}"
BUILD_DIR = os.path.join(project_root, 'build')
DIST_DIR = os.path.join(project_root, 'dist')
SPEC_FILE = os.path.join(BUILD_DIR, f'{APP_NAME}.spec')

def run_command(command, error_message):
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        logging.error(f"{error_message}: {e}")
        sys.exit(1)

def install_dependencies():
    logging.info("Installing required packages...")
    requirements_path = os.path.join(project_root, 'requirements.txt')
    run_command([sys.executable, "-m", "pip", "install", "-r", requirements_path, "--upgrade"],
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
    for item in [BUILD_DIR, DIST_DIR, SPEC_FILE]:
        try:
            if os.path.isdir(item):
                shutil.rmtree(item)
            elif os.path.isfile(item):
                os.remove(item)
            logging.info(f"Removed: {item}")
        except PermissionError:
            logging.warning(f"Unable to remove {item} due to permission error. Please close any open files or applications.")
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error removing {item}: {e}")

def create_spec_file():
    import moomoo
    print(f"moomoo.__path__ = {moomoo.__path__}")
    icon_path = os.path.join(project_root, 'assets', 'icons', 'app_icon.ico')
    src_path = os.path.join(project_root, 'src')
    main_script = os.path.join(project_root, "grid_trading_app.py")

    if not os.path.exists(main_script):
        logging.error(f"Main script not found: {main_script}")
        sys.exit(1)

    moomoo_path = subprocess.check_output([sys.executable, "-c", 
                                           "import moomoo; print(moomoo.__path__[0])"], 
                                           text=True).strip()

    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [r'{main_script}'],
    pathex=[r'{project_root}'],
    binaries=[],
    datas=[
    (r'{icon_path}', 'assets/icons'),
    (r'{src_path}', 'src'),
    (r'{moomoo_path}', 'moomoo'),
],
    hiddenimports=[
        'moomoo',
        'moomoo.common.pb',
        'moomoo.common.pb.Common_pb2',
        'moomoo.common.pb.Qot_Common_pb2',
        'moomoo.common.pb.Qot_GetCodeChange_pb2',
        'moomoo.common.constant',
        'moomoo.common.utils',
        'moomoo.common.open_context_base',
        'moomoo.quote.open_quote_context',
        'moomoo.common.pb.Trd_Common_pb2',
        'moomoo.common.pb.Verification_pb2',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=r'{EXE_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging, change to False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{icon_path}',
)
"""
    print(f"Checking paths:")
    print(f"Main script: {os.path.exists(main_script)}")
    print(f"Icon path: {os.path.exists(icon_path)}")
    print(f"Source path: {os.path.exists(src_path)}")
    print(f"Moomoo path: {os.path.exists(moomoo_path)}")
    with open(SPEC_FILE, 'w') as f:
        f.write(spec_content)
    logging.info(f"Created spec file: {SPEC_FILE}")

def build_exe():
    logging.info("Building executable...")
    if not os.path.exists(SPEC_FILE):
        create_spec_file()

    build_command = [
        "pyinstaller",
        "--clean",
        "--log-level=DEBUG",
        SPEC_FILE
    ]
    try:
        subprocess.check_output(build_command, stderr=subprocess.STDOUT, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"PyInstaller failed with error code {e.returncode}")
        logging.error(f"Command output:\n{e.output}")
        raise

def verify_build():
    exe_path = os.path.join(DIST_DIR, f"{EXE_NAME}.exe")
    if not os.path.exists(exe_path):
        logging.error(f"Executable not found: {exe_path}")
        return False
    
    logging.info(f"Executable created successfully: {exe_path}")
    return True

def main():
    try:
        check_tkinter()
        install_dependencies()
        clean_build()
        build_exe()
        if verify_build():
            logging.info(f"Build complete. Executable '{EXE_NAME}.exe' can be found in the 'dist' folder.")
        else:
            logging.error("Build process failed to produce the expected executable.")
    except Exception as e:
        logging.exception("An unexpected error occurred during the build process:")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    main()