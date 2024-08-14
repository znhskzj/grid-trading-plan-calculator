# src/config.py

import os
import json
import configparser
import logging
from typing import Dict, Any

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
    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_CONFIG)
    
    config_path = os.path.join(get_project_root(), 'config.ini')
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
    config.read_dict(DEFAULT_USER_CONFIG)
    
    config_path = os.path.join(get_project_root(), 'user_config.ini')
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        save_user_config(dict(config))
    
    return {section: dict(config[section]) for section in config.sections()}

def save_user_config(config: Dict[str, Any]):
    config_parser = configparser.ConfigParser()
    for section, values in config.items():
        config_parser[section] = {k: str(v) for k, v in values.items()}
    
    config_path = os.path.join(get_project_root(), 'user_config.ini')
    with open(config_path, 'w') as f:
        config_parser.write(f)

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