# /src/config/config_manager.py

import os
import io
import configparser
import json
import difflib
from typing import Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger('config_manager')

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

USER_CONFIG_FILE = 'userconfig.ini'
SYSTEM_CONFIG_FILE = 'config.ini'

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.system_config = {}
            cls._instance.user_config = {}
        return cls._instance

    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), '..')
        self.system_config_path = os.path.join(self.config_dir, SYSTEM_CONFIG_FILE)
        self.user_config_path = os.path.join(self.config_dir, USER_CONFIG_FILE)
        self.load_configurations()

    def load_system_config(self) -> Dict[str, Any]:
        """
        加载系统配置。如果配置文件不存在，则使用默认配置。
        
        :return: 系统配置字典
        """
        config = configparser.ConfigParser()
        config.read_dict(DEFAULT_CONFIG)
        
        if os.path.exists(self.system_config_path):
            config.read(self.system_config_path)
        
        return {section: dict(config[section]) for section in config.sections()}

    def save_system_config(self) -> None:
        """
        保存系统配置到文件
        """
        config_parser = configparser.ConfigParser()
        for section, values in self.system_config.items():
            config_parser[section] = values

        with open(self.system_config_path, 'w') as f:
            config_parser.write(f)
        logger.info(f"系统配置已保存到 {self.system_config_path}")

    def load_user_config(self) -> Dict[str, Any]:
        """
        加载用户配置。如果配置文件不存在或为空，则使用默认配置。
        
        :return: 用户配置字典
        """
        config = configparser.ConfigParser()
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

    def save_user_config(self) -> None:
        """
        保存用户配置到文件
        """
        config_parser = configparser.ConfigParser()
        for section, options in self.user_config.items():
            config_parser[section] = {k: str(v) for k, v in options.items()}
        
        with open(self.user_config_path, 'w', encoding='utf-8') as configfile:
            config_parser.write(configfile)
        logger.info(f"用户配置已保存到 {self.user_config_path}")

    def ensure_config_structure(self) -> None:
        """
        确保用户配置结构完整
        """
        for section, values in DEFAULT_USER_CONFIG.items():
            if section not in self.user_config:
                self.user_config[section] = {}
            for key, default_value in values.items():
                if key not in self.user_config[section]:
                    self.user_config[section][key] = default_value

    def load_configurations(self) -> None:
        """
        加载系统和用户配置
        """
        self.system_config = self.load_system_config()
        self.user_config = self.load_user_config()
        self.ensure_config_structure()

    def save_user_settings(self) -> None:
        """
        保存用户设置并进行配置比较
        """
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

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        :param key: 配置键
        :param default: 默认值
        :return: 配置值
        """
        return self.user_config.get(key, self.system_config.get(key, default))

    def set_config(self, key: str, value: Any, is_system_config: bool = False) -> None:
        """
        设置配置值
        
        :param key: 配置键
        :param value: 配置值
        :param is_system_config: 是否为系统配置
        """
        if is_system_config:
            self.system_config[key] = value
            self.save_system_config()
        else:
            self.user_config[key] = value
            self.save_user_config()

    def reset_to_default(self) -> None:
        """
        重置用户配置到默认状态
        """
        self.user_config = DEFAULT_USER_CONFIG.copy()
        self.save_user_config()

    def get_api_config(self) -> Dict[str, Any]:
        """
        获取API配置
        
        :return: API配置字典
        """
        return self.user_config.get('API', {})

    def set_api_config(self, api_config: Dict[str, Any]) -> None:
        """
        设置API配置
        
        :param api_config: API配置字典
        """
        self.user_config['API'] = api_config
        self.save_user_config()

    def get_trading_config(self) -> Dict[str, Any]:
        """
        获取交易配置
        
        :return: 交易配置字典
        """
        return self.user_config.get('Trading', {})

    def set_trading_config(self, trading_config: Dict[str, Any]) -> None:
        """
        设置交易配置
        
        :param trading_config: 交易配置字典
        """
        self.user_config['Trading'] = trading_config
        self.save_user_config()

    def get_price_query_api_config(self) -> Dict[str, Any]:
        """
        获取价格查询API配置
        
        :return: 价格查询API配置字典
        """
        return self.user_config.get('API', {})

    def get_trading_api_config(self) -> Dict[str, Any]:
        """
        获取交易API配置
        
        :return: 交易API配置字典
        """
        trading_api = self.user_config['API'].get('trading_api_choice', 'moomoo')
        if trading_api == 'moomoo':
            return self.user_config.get('MoomooAPI', {})
        # 为未来的其他交易API添加支持
        # elif trading_api == 'fidelity':
        #     return self.user_config.get('FidelityAPI', {})
        else:
            return {}

    def set_price_query_api_config(self, api_config: Dict[str, Any]) -> None:
        """
        设置价格查询API配置
        
        :param api_config: 价格查询API配置字典
        """
        if 'API' not in self.user_config:
            self.user_config['API'] = {}
        self.user_config['API'].update(api_config)
        self.save_user_config()

    def set_trading_api_config(self, api_name: str, api_config: Dict[str, Any]) -> None:
        """
        设置交易API配置
        
        :param api_name: API名称
        :param api_config: API配置字典
        """
        if api_name == 'moomoo':
            self.user_config['MoomooAPI'] = api_config
        # 为未来的其他交易API添加支持
        # elif api_name == 'fidelity':
        #     self.user_config['FidelityAPI'] = api_config
        self.user_config['API']['trading_api_choice'] = api_name
        self.save_user_config()