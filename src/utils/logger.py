# src/utils/logger.py

import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    设置日志记录器
    
    :param name: 日志记录器的名称
    :param log_file: 日志文件名，默认为 'grid_trading.log'
    :param level: 日志级别，默认为 INFO
    :return: 配置好的日志记录器
    """
    if log_file is None:
        # 移除这里的 'logs' 文件夹
        log_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        log_file = os.path.join(log_dir, 'logs', f'{name}.log')
    
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
    
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
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