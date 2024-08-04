import os
import configparser
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_CONFIG = {
    'General': {
        'funds': '50000.0',
        'initial_price': '50.0',
        'stop_loss_price': '30.0',
        'num_grids': '10',
        'allocation_method': '1'
    }, 'CommonStocks': {
        'stock1': 'AAPL',
        'stock2': 'GOOGL',
        'stock3': 'MSFT',
        'stock4': 'AMZN',
        'stock5': 'FB'
    }

}


def load_config(config_file: str = 'config.ini') -> Dict[str, Dict[str, str]]:
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

    return {section: dict(config[section]) for section in config.sections()}


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
