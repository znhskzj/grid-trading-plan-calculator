# scripts/validate_trading_logic.py

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.trading_logic import TradingLogic
from tests.test_data import SAMPLE_INSTRUCTIONS, SAMPLE_BUY_PLAN_INPUTS, get_trading_logic_instance

def main():
    trading_logic = get_trading_logic_instance()
    
    # 测试 calculate_buy_plan
    for input_data in SAMPLE_BUY_PLAN_INPUTS:
        buy_plan, warning = trading_logic.calculate_buy_plan(**input_data)
        print(f"Buy Plan for {input_data}: {buy_plan}")
        print(f"Warning: {warning}")
    
    # 测试 parse_trading_instruction
    for instruction in SAMPLE_INSTRUCTIONS:
        parsed = trading_logic.parse_trading_instruction(instruction)
        print(f"Parsed Instruction: {parsed}")

if __name__ == "__main__":
    main()