# src/utils.py

import sys
import os
import logging
import requests
import subprocess
from functools import wraps
from packaging import version
from tqdm import tqdm

# 创建一个模块级的 logger
logger = logging.getLogger(__name__)

def exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True, extra={'config_module': func.__module__})
            raise
    return wrapper

def get_current_version():
    """
    从 version.py 文件中获取当前版本
    """
    try:
        with open('version.py', 'r') as f:
            exec(f.read())
        return locals()['VERSION']
    except Exception as e:
        logger.error(f"Error reading version.py: {str(e)}")
        return None

def compare_versions(current_version, latest_version):
    """
    比较当前版本和最新版本
    返回 True 如果有新版本可用，否则返回 False
    """
    return version.parse(latest_version) > version.parse(current_version)

@exception_handler
def get_latest_version():
    """
    从 GitHub 获取最新版本信息
    """
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
def download_update(version):
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
def install_update(filename):
    if sys.platform.startswith('win'):
        subprocess.Popen([filename], shell=True)
        sys.exit()
    else:
        logger.error("自动更新只支持 Windows 系统")

def check_for_updates():
    current_version = get_current_version()
    latest_version = get_latest_version()
    
    if latest_version and compare_versions(current_version, latest_version):
        return latest_version
    return None