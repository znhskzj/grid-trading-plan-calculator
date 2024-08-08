# src/api_manager.py

import yfinance as yf
import requests
import logging

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self, api_choice='yahoo', alpha_vantage_key=None):
        self.api_choice = api_choice
        self.alpha_vantage_key = alpha_vantage_key

    def get_stock_price(self, symbol):
        if self.api_choice == 'yahoo':
            return self._get_yahoo_price(symbol)
        elif self.api_choice == 'alpha_vantage':
            return self._get_alpha_vantage_price(symbol)
        else:
            raise ValueError("Invalid API choice")

    def _get_yahoo_price(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            price = stock.info.get('regularMarketPrice') or stock.info.get('currentPrice')
            if price is None:
                raise ValueError(f"无法获取 {symbol} 的价格")
            return price, "Yahoo Finance"
        except Exception as e:
            logger.error(f"从Yahoo Finance获取价格时发生错误: {str(e)}")
            raise

    def _get_alpha_vantage_price(self, symbol):
        try:
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}'
            response = requests.get(url)
            response.raise_for_status()  # 如果请求失败，这将引发异常
            data = response.json()
            if 'Global Quote' not in data or '05. price' not in data['Global Quote']:
                raise ValueError(f"无法获取 {symbol} 的价格数据")
            return float(data['Global Quote']['05. price']), "Alpha Vantage"
        except requests.RequestException as e:
            logger.error(f"从Alpha Vantage获取价格时发生网络错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"从Alpha Vantage获取价格时发生错误: {str(e)}")
            raise