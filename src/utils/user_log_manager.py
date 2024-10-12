# src/utils/user_log_manager.py

import logging
from logging.handlers import RotatingFileHandler
from src.config.config_manager import ConfigManager
from typing import List, Optional
import os

class UserLogManager:
    def __init__(self):
        config_manager = ConfigManager()
        log_config = config_manager.get_log_config()

        self.logger = logging.getLogger('user_log')
        self.logger.setLevel(logging.INFO)

        handler = RotatingFileHandler(
            log_config['user_log_file'],
            maxBytes=log_config['max_log_size'],
            backupCount=log_config['backup_count']
        )
        formatter = logging.Formatter(log_config['user_log_format'])
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def add_log(self, message: str, level: str = 'INFO'):
        if level == 'INFO':
            self.logger.info(message)
        elif level == 'WARNING':
            self.logger.warning(message)
        elif level == 'ERROR':
            self.logger.error(message)

    def get_recent_logs(self, n: int = 100) -> List[str]:
        with open(self.logger.handlers[0].baseFilename, 'r') as f:
            logs = f.readlines()[-n:]
        return logs

    def clear_logs(self):
        with open(self.logger.handlers[0].baseFilename, 'w'):
            pass