import unittest
import pandas as pd
from unittest.mock import patch
from src.api.yahoo_finance_adapter import YahooFinanceAdapter

class TestYahooFinanceAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = YahooFinanceAdapter()

    @patch('yfinance.Ticker')
    def test_get_stock_price(self, mock_ticker):
        mock_ticker.return_value.history.return_value = pd.DataFrame({'Close': [150.0]})
        price, source = self.adapter.get_stock_price('AAPL')
        self.assertEqual(price, 150.0)
        self.assertEqual(source, 'Yahoo Finance')

    # 添加更多测试...

if __name__ == '__main__':
    unittest.main()