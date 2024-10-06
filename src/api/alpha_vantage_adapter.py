from typing import Tuple
from alpha_vantage.timeseries import TimeSeries
from .price_query_interface import PriceQueryInterface
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    pass

class AlphaVantageAdapter(PriceQueryInterface):
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
                logger.error(f"Alpha Vantage 未返回 {symbol} 的有效价格数据")
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