# src/api/alpha_vantage_adapter.py

from typing import Tuple
from alpha_vantage.timeseries import TimeSeries
from src.utils.logger import setup_logger
from src.utils.error_handler import PriceQueryError
from .price_query_interface import PriceQueryInterface

logger = setup_logger('alpha_vantage')

class AlphaVantageAdapter(PriceQueryInterface):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ts = None

    def get_stock_price(self, symbol: str) -> Tuple[float, str]:
        """
        获取股票价格
        
        :param symbol: 股票代码
        :return: (价格, API名称)
        :raises PriceQueryError: 如果无法获取价格数据
        """
        try:
            ts = self._get_alpha_vantage_ts()
            data, _ = ts.get_quote_endpoint(symbol)
            if data and '05. price' in data:
                price = float(data['05. price'])
                logger.info(f"Successfully retrieved price for {symbol}: {price}")
                return price, 'Alpha Vantage'
            else:
                raise PriceQueryError(f"Alpha Vantage 未返回 {symbol} 的有效价格数据")
        except Exception as e:
            error_msg = str(e)
            if "Thank you for using Alpha Vantage!" in error_msg:
                error_msg = "已达到 Alpha Vantage API 的每日请求限制。请稍后再试或切换到其他 API。"
            logger.error(f"从Alpha Vantage获取价格时发生错误: {error_msg}")
            raise PriceQueryError(f"无法获取 {symbol} 的价格: {error_msg}")

    def _get_alpha_vantage_ts(self) -> TimeSeries:
        """
        获取或创建 Alpha Vantage TimeSeries 对象
        
        :return: TimeSeries 对象
        :raises ImportError: 如果 alpha_vantage 库未安装
        """
        if self.ts is None:
            try:
                self.ts = TimeSeries(key=self.api_key)
            except ImportError:
                logger.error("无法导入 alpha_vantage 库。请确保已安装该库。")
                raise ImportError("alpha_vantage 库未安装。请使用 'pip install alpha_vantage' 安装。")
        return self.ts