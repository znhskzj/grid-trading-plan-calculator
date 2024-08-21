# src/api_manager.py

from typing import Tuple, Optional
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class APIError(Exception):
    pass

class YahooFinanceAPI:
    @staticmethod
    def get_stock_price(symbol: str) -> Tuple[float, str]:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                price = round(data['Close'].iloc[-1], 2)
                return price, 'Yahoo Finance'
            else:
                raise APIError(f"Yahoo Finance 未返回 {symbol} 的数据")
        except Exception as e:
            logger.error(f"从Yahoo Finance获取价格时发生错误: {str(e)}")
            raise APIError(f"Yahoo Finance 无法获取 {symbol} 的价格: {str(e)}")

class AlphaVantageAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ts = None

    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        try:
            ts = self._get_alpha_vantage_ts()
            data, _ = ts.get_quote_endpoint(symbol)
            if data and '05. price' in data:
                return float(data['05. price']), 'Alpha Vantage'
            else:
                raise APIError(f"Alpha Vantage 未返回 {symbol} 的有效价格数据")
        except Exception as e:
            error_msg = str(e)
            if "Thank you for using Alpha Vantage!" in error_msg:
                error_msg = "已达到 Alpha Vantage API 的每日请求限制。请稍后再试或切换到其他 API。"
            logger.error(f"从Alpha Vantage获取价格时发生错误: {error_msg}")
            raise APIError(f"无法获取 {symbol} 的价格: {error_msg}")

    def _get_alpha_vantage_ts(self) -> TimeSeries:
        if self.ts is None:
            try:
                self.ts = TimeSeries(key=self.api_key)
            except ImportError:
                logger.error("无法导入 alpha_vantage 库。请确保已安装该库。")
                raise ImportError("alpha_vantage 库未安装。请使用 'pip install alpha_vantage' 安装。")
        return self.ts

class APIManager:
    def __init__(self, api_choice: str, alpha_vantage_key: str):
        self.api_choice = api_choice
        self.alpha_vantage_api = AlphaVantageAPI(alpha_vantage_key)
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)

    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        cached_result = self._get_cached_price(symbol)
        if cached_result:
            return cached_result

        if self.api_choice == 'yahoo':
            result = YahooFinanceAPI.get_stock_price(symbol)
        elif self.api_choice == 'alpha_vantage':
            result = self.alpha_vantage_api.get_stock_price(symbol)
        else:
            raise ValueError(f"不支持的 API: {self.api_choice}")

        self._cache_price(symbol, result)
        return result

    def _get_cached_price(self, symbol: str) -> Optional[Tuple[float, str]]:
        if symbol in self.cache:
            timestamp, price, source = self.cache[symbol]
            if datetime.now() - timestamp < self.cache_duration:
                return price, source
        return None

    def _cache_price(self, symbol: str, result: Tuple[float, str]):
        self.cache[symbol] = (datetime.now(), *result)