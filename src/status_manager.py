# src/status_manager.py

class StatusManager:
    _instance = None

    @classmethod
    def set_instance(cls, instance):
        cls._instance = instance

    @classmethod
    def update_status(cls, message):
        if cls._instance:
            cls._instance.update_status(message)
        else:
            print(f"Status: {message}")  # 如果实例未设置，则打印到控制台
