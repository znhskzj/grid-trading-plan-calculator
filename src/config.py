# src/config.py

"""
This module handles configuration management for the Grid Trading Tool.

It manages two main configuration files:
1. config.ini: System-wide configuration with default settings.
2. userconfig.ini: User-specific configuration with customizable settings.

This separation allows for easier updates and prevents user settings 
from being overwritten during application updates.
"""

import os
import io
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
        'stock2': 'SOXL',
        'stock3': 'UPST',
        'stock4': 'OXY',
        'stock5': 'DE'
    },
    'MoomooSettings': {
        'trade_mode': '模拟',
        'market': '港股'
    },
    'MoomooAPI': {
        'host': '127.0.0.1',
        'port': '11111',
        'trade_env': 'REAL',
        'security_firm': 'FUTUINC'
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
    
    user_config = {section: dict(config[section]) for section in config.sections()}
    
    # 如果配置为空，返回默认配置
    if not user_config:
        return DEFAULT_USER_CONFIG.copy()
    
    # 使用默认配置填充缺失的部分
    for section, values in DEFAULT_USER_CONFIG.items():
        if section not in user_config:
            user_config[section] = {}
        for key, default_value in values.items():
            if key not in user_config[section]:
                user_config[section][key] = default_value
    
    return user_config

def save_user_config(config: Dict[str, Any]) -> None:
    config_parser = configparser.ConfigParser()
    for section, options in config.items():
        config_parser[section] = {k: str(v) for k, v in options.items()}  # 确保所有值都转换为字符串
    
    config_path = os.path.join(get_project_root(), USER_CONFIG_FILE)
    with open(config_path, 'w', encoding='utf-8') as configfile:
        config_parser.write(configfile)
    logger.info(f"用户配置已保存到 {config_path}")

