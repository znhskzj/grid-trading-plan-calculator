# src/api/yahoo_finance_adapter.py

from typing import Tuple
import yfinance as yf
from time import time
from src.utils.logger import setup_logger
from src.utils.error_handler import PriceQueryError
from .price_query_interface import PriceQueryInterface

logger = setup_logger('yahoo_finance')

class YahooFinanceAdapter(PriceQueryInterface):
    def __init__(self):
        self._tickers = {}  # 缓存 Ticker 对象
        self._cache = {}    # 缓存价格数据
        self._cache_time = {}  # 缓存时间
        self._retry_count = {}  # 跟踪每个symbol的重试次数

    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        """
        获取股票价格
        
        Args:
            symbol: 股票代码
        Returns:
            Tuple[float, str]: (价格, API名称)
        Raises:
            PriceQueryError: 如果无法获取价格数据
        """
        logger.debug(f"开始从Yahoo Finance获取 {symbol} 的价格")
        
        # 初始化重试计数器
        if symbol not in self._retry_count:
            self._retry_count[symbol] = 0
        
        # 检查缓存
        if symbol in self._cache:
            cache_age = time() - self._cache_time[symbol]
            if cache_age < 60:  # 1分钟内的缓存有效
                logger.debug(f"使用缓存的价格数据: {symbol}")
                return self._cache[symbol], 'Yahoo Finance'

        try:
            # 更新状态消息
            status_message = "正在从Yahoo Finance获取最新价格，请稍候......"
            logger.info(status_message)
            
            # 获取或创建 Ticker
            if symbol not in self._tickers:
                self._tickers[symbol] = yf.Ticker(symbol)
            
            ticker = self._tickers[symbol]
            data = ticker.history(period="1d")
            
            if not data.empty:
                price = round(data['Close'].iloc[-1], 2)
                # 更新缓存
                self._cache[symbol] = price
                self._cache_time[symbol] = time()
                self._retry_count[symbol] = 0  # 重置重试计数
                logger.info(f"成功获取并缓存 {symbol} 的价格: {price}")
                return price, 'Yahoo Finance'
            else:
                retry_message = self._generate_retry_message(symbol)
                raise PriceQueryError(f"Yahoo Finance 未返回 {symbol} 的数据。{retry_message}")
        except Exception as e:
            self._retry_count[symbol] += 1
            retry_message = self._generate_retry_message(symbol)
            error_msg = f"Yahoo Finance 无法获取 {symbol} 的价格: {str(e)}\n{retry_message}"
            logger.error(f"从Yahoo Finance获取价格时发生错误: {str(e)}")
            raise PriceQueryError(error_msg)

    def _generate_retry_message(self, symbol: str) -> str:
        """生成重试建议消息"""
        retry_count = self._retry_count.get(symbol, 0)
        if retry_count == 0:
            return "请稍后再试一次，有时第一次查询可能不成功。"
        elif retry_count == 1:
            return "如果再次查询失败，建议稍等片刻后重试或切换到其他价格查询API（如Alpha Vantage）。"
        else:
            return "多次查询失败，建议切换到其他价格查询API或检查网络连接。"

    def close(self) -> None:
        """关闭连接"""
        self._tickers.clear()
        self._cache.clear()
        self._cache_time.clear()
        self._retry_count.clear()

    @property
    def name(self) -> str:
        """获取API名称"""
        return 'Yahoo Finance'