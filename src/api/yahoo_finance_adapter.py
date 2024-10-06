from typing import Tuple
import yfinance as yf
import logging
from .price_query_interface import PriceQueryInterface

logger = logging.getLogger(__name__)

class YahooFinanceAdapter(PriceQueryInterface):
    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                price = round(data['Close'].iloc[-1], 2)
                return price, 'Yahoo Finance'
            else:
                logger.error(f"Yahoo Finance 未返回 {symbol} 的数据")
                raise ValueError(f"Yahoo Finance 未返回 {symbol} 的数据")
        except Exception as e:
            logger.error(f"从Yahoo Finance获取价格时发生错误: {str(e)}")
            raise ValueError(f"Yahoo Finance 无法获取 {symbol} 的价格: {str(e)}")