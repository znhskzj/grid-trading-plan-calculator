# src/status_manager.py

from typing import Optional

class StatusManager:
    _instance: Optional['StatusManager'] = None

    @classmethod
    def set_instance(cls, instance: 'StatusManager') -> None:
        cls._instance = instance

    @classmethod
    def update_status(cls, message: str) -> None:
        if cls._instance:
            cls._instance._update_status_impl(message)
        else:
            print(f"Status: {message}")  # 如果实例未设置，则打印到控制台

    def _update_status_impl(self, message: str) -> None:
        # 这个方法应该在子类中实现
        raise NotImplementedError("Subclasses must implement _update_status_impl method")