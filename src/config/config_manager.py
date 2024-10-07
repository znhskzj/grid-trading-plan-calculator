
import os
import io
import configparser
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

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
        加载系统配置。
        如果配置文件不存在，则使用默认配置。
        """
        config = configparser.ConfigParser()
        config.read_dict(DEFAULT_CONFIG)
        
        if os.path.exists(self.system_config_path):
            config.read(self.system_config_path)
        
        return {section: dict(config[section]) for section in config.sections()}

    def save_system_config(self) -> None:
        config_parser = configparser.ConfigParser()
        for section, values in self.system_config.items():
            config_parser[section] = values

        with open(self.system_config_path, 'w') as f:
            config_parser.write(f)
        logger.info(f"系统配置已保存到 {self.system_config_path}")

    def load_user_config(self) -> Dict[str, Any]:
        config = configparser.ConfigParser()
        if os.path.exists(self.user_config_path):
            with io.open(self.user_config_path, 'r', encoding='utf-8') as f:
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

    def save_user_config(self) -> None:
        config_parser = configparser.ConfigParser()
        for section, options in self.user_config.items():
            config_parser[section] = {k: str(v) for k, v in options.items()}  # 确保所有值都转换为字符串
        
        with open(self.user_config_path, 'w', encoding='utf-8') as configfile:
            config_parser.write(configfile)
        logger.info(f"用户配置已保存到 {self.user_config_path}")

    def ensure_config_structure(self):
        for section, values in DEFAULT_USER_CONFIG.items():
            if section not in self.user_config:
                self.user_config[section] = {}
            for key, default_value in values.items():
                if key not in self.user_config[section]:
                    self.user_config[section][key] = default_value

    def load_configurations(self) -> None:
        self.system_config = self.load_system_config()
        self.user_config = self.load_user_config()
        self.ensure_config_structure()

    def save_user_settings(self) -> None:
        """保存用户设置"""
        try:
            # 更新用户配置
            # 注意：这里需要修改，因为 self.api_choice 等属性不应该在 ConfigManager 中
            # 这部分逻辑应该在 GUI 类中处理，然后调用 ConfigManager 的方法来保存
            self.save_user_config()
            logger.info("用户设置已自动保存")

            # 加载保存后的配置进行比较
            loaded_config = self.load_user_config()
            
            # 比较配置
            if self.user_config != loaded_config:
                logger.warning("保存的配置与加载的配置不匹配，可能存在保存问题")
                # 使用 json.dumps 来创建可比较的字符串
                original = json.dumps(self.user_config, sort_keys=True)
                loaded = json.dumps(loaded_config, sort_keys=True)
                logger.debug(f"原始配置: {original}")
                logger.debug(f"加载的配置: {loaded}")
                # 找出差异
                import difflib
                diff = list(difflib.unified_diff(original.splitlines(), loaded.splitlines()))
                logger.debug(f"配置差异:\n" + "\n".join(diff))
        except Exception as e:
            logger.error(f"保存用户设置时发生错误: {str(e)}", exc_info=True)

    def load_user_settings(self) -> None:
        """加载用户设置"""
        # 这个方法应该在 GUI 类中实现，因为它涉及到 GUI 组件的更新
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        # 先从用户配置中查找，如果没有再从系统配置中查找
        return self.user_config.get(key, self.system_config.get(key, default))

    def set_config(self, key: str, value: Any, is_system_config: bool = False) -> None:
        if is_system_config:
            self.system_config[key] = value
            self.save_system_config()
        else:
            self.user_config[key] = value
            self.save_user_config()

    def reset_to_default(self) -> None:
        # 重置配置到默认状态
        self.user_config = DEFAULT_USER_CONFIG.copy()
        self.save_user_config()

    # API 相关方法
    def get_api_config(self) -> Dict[str, Any]:
        return self.user_config.get('API', {})

    def set_api_config(self, api_config: Dict[str, Any]) -> None:
        self.user_config['API'] = api_config
        self.save_user_config()

    # 交易逻辑相关方法
    def get_trading_config(self) -> Dict[str, Any]:
        return self.user_config.get('Trading', {})

    def set_trading_config(self, trading_config: Dict[str, Any]) -> None:
        self.user_config['Trading'] = trading_config
        self.save_user_config()