# src/utils/logger.py

import logging
import os

def setup_logger(name, log_file=None, level=logging.INFO):
    """Function setup as many loggers as you want"""
    if log_file is None:
        # 设置默认日志文件路径
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'{name}.log')

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# 使用示例：
# api_logger = setup_logger('api_logger')  # 将使用默认的日志文件路径
# 或者
# api_logger = setup_logger('api_logger', 'logs/api.log')  # 指定日志文件路径