# test_calculations.py

import pytest
import sys
import os
from unittest.mock import Mock, patch, ANY, MagicMock
import tkinter as tk
from src.gui import App
from src.calculations import parse_trading_instruction, calculate_grid_from_instruction
from src.calculations import validate_inputs, calculate_weights, calculate_buy_plan
from version import VERSION

# 模拟 tkinter
sys.modules['tkinter'] = Mock()


class MockStringVar:
    def __init__(self, value=''):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


tk.Tk = Mock()
tk.Frame = Mock()
tk.Label = Mock()
tk.Button = Mock()
tk.StringVar = MockStringVar


class MockTk:
    def __init__(self, screenName=None, baseName=None, className='Tk', useTk=True, sync=False, use=None):
        self.title = Mock()
        self._last_child_ids = {}
        self.tk = Mock()
        self.tk.call = Mock(return_value="")
        self.children = {}
    
    def __getattr__(self, name):
        return Mock()

    def _options(self, *args, **kwargs):
        return {}

    def winfo_children(self):
        return list(self.children.values())


class MockStatusManager:
    @staticmethod
    def set_instance(instance):
        pass

    @staticmethod
    def update_status(message):
        pass


sys.modules['tkinter'].Tk = MockTk
sys.modules['tkinter'].StringVar = MockStringVar
sys.modules['tkinter'].messagebox = Mock()

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_validate_inputs():
    # 测试有效输入
    validate_inputs(50000, 100, 90, 10, 0)

    # 测试无效输入
    with pytest.raises(ValueError):
        validate_inputs(-1000, 100, 90, 10, 0)  # 负资金
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 110, 10, 0)  # 止损价高于初始价
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 90, 101, 0)  # 网格数量过多


def test_calculate_weights():
    prices = [100, 95, 90, 85, 80]

    # 测试等金额分配
    weights_equal = calculate_weights(prices, 0, 100)
    assert len(weights_equal) == len(prices)
    assert all(w > 0 for w in weights_equal)

    # 测试指数分配
    weights_exp = calculate_weights(prices, 1, 100)
    assert len(weights_exp) == len(prices)
    assert all(w > 0 for w in weights_exp)
    assert weights_exp[-1] > weights_exp[0]  # 最低价格应该有最高权重

    # 测试线性分配
    weights_linear = calculate_weights(prices, 2, 100)
    assert len(weights_linear) == len(prices)
    assert all(w > 0 for w in weights_linear)
    assert weights_linear[-1] > weights_linear[0]  # 最低价格应该有最高权重


def test_calculate_buy_plan():
    funds = 50000
    initial_price = 100
    stop_loss_price = 90
    num_grids = 10
    allocation_method = 0

    buy_plan, warning = calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids, allocation_method)

    assert len(buy_plan) == num_grids
    assert all(price >= stop_loss_price and price <= initial_price for price, _ in buy_plan)
    assert all(quantity > 0 for _, quantity in buy_plan)
    assert sum(price * quantity for price, quantity in buy_plan) <= funds


def test_validate_inputs_edge_cases():
    # 测试边界值
    validate_inputs(1, 1, 0.1, 2, 0)  # 最小可能的有效输入

    # 测试更多无效输入
    with pytest.raises(ValueError):
        validate_inputs(50000, 0, 90, 10, 0)  # 初始价格为0
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 0, 10, 0)  # 止损价格为0
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 90, 0, 0)  # 网格数量为0
    with pytest.raises(ValueError):
        validate_inputs(50000, 100, 90, 10, 3)  # 无效的分配方式


def test_calculate_weights_edge_cases():
    # 测试单一价格
    assert calculate_weights([100], 0, 100) == [100]
    assert calculate_weights([100], 1, 100) == [100]
    assert calculate_weights([100], 2, 100) == [100]

    # 测试极端价格差
    prices_extreme = [1000, 1]
    weights_extreme = calculate_weights(prices_extreme, 1, 100)
    assert weights_extreme[1] > weights_extreme[0] * 10  # 确保最低价格的权重显著更高

    # 测试大量价格点
    prices_many = list(range(1, 101))  # 100个价格点
    weights_many = calculate_weights(prices_many, 2, 1000)
    assert len(weights_many) == 100
    assert weights_many[-1] == max(weights_many)  # 最低价格应有最高权重


def test_calculate_buy_plan_different_allocations():
    funds = 50000
    initial_price = 100
    stop_loss_price = 90
    num_grids = 10

    # 测试不同的分配方式
    for allocation_method in [0, 1, 2]:
        buy_plan, warning = calculate_buy_plan(funds, initial_price, stop_loss_price, num_grids, allocation_method)
        assert len(buy_plan) == num_grids
        assert all(price >= stop_loss_price and price <= initial_price for price, _ in buy_plan)
        assert all(quantity > 0 for _, quantity in buy_plan)
        assert sum(price * quantity for price, quantity in buy_plan) <= funds


def test_calculate_buy_plan_edge_cases():
    # 测试极小资金
    buy_plan, warning = calculate_buy_plan(100, 10, 9, 5, 0)
    assert len(buy_plan) == 5
    assert sum(quantity for _, quantity in buy_plan) >= 10  # 至少应该买10股

    # 测试极大网格数
    buy_plan, warning = calculate_buy_plan(1000000, 100, 50, 100, 1)
    assert len(buy_plan) == 100

    # 测试初始价格和止损价格非常接近的情况
    buy_plan, warning = calculate_buy_plan(10000, 100, 99.9, 10, 2)
    assert len(buy_plan) == 10
    assert all(99.9 <= price <= 100 for price, _ in buy_plan)


def test_calculate_buy_plan_warnings():
    # 测试可能触发警告的情况
    _, warning = calculate_buy_plan(1000, 100, 90, 20, 0)
    assert "警告" in warning  # 资金可能不足以合理分配到所有网格

    _, warning = calculate_buy_plan(1000000, 100, 90, 2, 0)
    assert warning == ""  # 不应该有警告


@pytest.fixture
def mock_app():
    with patch('tkinter.Tk', MockTk), \
         patch('src.gui.StatusManager', MockStatusManager), \
         patch('tkinter.messagebox.showerror', Mock()), \
         patch('tkinter.Frame', MagicMock), \
         patch('tkinter.Label', MagicMock), \
         patch('tkinter.Entry', MagicMock), \
         patch('tkinter.Button', MagicMock), \
         patch('tkinter.Radiobutton', MagicMock):
        
        mock_config = {
            'General': {
                'funds': '50000.0',
                'initial_price': '100.0',
                'stop_loss_price': '90.0',
                'num_grids': '10',
                'allocation_method': '1'
            },
            'CommonStocks': {'stock1': 'AAPL', 'stock2': 'GOOGL'},
            'AvailableAPIs': {'apis': ['yahoo', 'alpha_vantage']},
            'API': {'choice': 'yahoo', 'alpha_vantage_key': ''}
        }
        
        # 创建一个模拟的 Frame 对象
        mock_frame = MagicMock()
        mock_frame.winfo_children.return_value = []
        mock_frame._last_child_ids = {}
        
        with patch('src.gui.App.create_widgets', Mock()), \
             patch('src.gui.App.setup_layout', Mock()), \
             patch('src.gui.App.load_user_settings', Mock()):
            app = App(None, mock_config, VERSION)
        
        # 手动设置一些属性
        app.left_frame = mock_frame
        app.right_frame = mock_frame
        app.common_stocks_button = MagicMock()
        app.status_bar = MagicMock()
        app.result_text = MagicMock()
        app.funds_var = MockStringVar(value='50000.0')
        app.initial_price_var = MockStringVar(value='100.0')
        app.stop_loss_price_var = MockStringVar(value='90.0')
        app.num_grids_var = MockStringVar(value='10')
        app.allocation_method_var = MockStringVar(value='1')
        app.user_config = {'common_stocks': []}
        
        return app

def test_set_stock_price(mock_app):
    with patch('yfinance.Ticker') as mock_yf:
        mock_yf.return_value.info = {'regularMarketPrice': 150.0}
        mock_app.set_stock_price('AAPL')
        assert mock_app.initial_price_var.get() == '150.0'
        mock_app.status_bar.config.assert_called()
        assert any("已选择标的 AAPL" in str(call) for call in mock_app.status_bar.config.call_args_list)

        mock_yf.return_value.info = {}
        mock_app.set_stock_price('INVALID')
        mock_app.status_bar.config.assert_called()
        assert any("无法获取股票 INVALID 的价格" in str(call) for call in mock_app.status_bar.config.call_args_list)

def test_run_calculation(mock_app):
    with patch('src.calculations.run_calculation', return_value="模拟计算结果"):
        mock_app.run_calculation()
        mock_app.status_bar.config.assert_called()
        assert any("开始计算购买计划" in str(call) for call in mock_app.status_bar.config.call_args_list)
        mock_app.result_text.delete.assert_called()
        mock_app.result_text.insert.assert_called()
        assert any("计算完成" in str(call) for call in mock_app.status_bar.config.call_args_list)

# in test_calculations.py

def test_show_common_stocks(mock_app):
    mock_app.config = {'CommonStocks': {'stock1': 'AAPL', 'stock2': 'GOOGL'}}
    mock_app.common_stocks_button = MagicMock()
    mock_app.common_stocks_button.__getitem__.return_value = "常用标的"
    mock_app.left_frame = MagicMock()
    mock_app.left_frame.winfo_children.return_value = [mock_app.common_stocks_button]
    
    mock_app.show_common_stocks()
    
    # 检查是否尝试更新按钮文本
    mock_app.common_stocks_button.__setitem__.assert_called_with('text', "隐藏常用标的")
    
    # 检查是否尝试创建新的按钮
    assert mock_app.left_frame.winfo_children.called
    assert mock_app.left_frame.update.called

    # 检查是否尝试获取 CommonStocks 配置
    assert mock_app.config['CommonStocks'] == {'stock1': 'AAPL', 'stock2': 'GOOGL'}

def test_placeholder_methods(mock_app):
    methods = [
        mock_app.enable_real_time_notifications,
        mock_app.query_available_funds,
        mock_app.place_order_by_plan,
        mock_app.export_transaction_details,
        mock_app.calculate_total_profit
    ]
    for method in methods:
        method()
        mock_app.status_bar.config.assert_called()
        assert any("尚未实现" in str(call) for call in mock_app.status_bar.config.call_args_list)

def test_parse_trading_instruction():
    # 测试基本指令解析
    instruction = "日内SOXL 现价到30之间分批入，压力31.5，止损29.5"
    result = parse_trading_instruction(instruction)
    assert result['symbol'] == 'SOXL'
    assert result['current_price'] == 30.0
    assert result['stop_loss'] == 29.5
    assert result['resistance'] == 31.5

    # 测试没有止损价的指令
    instruction = "AAPL 现价150区间买入"
    result = parse_trading_instruction(instruction)
    assert result['symbol'] == 'AAPL'
    assert result['current_price'] == 150.0
    assert result['stop_loss'] is not None  # 应该自动设置一个止损价

    # 测试价格区间指令
    instruction = "TSLA 230-240之间建仓"
    result = parse_trading_instruction(instruction)
    assert result['symbol'] == 'TSLA'
    assert result['price_range'] == (230.0, 240.0)

    # 测试带有API价格的指令解析
    instruction = "GOOGL 2800附近买入"
    result = parse_trading_instruction(instruction, current_api_price=3500) 
    assert 'price_warning' in result

def test_calculate_grid_from_instruction():
    instruction = "日内SOXL 现价到30之间分批入，压力31.5，止损29.5"
    parsed_instruction = parse_trading_instruction(instruction)
    result = calculate_grid_from_instruction(parsed_instruction, 50000, 10, 1)
    assert isinstance(result, str)
    assert "SOXL" in result
    assert "30.0" in result
    assert "29.5" in result

def test_validate_inputs_with_instruction():
    instruction = "AAPL 现价150区间买入，止损145"
    parsed_instruction = parse_trading_instruction(instruction)
    with pytest.raises(ValueError, match="总资金必须大于初始价格"):
        calculate_grid_from_instruction(parsed_instruction, 100, 10, 0)

def test_calculate_weights_with_instruction():
    instruction = "TSLA 230-240之间建仓，止损220"
    parsed_instruction = parse_trading_instruction(instruction)
    result = calculate_grid_from_instruction(parsed_instruction, 50000, 5, 2)
    assert isinstance(result, str)
    assert "线性加权分配" in result

def test_edge_cases_with_instruction():
    # 测试极小价格区间
    instruction = "XYZ 100-100.1之间买入"
    parsed_instruction = parse_trading_instruction(instruction)
    result = calculate_grid_from_instruction(parsed_instruction, 10000, 5, 0)
    assert isinstance(result, str)
    assert "100.0" in result and "100.1" in result

    # 测试大资金小价格
    instruction = "PENNY 1-2元区间买入"
    parsed_instruction = parse_trading_instruction(instruction)
    result = calculate_grid_from_instruction(parsed_instruction, 1000000, 10, 1)
    assert isinstance(result, str)
    assert "大量股票" in result or "高数量" in result

def test_invalid_instructions():
    invalid_instructions = [
        "买入 AAPL",  
        "XYZ 100到90之间买入",  
        "ABC 现价到stop之间买入",  
    ]
    for instruction in invalid_instructions:
        with pytest.raises(ValueError):
            parse_trading_instruction(instruction)

def test_price_tolerance_warning():
    instruction = "GOOG 2800附近买入"
    result = parse_trading_instruction(instruction, current_api_price=3500)  # 增加价格差异
    assert 'price_warning' in result

if __name__ == "__main__":
    pytest.main()