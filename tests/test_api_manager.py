import unittest
from src.api.api_manager import APIManager
from src.api.yahoo_finance_adapter import YahooFinanceAdapter
from src.api.alpha_vantage_adapter import AlphaVantageAdapter
from src.api.moomoo_adapter import MoomooAdapter

class TestAPIManager(unittest.TestCase):
    def setUp(self):
        self.api_manager = APIManager()
        self.api_manager.add_price_query_api('yahoo', YahooFinanceAdapter())
        self.api_manager.add_price_query_api('alpha_vantage', AlphaVantageAdapter('dummy_key'))
        self.api_manager.add_trading_api('moomoo', MoomooAdapter({'host': 'localhost', 'port': '11111'}))

    def test_get_stock_price_yahoo(self):
        price, source = self.api_manager.get_stock_price('yahoo', 'AAPL')
        self.assertIsInstance(price, float)
        self.assertEqual(source, 'Yahoo Finance')

    # 添加更多测试...

if __name__ == '__main__':
    unittest.main()