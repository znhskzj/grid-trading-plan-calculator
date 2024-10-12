# src/utils/debug_manager.py

import logging
from src.config.config_manager import ConfigManager
from src.utils.user_log_manager import UserLogManager

class DebugManager:
    def __init__(self, config_manager: ConfigManager, user_log_manager: UserLogManager):
        self.config_manager = config_manager
        self.user_log_manager = user_log_manager
        self.debug_mode = self.config_manager.is_debug_mode()
        self.debug_level = self.config_manager.get_debug_level()

    def set_debug_mode(self, enabled: bool):
        self.debug_mode = enabled
        self.config_manager.set_debug_mode(enabled)
        if enabled:
            logging.getLogger().setLevel(self.debug_level)
        else:
            logging.getLogger().setLevel(logging.INFO)

    def set_debug_level(self, level: str):
        self.debug_level = level
        self.config_manager.set_debug_level(level)
        if self.debug_mode:
            logging.getLogger().setLevel(level)

    def debug_log(self, message: str):
        if self.debug_mode:
            logging.debug(message)
            self.user_log_manager.add_log(f"[DEBUG] {message}")

    def info_log(self, message: str):
        logging.info(message)
        self.user_log_manager.add_log(message)

    def warning_log(self, message: str):
        logging.warning(message)
        self.user_log_manager.add_log(f"[WARNING] {message}")

    def error_log(self, message: str):
        logging.error(message)
        self.user_log_manager.add_log(f"[ERROR] {message}")