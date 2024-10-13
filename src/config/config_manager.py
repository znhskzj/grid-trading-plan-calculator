# /src/config/config_manager.py

import os
import io
import configparser
import json
import difflib
from typing import Dict, Any
from configparser import ConfigParser, ExtendedInterpolation
import logging

logger = logging.getLogger('config_manager')

DEFAULT_CONFIG = {
    'General': {
        'default_funds': '50000.0',
        'default_initial_price': '50.0',
        'default_stop_loss_price': '30.0',
        'default_num_grids': '5',
        'max_num_grids': '10',
        'default_allocation_method': '1',
        'debug_mode': 'False',
        'debug_level': 'INFO'
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
    },
    'Logging': {
        'log_dir': 'logs',
        'system_log_file': 'system.log',
        'user_log_file': 'user.log',
        'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'user_log_format': '%(asctime)s - %(levelname)s - %(message)s',
        'max_log_size': '5242880',
        'backup_count': '3'
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

USER_CONFIG_FILE = 'userconfig.ini'
SYSTEM_CONFIG_FILE = 'config.ini'

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.system_config = {}
            cls._instance.user_config = {}
            cls._instance.config_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            cls._instance.system_config_path = os.path.join(cls._instance.config_dir, SYSTEM_CONFIG_FILE)
            cls._instance.user_config_path = os.path.join(cls._instance.config_dir, USER_CONFIG_FILE)
            cls._instance.load_configurations()
        return cls._instance

    def load_configurations(self) -> None:
        """加载系统和用户配置"""
        self.system_config = self.load_system_config()
        self.user_config = self.load_user_config()
        self.ensure_config_structure()

    def load_system_config(self) -> Dict[str, Any]:
        """加载系统配置。如果配置文件不存在，则使用默认配置。"""
        config = ConfigParser(interpolation=None)
        config.read_dict(DEFAULT_CONFIG)
        
        if os.path.exists(self.system_config_path):
            config.read(self.system_config_path)
        
        return {section: dict(config[section]) for section in config.sections()}

    def load_user_config(self) -> Dict[str, Any]:
        """加载用户配置。如果配置文件不存在或为空，则使用默认配置。"""
        config = ConfigParser(interpolation=None)
        if os.path.exists(self.user_config_path):
            with io.open(self.user_config_path, 'r', encoding='utf-8') as f:
                config.read_file(f)
        
        user_config = {section: dict(config[section]) for section in config.sections()}
        
        if not user_config:
            return DEFAULT_USER_CONFIG.copy()
        
        for section, values in DEFAULT_USER_CONFIG.items():
            if section not in user_config:
                user_config[section] = {}
            for key, default_value in values.items():
                if key not in user_config[section]:
                    user_config[section][key] = default_value
        
        return user_config

    def ensure_config_structure(self) -> None:
        """确保用户配置结构完整"""
        for section, values in DEFAULT_USER_CONFIG.items():
            if section not in self.user_config:
                self.user_config[section] = {}
            for key, default_value in values.items():
                if key not in self.user_config[section]:
                    self.user_config[section][key] = default_value

    def save_system_config(self) -> None:
        """保存系统配置到文件"""
        config_parser = ConfigParser(interpolation=None)
        for section, values in self.system_config.items():
            config_parser[section] = values

        with open(self.system_config_path, 'w') as f:
            config_parser.write(f)
        logger.info(f"系统配置已保存到 {self.system_config_path}")

    def save_user_config(self) -> None:
        """保存用户配置到文件"""
        config_parser = ConfigParser(interpolation=None)
        for section, options in self.user_config.items():
            config_parser[section] = {k: str(v) for k, v in options.items()}
        
        with open(self.user_config_path, 'w', encoding='utf-8') as configfile:
            config_parser.write(configfile)
        logger.info(f"用户配置已保存到 {self.user_config_path}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if isinstance(key, str) and '.' in key:
            section, option = key.split('.', 1)
            return self.user_config.get(section, {}).get(option) or \
                   self.system_config.get(section, {}).get(option, default)
        return self.user_config.get(key) or self.system_config.get(key, default)

    def set_config(self, key: str, value: Any, is_system_config: bool = False) -> None:
        """设置配置值"""
        if isinstance(key, str) and '.' in key:
            section, option = key.split('.', 1)
        else:
            section, option = key, value

        config = self.system_config if is_system_config else self.user_config

        if section not in config:
            config[section] = {}
        
        if isinstance(value, dict):
            # 如果值是字典，递归设置嵌套的配置
            for sub_key, sub_value in value.items():
                self.set_config(f"{section}.{sub_key}", sub_value, is_system_config)
        else:
            config[section][option] = value

        if is_system_config:
            self.save_system_config()
        else:
            self.save_user_config()

    def reset_to_default(self) -> None:
        """重置用户配置到默认状态"""
        self.user_config = DEFAULT_USER_CONFIG.copy()
        self.save_user_config()

    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.user_config.get('API', {})

    def set_api_config(self, api_config: Dict[str, Any]) -> None:
        """设置API配置"""
        self.user_config['API'] = api_config
        self.save_user_config()

    def get_trading_config(self) -> Dict[str, Any]:
        """获取交易配置"""
        return self.user_config.get('Trading', {})

    def set_trading_config(self, trading_config: Dict[str, Any]) -> None:
        """设置交易配置"""
        self.user_config['Trading'] = trading_config
        self.save_user_config()

    def get_price_query_api_config(self) -> Dict[str, Any]:
        """获取价格查询API配置"""
        return self.user_config.get('API', {})

    def get_trading_api_config(self) -> Dict[str, Any]:
        """获取交易API配置"""
        trading_api = self.user_config['API'].get('trading_api_choice', 'moomoo')
        if trading_api == 'moomoo':
            return self.user_config.get('MoomooAPI', {})
        return {}

    def set_price_query_api_config(self, api_config: Dict[str, Any]) -> None:
        """设置价格查询API配置"""
        if 'API' not in self.user_config:
            self.user_config['API'] = {}
        self.user_config['API'].update(api_config)
        self.save_user_config()

    def set_trading_api_config(self, api_name: str, api_config: Dict[str, Any]) -> None:
        """设置交易API配置"""
        if api_name == 'moomoo':
            self.user_config['MoomooAPI'] = api_config
        self.user_config['API']['trading_api_choice'] = api_name
        self.save_user_config()

    def is_debug_mode(self) -> bool:
        return self.get_config('General.debug_mode', 'False').lower() == 'true'

    def set_debug_mode(self, enabled: bool):
        self.set_config('General.debug_mode', str(enabled))

    def get_debug_level(self) -> str:
        return self.get_config('General.debug_level', 'INFO')

    def set_debug_level(self, level: str):
        self.set_config('General.debug_level', level)

    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        log_config = self.get_config('Logging', {})
        base_dir = self.config_dir
        log_dir = os.path.join(base_dir, log_config.get('log_dir', 'logs'))
        
        return {
            'log_dir': log_dir,
            'system_log_file': os.path.join(log_dir, log_config.get('system_log_file', 'system.log')),
            'user_log_file': os.path.join(log_dir, log_config.get('user_log_file', 'user.log')),
            'log_format': log_config.get('log_format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'user_log_format': log_config.get('user_log_format', '%(asctime)s - %(levelname)s - %(message)s'),
            'max_log_size': int(log_config.get('max_log_size', 5242880)),
            'backup_count': int(log_config.get('backup_count', 3))
        }

    def save_user_settings(self) -> None:
        """保存用户设置并进行配置比较"""
        try:
            self.save_user_config()
            logger.info("用户设置已自动保存")

            loaded_config = self.load_user_config()
            
            if self.user_config != loaded_config:
                logger.warning("保存的配置与加载的配置不匹配，可能存在保存问题")
                original = json.dumps(self.user_config, sort_keys=True)
                loaded = json.dumps(loaded_config, sort_keys=True)
                logger.debug(f"原始配置: {original}")
                logger.debug(f"加载的配置: {loaded}")
                diff = list(difflib.unified_diff(original.splitlines(), loaded.splitlines()))
                logger.debug(f"配置差异:\n" + "\n".join(diff))
        except Exception as e:
            logger.error(f"保存用户设置时发生错误: {str(e)}", exc_info=True)

    def save_config(self):
        self.save_user_config()
        self.save_system_config()