# src/utils/logger.py

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file='grid_trading.log', level=logging.INFO):
    """
    设置日志记录器
    
    :param name: 日志记录器的名称
    :param log_file: 日志文件名，默认为 'grid_trading.log'
    :param level: 日志级别，默认为 INFO
    :return: 配置好的日志记录器
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
    
    file_handler = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# 创建一个全局的主日志记录器
main_logger = setup_logger('grid_trading')