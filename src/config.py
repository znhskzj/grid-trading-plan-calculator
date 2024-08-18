# src/config.py

"""
This module handles configuration management for the Grid Trading Tool.

Two main configuration files are used:
1. config.ini: System-wide configuration containing default settings and 
   configurations that should not be directly modified by users.
2. userconfig.ini: User-specific configuration containing user preferences 
   and settings that can be modified through the application.

The system config (config.ini) should include:
- Default values for trading parameters
- GUI settings
- Available APIs
- Default common stocks

The user config (userconfig.ini) should include:
- User's API choice and API keys
- User's preferred allocation method
- User's common stocks
- Recent calculation parameters

This separation allows for easier updates and prevents user settings 
from being overwritten during application updates.
"""

# ... rest of the file content ...
import os
import io
import json
import configparser
import logging
from typing import Dict, Any
from .utils import get_project_root

logger = logging.getLogger(__name__)

USER_CONFIG_FILE = 'userconfig.ini'
SYSTEM_CONFIG_FILE = 'config.ini'

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_CONFIG = {
    'General': {
        'default_funds': '50000.0',
        'default_initial_price': '50.0',
        'default_stop_loss_price': '30.0',
        'default_num_grids': '10',
        'default_allocation_method': '1'
    },
    'GUI': {
        'window_width': '750',
        'window_height': '700'
    },
    'AvailableAPIs': {
        'apis': 'yahoo,alpha_vantage'
    },
    'DefaultCommonStocks': {
        'stock1': 'AAPL',
        'stock2': 'GOOGL',
        'stock3': 'MSFT',
        'stock4': 'AMZN',
        'stock5': 'TSLA'
    }
}

DEFAULT_USER_CONFIG = {
    'API': {
        'choice': 'yahoo',
        'alpha_vantage_key': ''
    },
    'General': {
        'allocation_method': '1'
    },
    'CommonStocks': {
        'stock1': 'AAPL',
        'stock2': 'GOOGL',
        'stock3': 'UPST',
        'stock4': 'TSLA',
        'stock5': 'SOXL'
    },
    'RecentCalculations': {
        'funds': '50000.0',
        'initial_price': '50.0',
        'stop_loss_price': '30.0',
        'num_grids': '10'
    }
}

def load_system_config() -> Dict[str, Any]:
        """
        加载系统配置。
        如果配置文件不存在，则使用默认配置。
        """
        config = configparser.ConfigParser()
        config.read_dict(DEFAULT_CONFIG)
        
        config_path = os.path.join(get_project_root(), SYSTEM_CONFIG_FILE)
        if os.path.exists(config_path):
            config.read(config_path)
        
        return {section: dict(config[section]) for section in config.sections()}

def save_system_config(config: Dict[str, Dict[str, str]], config_file: str = SYSTEM_CONFIG_FILE):
    config_parser = configparser.ConfigParser()
    for section, values in config.items():
        config_parser[section] = values

    config_path = os.path.join(get_project_root(), config_file)
    with open(config_path, 'w') as f:
        config_parser.write(f)
    logger.info(f"系统配置已保存到 {config_path}")

def load_user_config() -> Dict[str, Any]:
    config = configparser.ConfigParser()
    config_path = os.path.join(get_project_root(), 'userconfig.ini')
    if os.path.exists(config_path):
        with io.open(config_path, 'r', encoding='utf-8') as f:
            config.read_file(f)
    return {section: dict(config[section]) for section in config.sections()}

def save_user_config(config: Dict[str, Any]) -> None:
    config_parser = configparser.ConfigParser()
    for section, options in config.items():
        config_parser[section] = {k: str(v) for k, v in options.items()}  # 确保所有值都转换为字符串
    
    config_path = os.path.join(get_project_root(), USER_CONFIG_FILE)
    with open(config_path, 'w', encoding='utf-8') as configfile:
        config_parser.write(configfile)
    logger.info(f"用户配置已保存到 {config_path}")

def convert_json_to_ini(json_file: str = 'config.json', ini_file: str = SYSTEM_CONFIG_FILE):
    try:
        json_path = os.path.join(get_project_root(), json_file)
        ini_path = os.path.join(get_project_root(), ini_file)

        with open(json_path, 'r') as f:
            json_config = json.load(f)

        config = {'General': {k: str(v) for k, v in json_config.items()}}
        save_system_config(config, ini_file)
        logger.info(f"JSON 配置已转换并保存为 INI 格式: {ini_path}")
    except Exception as e:
        logger.error(f"转换 JSON 到 INI 失败: {str(e)}")