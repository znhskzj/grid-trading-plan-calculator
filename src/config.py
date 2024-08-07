import os
import json
import configparser
import logging
from typing import Dict

logger = logging.getLogger(__name__)

USER_CONFIG_FILE = 'user_config.json'


def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_CONFIG = {
    'General': {
        'funds': '50000.0',
        'initial_price': '50.0',
        'stop_loss_price': '30.0',
        'num_grids': '10',
        'allocation_method': '1'
    },
    'CommonStocks': {
        'stock1': 'AAPL',
        'stock2': 'GOOGL',
        'stock3': 'MSFT',
        'stock4': 'AMZN',
        'stock5': 'TSLA'
    },
    'API': {
        'choice': 'yahoo',
        'alpha_vantage_key': ''
    },
    'AvailableAPIs': {
        'apis': 'yahoo,alpha_vantage'
    }
}


def load_config(config_file: str = 'config.ini') -> Dict[str, Dict[str, any]]:
    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_CONFIG)
    
    config_path = os.path.join(get_project_root(), config_file)
    if os.path.exists(config_path):
        try:
            config.read(config_path)
            logger.info(f"配置已从 {config_path} 加载", extra={'config_module': 'config'})
        except configparser.Error as e:
            logger.error(f"配置文件 {config_path} 读取错误: {str(e)}，使用默认配置", extra={'config_module': 'config'})
    else:
        logger.warning(f"配置文件 {config_path} 不存在，使用默认配置", extra={'config_module': 'config'})
        save_config(dict(config['General']), config_file)

    # 处理 AvailableAPIs
    result = {section: dict(config[section]) for section in config.sections()}
    if 'AvailableAPIs' in result:
        result['AvailableAPIs']['apis'] = result['AvailableAPIs']['apis'].split(',')

    return result

def save_config(config: Dict[str, str], config_file: str = 'config.ini'):
    config_parser = configparser.ConfigParser()
    config_parser['General'] = config

    config_path = os.path.join(get_project_root(), config_file)
    with open(config_path, 'w') as f:
        config_parser.write(f)
    logger.info(f"配置已保存到 {config_path}", extra={'config_module': 'config'})


def convert_json_to_ini(json_file: str = 'config.json', ini_file: str = 'config.ini'):
    import json
    try:
        json_path = os.path.join(get_project_root(), json_file)
        ini_path = os.path.join(get_project_root(), ini_file)

        with open(json_path, 'r') as f:
            json_config = json.load(f)

        config = {'General': {k: str(v) for k, v in json_config.items()}}
        save_config(config['General'], ini_file)
        logger.info(f"JSON 配置已转换并保存为 INI 格式: {ini_path}", extra={'config_module': 'config'})
    except Exception as e:
        logger.error(f"转换 JSON 到 INI 失败: {str(e)}", extra={'config_module': 'config'})

def get_user_config_path():
    return os.path.join(get_project_root(), USER_CONFIG_FILE)

def load_user_config() -> Dict[str, any]:
    config = configparser.ConfigParser()
    config_path = os.path.join(get_project_root(), 'config.ini')
    if os.path.exists(config_path):
        config.read(config_path)
        user_config = {
            'API': {
                'choice': config.get('API', 'choice', fallback='yahoo'),
                'alpha_vantage_key': config.get('API', 'alpha_vantage_key', fallback='')
            },
            'allocation_method': config.get('General', 'allocation_method', fallback='1'),
            'common_stocks': [config.get('CommonStocks', f'stock{i}', fallback='') for i in range(1, 6) if config.get('CommonStocks', f'stock{i}', fallback='')]
        }
        return user_config
    return {}

def save_user_config(config):
    config_path = get_user_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("用户配置已保存")
    except Exception as e:
        logger.error(f"保存用户配置时发生错误: {str(e)}")