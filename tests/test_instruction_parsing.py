# test_instruction_parsing.py

import pytest
from src.calculations import parse_trading_instruction

@pytest.mark.parametrize("instruction, expected", [
    ("日内SOXL 现价到30之间分批入，压力31.5，止损29.5", {
        "symbol": "SOXL",
        "current_price": 30.0,
        "stop_loss": 29.5,
        "price_range": (30.0, 30.0),
        "resistance": 31.5
    }),
    ("AAPL 现价150区间买入，止损145", {
        "symbol": "AAPL",
        "current_price": 150.0,
        "stop_loss": 145.0,
        "price_range": (150.0, 150.0),
        "resistance": None
    }),
    ("TSLA 230-240之间建仓，止损220", {
        "symbol": "TSLA",
        "current_price": 235.0,
        "stop_loss": 220.0,
        "price_range": (230.0, 240.0),
        "resistance": None
    }),
    ("GOOGL 2800附近买入，压力2900", {
        "symbol": "GOOGL",
        "current_price": 2800.0,
        "stop_loss": 2520.0,
        "price_range": (2772.0, 2828.0),
        "resistance": 2900.0
    }),
    ("OXY 日内区间56.4-57，我待会通知大家如何做财报", {
        "symbol": "OXY",
        "current_price": 56.7,
        "stop_loss": 51.03,
        "price_range": (56.4, 57.0),
        "resistance": None
    }),
])
def test_parse_trading_instruction(instruction, expected):
    result = parse_trading_instruction(instruction)
    
    # 修改: 增加断言的容差
    tolerance = 0.01
    
    for key, value in expected.items():
        if isinstance(value, float):
            assert abs(result[key] - value) < tolerance, f"Key {key}: expected {value}, got {result[key]}"
        elif isinstance(value, tuple):
            assert all(abs(a - b) < tolerance for a, b in zip(result[key], value)), f"Key {key}: expected {value}, got {result[key]}"
        else:
            assert result[key] == value, f"Key {key}: expected {value}, got {result[key]}"

    # 新增: 检查其他可能的键
    possible_keys = {"symbol", "current_price", "stop_loss", "price_range", "resistance"}
    assert set(result.keys()) == possible_keys, f"Unexpected keys in result: {set(result.keys()) - possible_keys}"

def test_parse_trading_instruction_with_api_price():
    instruction = "GOOGL 2800附近买入"
    result = parse_trading_instruction(instruction, current_api_price=3500)
    assert 'price_warning' in result
    assert abs(result['current_price'] - 2800) < 0.01

def test_invalid_instructions():
    invalid_instructions = [
        "买入 AAPL",
        "XYZ 100到90之间买入",
        "ABC 现价到stop之间买入",
    ]
    for instruction in invalid_instructions:
        with pytest.raises(ValueError):
            parse_trading_instruction(instruction)

# 可以添加更多测试函数