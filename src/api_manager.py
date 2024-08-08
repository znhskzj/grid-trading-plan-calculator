# src/api_manager.py

import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import logging

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self, api_choice, alpha_vantage_key):
        self.api_choice = api_choice
        self.alpha_vantage_key = alpha_vantage_key
        self.alpha_vantage_ts = None

    def get_stock_price(self, symbol):
        if self.api_choice == 'yahoo':
            return self._get_yahoo_price(symbol)
        elif self.api_choice == 'alpha_vantage':
            return self._get_alpha_vantage_price(symbol)
        else:
            raise ValueError(f"不支持的 API: {self.api_choice}")

    def _get_yahoo_price(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                price = round(data['Close'].iloc[-1], 2)  # 四舍五入到两位小数
                return price, 'Yahoo Finance'
            else:
                raise ValueError(f"Yahoo Finance 未返回 {symbol} 的数据")
        except Exception as e:
            logger.error(f"从Yahoo Finance获取价格时发生错误: {str(e)}")
            raise ValueError(f"Yahoo Finance 无法获取 {symbol} 的价格: {str(e)}")

    def _get_alpha_vantage_price(self, symbol):
        try:
            ts = self._get_alpha_vantage_ts()
            data, _ = ts.get_quote_endpoint(symbol)
            if data and '05. price' in data:
                return float(data['05. price']), 'Alpha Vantage'
            else:
                raise ValueError(f"Alpha Vantage 未返回 {symbol} 的有效价格数据")
        except Exception as e:
            error_msg = str(e)
            if "Thank you for using Alpha Vantage!" in error_msg:
                error_msg = "已达到 Alpha Vantage API 的每日请求限制。请稍后再试或切换到其他 API。"
            logger.error(f"从Alpha Vantage获取价格时发生错误: {error_msg}")
            raise AlphaVantageError(f"无法获取 {symbol} 的价格: {error_msg}")

    def _get_alpha_vantage_ts(self):
        if self.alpha_vantage_ts is None:
            try:
                from alpha_vantage.timeseries import TimeSeries
                self.alpha_vantage_ts = TimeSeries(key=self.alpha_vantage_key)
            except ImportError:
                logger.error("无法导入 alpha_vantage 库。请确保已安装该库。")
                raise ImportError("alpha_vantage 库未安装。请使用 'pip install alpha_vantage' 安装。")
        return self.alpha_vantage_ts


class AlphaVantageError(Exception):
    pass
