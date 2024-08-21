# src/utils.py

import sys
import os
import logging
import requests
import subprocess
from functools import wraps
from packaging import version
from tqdm import tqdm
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

def exception_handler(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True, extra={'config_module': func.__module__})
            raise
    return wrapper

def get_current_version() -> Optional[str]:
    try:
        with open('version.py', 'r') as f:
            exec(f.read())
        return locals().get('VERSION')
    except Exception as e:
        logger.error(f"Error reading version.py: {str(e)}")
        return None

def compare_versions(current_version: str, latest_version: str) -> bool:
    return version.parse(latest_version) > version.parse(current_version)

@exception_handler
def get_latest_version() -> Optional[str]:
    url = "https://api.github.com/repos/znhskzj/grid-trading-plan-calculator/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["tag_name"].lstrip('v')
    except Exception as e:
        logger.error(f"获取最新版本信息时出错：{e}")
        return None

@exception_handler
def download_update(version: str) -> str:
    url = f"https://github.com/znhskzj/grid-trading-plan-calculator/releases/download/v{version}/grid_trading_app.exe"
    local_filename = f"grid_trading_app-{version}.exe"
    
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        
        with open(local_filename, 'wb') as f, tqdm(
            desc=local_filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for chunk in r.iter_content(chunk_size=8192):
                size = f.write(chunk)
                progress_bar.update(size)
    
    return local_filename

@exception_handler
def install_update(filename: str) -> None:
    if sys.platform.startswith('win'):
        subprocess.Popen([filename], shell=True)
        sys.exit()
    else:
        logger.error("自动更新只支持 Windows 系统")

def check_for_updates() -> Optional[str]:
    current_version = get_current_version()
    if current_version is None:
        return None
    latest_version = get_latest_version()
    
    if latest_version and compare_versions(current_version, latest_version):
        return latest_version
    return None

def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))