import logging
from functools import wraps

# 创建一个模块级的 logger
logger = logging.getLogger(__name__)


def exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True, extra={'config_module': func.__module__})
            raise
    return wrapper
