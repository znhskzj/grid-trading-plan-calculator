# src/utils/gui_helpers.py

import os
import functools
from tkinter import messagebox
from src.utils.logger import main_logger as logger

def validate_float_input(action: str, value_if_allowed: str) -> bool:
    """
    验证输入是否为有效的浮点数
    
    :param action: 操作类型
    :param value_if_allowed: 允许的值
    :return: 是否为有效的浮点数
    """
    if action == '1':  # insert
        if value_if_allowed == "":
            return True
        try:
            float(value_if_allowed)
            return True
        except ValueError:
            return False
    return True

def validate_int_input(action: str, value_if_allowed: str) -> bool:
    """
    验证输入是否为有效的整数
    
    :param action: 操作类型
    :param value_if_allowed: 允许的值
    :return: 是否为有效的整数
    """
    if action == '1':  # insert
        if value_if_allowed == "":
            return True
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False
    return True

def exception_handler(func):
    """
    装饰器：用于处理函数中的异常
    
    :param func: 被装饰的函数
    :return: 包装后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"在执行 {func.__name__} 时发生错误: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"发生错误: {str(e)}")
    return wrapper

def get_project_root() -> str:
    """
    获取项目根目录的路径
    
    :return: 项目根目录的路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(current_dir))