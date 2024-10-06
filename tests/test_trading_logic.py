# -*- coding: utf-8 -*-
# tests/test_trading_logic.py

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.trading_logic import TradingLogic
from tests.test_data import SAMPLE_INSTRUCTIONS, SAMPLE_BUY_PLAN_INPUTS, get_trading_logic_instance

@pytest.fixture
def trading_logic():
    return get_trading_logic_instance()

@pytest.mark.parametrize("input_data", SAMPLE_BUY_PLAN_INPUTS)
def test_calculate_buy_plan(trading_logic, input_data):
    buy_plan, warning = trading_logic.calculate_buy_plan(**input_data)
    print(f"Test calculate_buy_plan: {buy_plan}")
    assert isinstance(buy_plan, list)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in buy_plan)
    # 添加更多断言...

@pytest.mark.parametrize("instruction", SAMPLE_INSTRUCTIONS)
def test_parse_trading_instruction(trading_logic, instruction):
    parsed = trading_logic.parse_trading_instruction(instruction)
    assert isinstance(parsed, dict)
    assert 'symbol' in parsed
    assert 'current_price' in parsed
    # 添加更多断言...