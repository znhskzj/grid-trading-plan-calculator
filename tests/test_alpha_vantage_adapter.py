import unittest
from unittest.mock import patch, MagicMock
from src.api.alpha_vantage_adapter import AlphaVantageAdapter

class TestAlphaVantageAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = AlphaVantageAdapter('dummy_key')

    @patch('src.api.alpha_vantage_adapter.TimeSeries')
    def test_get_stock_price(self, mock_timeseries):
        mock_timeseries.return_value.get_quote_endpoint.return_value = ({'05. price': '160.0'}, None)
        price, source = self.adapter.get_stock_price('AAPL')
        self.assertEqual(price, 160.0)
        self.assertEqual(source, 'Alpha Vantage')

    # 添加更多测试...

if __name__ == '__main__':
    unittest.main()