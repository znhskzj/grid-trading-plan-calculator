# test_calculations.py

import pytest
import sys
import os
from unittest.mock import Mock, call, patch, ANY, MagicMock
import tkinter as tk
import yfinance as yf
from src.gui import App
from src.calculations import parse_trading_instruction, calculate_grid_from_instruction
from src.calculations import validate_inputs, calculate_weights, calculate_buy_plan
from src.calculations import run_calculation, calculate_with_reserve
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

def test_full_instruction_to_calculation_flow():
    instruction = "AAPL 150-160之间分批买入，止损145"
    parsed_instruction = parse_trading_instruction(instruction)
    result = calculate_grid_from_instruction(parsed_instruction, 50000, 5, 1)
    assert isinstance(result, str)
    assert "AAPL" in result
    assert any(f"{price:.2f}" in result for price in range(150, 161))  # 更灵活的检查
    assert "160.00" in result
    assert "145.00" in result
    assert "等比例分配" in result

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
            'API': {'choice': 'yahoo', 'alpha_vantage_key': ''},
            'General': {
                'funds': '50000.0',
                'initial_price': '100.0',
                'stop_loss_price': '90.0',
                'num_grids': '10',
                'allocation_method': '1'
            },
            'CommonStocks': {'stock1': 'AAPL', 'stock2': 'GOOGL'},
            'AvailableAPIs': {'apis': ['yahoo', 'alpha_vantage']},
            'MoomooSettings': {'trade_mode': 'simulate', 'market': 'US'},
            'RecentCalculations': []
        }
        
        mock_frame = MagicMock()
        mock_frame.winfo_children.return_value = []
        mock_frame._last_child_ids = {}
        
        # 修改：创建一个模拟的 Tk 实例
        mock_master = MockTk()
        
        with patch('src.gui.App.create_widgets', Mock()), \
             patch('src.gui.App.setup_layout', Mock()), \
             patch('src.gui.App.load_user_settings', Mock()):
            # 修改：传入模拟的 Tk 实例
            app = App(mock_master, mock_config, VERSION)
        
        # 修改：设置 master 属性
        app.master = mock_master
        
        app.left_frame = mock_frame
        app.right_frame = mock_frame
        app.common_stocks_button = MagicMock()
        app.common_stocks_frame = MagicMock()
        app.common_stocks_frame.winfo_children.return_value = []
        app.status_bar = MagicMock()
        app.result_text = MagicMock()
        app.funds_var = MockStringVar(value='50000.0')
        app.initial_price_var = MockStringVar(value='100.0')
        app.stop_loss_price_var = MockStringVar(value='90.0')
        app.num_grids_var = MockStringVar(value='10')
        app.allocation_method_var = MockStringVar(value='1')
        app.trade_mode_var = MockStringVar(value='simulate')
        app.market_var = MockStringVar(value='US')
        app.user_config = {'common_stocks': []}
        app.available_apis = ['yahoo', 'alpha_vantage']
        app.instruction_var = MockStringVar(value='')
        app.api_choice = MockStringVar(value='yahoo')
        app.alpha_vantage_key = MockStringVar(value='')
        
        return app

def test_set_stock_price(mock_app):
    with patch('src.api_manager.APIManager.get_stock_price') as mock_get_price:
        mock_get_price.return_value = (150.0, 'Yahoo Finance')
        mock_app.set_stock_price('AAPL')
        assert mock_app.initial_price_var.get() == '150.00'
        mock_app.status_bar.config.assert_called()
        assert any("已选择标的 AAPL" in str(call) for call in mock_app.status_bar.config.call_args_list)

    mock_get_price.side_effect = ValueError("无法获取股票价格")
    mock_app.set_stock_price('INVALID')
    mock_app.status_bar.config.assert_called()
    assert any("INVALID" in str(call) and "价格" in str(call) for call in mock_app.status_bar.config.call_args_list)

def test_run_calculation_combined(mock_app):
    with patch('src.calculations.run_calculation', return_value="模拟计算结果"):
        # 测试无指令情况
        mock_app.instruction_var.set('')
        mock_app.run_calculation()
        mock_app.status_bar.config.assert_called()
        assert any("开始计算购买计划" in str(call) for call in mock_app.status_bar.config.call_args_list)
        mock_app.result_text.delete.assert_called()
        mock_app.result_text.insert.assert_called()
        
        # 测试有指令情况
        mock_app.instruction_var.set("AAPL 现价150区间买入，止损145")
        mock_app.run_calculation()
        assert any("开始计算购买计划" in str(call) for call in mock_app.status_bar.config.call_args_list)
        mock_app.result_text.delete.assert_called()
        mock_app.result_text.insert.assert_called()

def test_calculate_with_reserve_combined(mock_app):
    with patch('src.calculations.calculate_with_reserve', return_value="模拟保留资金计算结果"):
        # 测试无指令情况
        mock_app.instruction_var.set('')
        mock_app.calculate_with_reserve(10)
        mock_app.status_bar.config.assert_called()
        assert any("开始计算（保留10%资金）" in str(call) for call in mock_app.status_bar.config.call_args_list)
        mock_app.result_text.delete.assert_called()
        mock_app.result_text.insert.assert_called()
        
        # 测试有指令情况
        mock_app.instruction_var.set("TSLA 230-240之间建仓，止损220")
        mock_app.calculate_with_reserve(20)
        assert any("开始计算（保留20%资金）" in str(call) for call in mock_app.status_bar.config.call_args_list)
        mock_app.result_text.delete.assert_called()
        mock_app.result_text.insert.assert_called()

def test_moomoo_settings(mock_app):
    assert mock_app.trade_mode_var.get() == 'simulate'
    assert mock_app.market_var.get() == 'US'
    
    mock_app.trade_mode_var.set('real')
    mock_app.market_var.set('HK')
    
    assert mock_app.trade_mode_var.get() == 'real'
    assert mock_app.market_var.get() == 'HK'

def test_test_moomoo_connection(mock_app):
    # 模拟 connection_test 方法
    def mock_connection_test(env_str, market_str):
        success_message = f"Moomoo API 连接成功！\n已连接到{market_str}{env_str}账户。"
        mock_app.display_results(success_message)
        mock_app.update_status(f"Moomoo API 已连接 - {market_str}{env_str}账户")

    # 替换原始的 connection_test 方法
    mock_app.connection_test = mock_connection_test

    # 调用被测试的方法
    mock_app.test_moomoo_connection()

    # 验证 display_results 和 update_status 被调用
    mock_app.display_results.assert_called_once()
    mock_app.update_status.assert_called()

    # 重置 mock
    mock_app.display_results.reset_mock()
    mock_app.update_status.reset_mock()

    # 模拟连接失败的情况
    def mock_failed_connection_test(env_str, market_str):
        error_message = f"Moomoo API 连接失败！\n无法连接到{market_str}{env_str}账户，请检查以下内容：\n1. Moomoo OpenD网关是否已启动\n2. 网络连接是否正常\n3. API设置是否正确"
        mock_app.display_results(error_message)
        mock_app.update_status("Moomoo API 连接失败")

    # 替换为失败的连接测试
    mock_app.connection_test = mock_failed_connection_test

    # 再次调用被测试的方法
    mock_app.test_moomoo_connection()

    # 验证 display_results 和 update_status 被再次调用
    mock_app.display_results.assert_called_once()
    mock_app.update_status.assert_called()

def test_reset_to_default(mock_app):
    # 修改: 模拟系统配置
    mock_app.system_config = {
        'General': {
            'default_funds': '10000',
            'default_initial_price': '100',
            'default_stop_loss_price': '90',
            'default_num_grids': '5',
            'default_allocation_method': '1'
        }
    }
    
    # 修改: 保存原始的常用股票和Moomoo设置
    original_common_stocks = mock_app.user_config.get('CommonStocks', {})
    original_moomoo_settings = mock_app.user_config.get('MoomooSettings', {})
    
    mock_app.reset_to_default()
    
    # 验证API选择
    assert mock_app.api_choice.get() == 'yahoo'
    
    # 修改: 验证资金和网格设置使用系统配置的默认值
    assert mock_app.funds_var.get() == mock_app.system_config['General']['default_funds']
    assert mock_app.initial_price_var.get() == mock_app.system_config['General']['default_initial_price']
    assert mock_app.stop_loss_price_var.get() == mock_app.system_config['General']['default_stop_loss_price']
    assert mock_app.num_grids_var.get() == mock_app.system_config['General']['default_num_grids']
    assert mock_app.allocation_method_var.get() == mock_app.system_config['General']['default_allocation_method']
    
    # 验证Moomoo设置保持不变
    assert mock_app.trade_mode_var.get() == original_moomoo_settings.get('trade_mode', '模拟')
    assert mock_app.market_var.get() == original_moomoo_settings.get('market', '港股')
    
    # 验证常用股票保持不变
    assert mock_app.user_config.get('CommonStocks') == original_common_stocks

    # 验证其他设置被重置
    assert mock_app.current_symbol is None
    assert mock_app.instruction_var.get() == ""

def test_save_user_settings(mock_app):
    # 修改: 使用 patch 来模拟 save_user_config 函数
    with patch('src.config.save_user_config') as mock_save_config:
        # 调用被测试的方法
        mock_app.save_user_settings()
        
        # 验证 save_user_config 被调用一次
        mock_save_config.assert_called_once()
        
        # 新增: 验证 save_user_config 被调用时传入了正确的参数
        mock_save_config.assert_called_with(mock_app.user_config)
    
    # 新增: 验证 update_status 方法被调用
    mock_app.update_status.assert_called_once_with("用户设置已保存")

    # 新增: 如果 App 类中有 is_closing 属性，验证它没有被设置为 True
    if hasattr(mock_app, 'is_closing'):
        assert not mock_app.is_closing, "is_closing should not be True after saving settings"

def test_load_user_settings(mock_app):
    # 修改: 创建一个模拟的用户配置
    mock_user_config = {
        'API': {'choice': 'alpha_vantage', 'alpha_vantage_key': 'test_key'},
        'General': {'allocation_method': '2', 'funds': '100000'},
        'MoomooSettings': {'trade_mode': 'real', 'market': 'HK'},
        'RecentCalculations': {
            'funds': '100000',
            'initial_price': '200',
            'stop_loss_price': '180',
            'num_grids': '8'
        }
    }

    # 使用 patch 来模拟 load_user_config 函数
    with patch('src.config.load_user_config', return_value=mock_user_config):
        # 调用被测试的方法
        mock_app.load_user_settings()
        
        # 验证 API 设置
        assert mock_app.api_choice.get() == 'alpha_vantage'
        assert mock_app.alpha_vantage_key.get() == 'test_key'
        
        # 验证常规设置
        assert mock_app.allocation_method_var.get() == '2'
        assert mock_app.funds_var.get() == '100000'
        
        # 验证 Moomoo 设置
        assert mock_app.trade_mode_var.get() == 'real'
        assert mock_app.market_var.get() == 'HK'
        
        # 验证最近的计算设置
        assert mock_app.initial_price_var.get() == '200'
        assert mock_app.stop_loss_price_var.get() == '180'
        assert mock_app.num_grids_var.get() == '8'

    # 验证 update_status 方法被调用
    mock_app.update_status.assert_called_once_with("用户设置已加载")

    # 如果 App 类中实现了 update_ui_from_config 方法，验证它被调用
    if hasattr(mock_app, 'update_ui_from_config'):
        mock_app.update_ui_from_config.assert_called_once()

def test_integration_flow(mock_app):
    # 模拟完整的用户操作流程
    with patch('src.api_manager.APIManager.get_stock_price', return_value=(150.0, 'Yahoo Finance')), \
         patch('src.calculations.run_calculation', return_value="模拟计算结果"), \
         patch('src.calculations.calculate_with_reserve', return_value="模拟保留资金计算结果"):
        
        # 设置股票价格
        mock_app.set_stock_price('AAPL')
        assert mock_app.initial_price_var.get() == '150.00'
        
        # 输入交易指令
        mock_app.instruction_var.set("AAPL 145-155之间分批买入，止损140")
        
        # 运行计算
        mock_app.run_calculation()
        mock_app.status_bar.config.assert_called()
        assert any("计算完成" in str(call) for call in mock_app.status_bar.config.call_args_list)
        
        # 使用保留资金计算
        mock_app.calculate_with_reserve(10)
        assert any("计算完成（保留10%资金）" in str(call) for call in mock_app.status_bar.config.call_args_list)
        
        # 检查结果显示
        mock_app.result_text.delete.assert_called()
        mock_app.result_text.insert.assert_called()

def test_api_switch(mock_app):
    # 修改: 确保 api_choice 是 MockStringVar 实例
    mock_app.api_choice = MockStringVar(value='yahoo')
    
    # 修改: 模拟 on_api_change 方法
    mock_app.on_api_change = lambda: None
    
    # 验证初始 API 选择
    assert mock_app.api_choice.get() == 'yahoo'
    
    # 修改: 模拟 API 切换
    mock_app.api_choice.set('alpha_vantage')
    
    # 验证 API 选择已更改
    assert mock_app.api_choice.get() == 'alpha_vantage'
    
    # 修改: 使用 patch 来模拟 tkinter.messagebox.showinfo
    with patch('tkinter.messagebox.showinfo') as mock_showinfo:
        # 调用 on_api_change 方法（如果存在）
        if hasattr(mock_app, 'on_api_change'):
            mock_app.on_api_change()
            
            # 验证 showinfo 被调用
            mock_showinfo.assert_called_once()
            
            # 验证 showinfo 调用的参数
            expected_call = call("API 更改", "API 已更改为 alpha_vantage")
            assert mock_showinfo.call_args == expected_call
    
    # 修改: 验证 update_status 方法被调用
    mock_app.update_status.assert_called_with("API 已切换到 alpha_vantage")
    
    # 修改: 如果存在 initialize_api_manager 方法，验证它被调用
    if hasattr(mock_app, 'initialize_api_manager'):
        mock_app.initialize_api_manager.assert_called_once()

def test_common_stocks_update(mock_app):
    # 修改: 创建一个新的常用股票字典
    new_stocks = {'AAPL': 'Apple Inc.', 'GOOGL': 'Alphabet Inc.', 'MSFT': 'Microsoft Corporation'}
    
    # 修改: 确保 common_stocks_frame 是 MagicMock 实例
    mock_app.common_stocks_frame = MagicMock()
    mock_app.common_stocks_frame.winfo_children.return_value = []
    
    # 修改: 模拟 create_common_stock_button 方法
    mock_app.create_common_stock_button = MagicMock()
    
    # 调用被测试的方法
    mock_app.update_common_stocks(new_stocks)
    
    # 验证 common_stocks_frame 的子部件被清除
    mock_app.common_stocks_frame.winfo_children.assert_called_once()
    for child in mock_app.common_stocks_frame.winfo_children():
        child.destroy.assert_called_once()
    
    # 验证为每个新的股票创建了按钮
    expected_calls = [call(symbol, name) for symbol, name in new_stocks.items()]
    mock_app.create_common_stock_button.assert_has_calls(expected_calls, any_order=True)
    assert mock_app.create_common_stock_button.call_count == len(new_stocks)
    
    # 验证 common_stocks_frame 被更新
    mock_app.common_stocks_frame.update.assert_called_once()
    
    # 验证 user_config 被更新
    assert mock_app.user_config.get('CommonStocks') == new_stocks
    
    # 验证 update_status 方法被调用
    mock_app.update_status.assert_called_once_with("常用股票已更新")
    
    # 如果存在 save_user_settings 方法，验证它被调用
    if hasattr(mock_app, 'save_user_settings'):
        mock_app.save_user_settings.assert_called_once()

if __name__ == "__main__":
    pytest.main()