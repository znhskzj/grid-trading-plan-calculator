# src/utils/gui_helpers.py

def validate_float_input(action: str, value_if_allowed: str) -> bool:
        """验证输入是否为有效的浮点数"""
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
    """验证输入是否为有效的整数"""
    if action == '1':  # insert
        if value_if_allowed == "":
            return True
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False
    return True

# 添加其他辅助函数