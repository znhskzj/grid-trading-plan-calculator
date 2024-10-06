# -*- coding: utf-8 -*-
# tests/test_data.py
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.trading_logic import TradingLogic

SAMPLE_INSTRUCTIONS = [
    "AAPL 150-155 止损145 压力160",
    "GOOGL 2500 止损2400",
    "日内SOXL 现价到30之间分批入，压力31.5，止损29.5",
    "AAPL 现价150区间买入",
    "TSLA 230-240之间建仓",
    "GOOGL 2800附近买入",
    "日内SOXL 现价到30之间分批入，压力31.5，止损29.5",
    "AAPL 现价150区间买入，止损145",
    "TSLA 230-240之间建仓，止损220"
    # 更多样例...
]

SAMPLE_BUY_PLAN_INPUTS = [
    {"funds": 10000, "initial_price": 100, "stop_loss_price": 90, "num_grids": 5, "allocation_method": 1},
    # 更多样例...
]

def get_trading_logic_instance():
    # 返回一个配置好的 TradingLogic 实例
    return TradingLogic()

if __name__ == "__main__":
    print("Sample Instructions:")
    for instruction in SAMPLE_INSTRUCTIONS:
        print(instruction)
    print("\nSample Buy Plan Inputs:")
    for input_data in SAMPLE_BUY_PLAN_INPUTS:
        print(input_data)
    print("\nTesting TradingLogic instance:")
    trading_logic = get_trading_logic_instance()
    print(f"TradingLogic instance created: {trading_logic}")