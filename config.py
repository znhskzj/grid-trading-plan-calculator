import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "funds": 50000,
    "initial_price": 26.7,
    "stop_loss_price": 25.5,
    "num_grids": 10,
    "allocation_method": 0
}


def load_config(config_file: str = 'config.json') -> Dict:
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"配置已从 {config_file} 加载")
        return config
    except FileNotFoundError:
        logger.warning(f"配置文件 {config_file} 不存在，使用默认配置")
        save_config(DEFAULT_CONFIG, config_file)
        return DEFAULT_CONFIG
    except json.JSONDecodeError:
        logger.error(f"配置文件 {config_file} 格式错误，使用默认配置")
        return DEFAULT_CONFIG


def save_config(config: Dict, config_file: str = 'config.json'):
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    logger.info(f"配置已保存到 {config_file}")
