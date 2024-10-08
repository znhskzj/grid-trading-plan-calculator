# src/api/yahoo_finance_adapter.py

from typing import Tuple
import yfinance as yf
from src.utils.logger import setup_logger
from src.utils.error_handler import PriceQueryError
from .price_query_interface import PriceQueryInterface

logger = setup_logger('yahoo_finance')

class YahooFinanceAdapter(PriceQueryInterface):
    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        """
        获取股票价格
        
        :param symbol: 股票代码
        :return: (价格, API名称)
        :raises PriceQueryError: 如果无法获取价格数据
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                price = round(data['Close'].iloc[-1], 2)
                logger.info(f"Successfully retrieved price for {symbol}: {price}")
                return price, 'Yahoo Finance'
            else:
                raise PriceQueryError(f"Yahoo Finance 未返回 {symbol} 的数据")
        except Exception as e:
            logger.error(f"从Yahoo Finance获取价格时发生错误: {str(e)}")
            raise PriceQueryError(f"Yahoo Finance 无法获取 {symbol} 的价格: {str(e)}")