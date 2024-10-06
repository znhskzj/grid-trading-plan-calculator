import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.api.moomoo_adapter import MoomooAdapter

class TestMoomooAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = MoomooAdapter({'host': 'localhost', 'port': '11111'})

    @patch('src.api.moomoo_adapter.OpenSecTradeContext')
    def test_get_account_info(self, mock_context):
        mock_context.return_value.__enter__.return_value.accinfo_query.return_value = (0, pd.DataFrame({'balance': [1000]}))
        result = self.adapter.get_account_info(acc_id=1, trade_env='SIMULATE', market='US')
        self.assertIsNotNone(result)
        self.assertEqual(result['balance'].values[0], 1000)

    # 添加更多测试...

if __name__ == '__main__':
    unittest.main()