# src/calculations.py

from __future__ import annotations
import logging
import numpy as np
import re
from typing import Dict, List, Tuple, Union, Optional
from src.utils import exception_handler
from src.status_manager import StatusManager

logger = logging.getLogger(__name__)

@exception_handler
def validate_inputs(funds: float, initial_price: float, stop_loss_price: float, num_grids: int, allocation_method: int):
    StatusManager.update_status("正在验证输入参数...")
    if funds <= 0:
        raise ValueError("总资金必须是正数")
    if initial_price <= 0:
        raise ValueError("初始价格必须是正数")
    if stop_loss_price <= 0:
        raise ValueError("止损价格必须是正数")
    if num_grids <= 0:
        raise ValueError("网格数量必须是正整数")
    if allocation_method not in [0, 1, 2]:
        raise ValueError("分配方式必须是0、1或2")
    if stop_loss_price >= initial_price:
        raise ValueError("止损价格必须小于初始价格")
    if funds < initial_price:
        raise ValueError("总资金必须大于初始价格")
    if num_grids > 100:
        raise ValueError("网格数量不能超过100")


def equal_amount_allocation(num_prices: int) -> List[float]:
    return [1.0] * num_prices

def exponential_allocation(prices: List[float]) -> List[float]:
    max_price = max(prices)
    min_price = min(prices)
    price_range = max_price - min_price
    if price_range == 0:
        return [1.0] * len(prices)
    return [np.exp(3 * (max_price - price) / price_range) for price in prices]

def linear_weighted_allocation(num_prices: int) -> List[float]:
    return list(range(1, num_prices + 1))

@exception_handler
def calculate_weights(prices: List[float], method: int, max_shares: int) -> List[int]:
    logger.debug(f"开始计算权重: 方法={method}, 最大股数={max_shares}")
    StatusManager.update_status("正在计算权重...")

    if len(prices) == 1:
        return [max_shares]

    allocation_methods = {
        0: lambda: equal_amount_allocation(len(prices)),
        1: lambda: exponential_allocation(prices),
        2: lambda: linear_weighted_allocation(len(prices))
    }

    weights = allocation_methods.get(method, lambda: [])()
    if not weights:
        raise ValueError("无效的分配方式")

    total_weight = sum(weights)
    initial_shares = [max(1, int(max_shares * (weight / total_weight))) for weight in weights]

    logger.debug(f"计算得到的初始股数: {initial_shares}")
    return initial_shares

@exception_handler
def calculate_buy_plan(funds: float, initial_price: float, stop_loss_price: float, num_grids: int, allocation_method:
                       int) -> Tuple[List[Tuple[float, int]],
                                     str]:
    logger.info("开始执行 calculate_buy_plan 函数")
    StatusManager.update_status("正在计算购买计划...")
    validate_inputs(funds, initial_price, stop_loss_price, num_grids, allocation_method)

    max_price = initial_price
    min_price = stop_loss_price

    max_shares = int(funds / min_price)
    logger.debug(f"最大可购买股数: {max_shares}")

    if max_shares < num_grids:
        num_grids = max_shares
        logger.warning(f"资金不足以分配到所有网格，已减少网格数量至 {num_grids}")

    buy_prices = np.linspace(max_price, min_price, num_grids)
    logger.debug(f"生成的价格网格: {buy_prices}")

    if allocation_method == 0:  # 等金额分配
        target_amount_per_grid = funds / num_grids
        buy_quantities = [max(1, int(target_amount_per_grid / price)) for price in buy_prices]
    else:
        buy_quantities = calculate_weights(buy_prices, allocation_method, max_shares)

    # 调整购买数量，确保总金额不超过可用资金
    total_cost = sum(price * quantity for price, quantity in zip(buy_prices, buy_quantities))
    if total_cost > funds:
        scale_factor = funds / total_cost
        buy_quantities = [max(1, int(quantity * scale_factor)) for quantity in buy_quantities]

    # 分配剩余资金
    remaining_funds = funds - sum(price * quantity for price, quantity in zip(buy_prices, buy_quantities))
    while remaining_funds > min(buy_prices):
        for i in range(num_grids):
            if remaining_funds >= buy_prices[i]:
                buy_quantities[i] += 1
                remaining_funds -= buy_prices[i]
                break

    buy_plan = [(round(price, 2), int(quantity)) for price, quantity in zip(buy_prices, buy_quantities)]

    # 检查是否有过多的1股购买
    single_share_count = sum(1 for _, quantity in buy_plan if quantity == 1)
    warning_message = ""
    if single_share_count > num_grids // 2:
        warning_message = "\n警告：当前参数可能不够合理，多个价位只购买1股。建议减少网格数量或增加总资金。"

    logger.info("calculate_buy_plan 函数执行完毕")
    return buy_plan, warning_message


def run_calculation(input_values: Dict[str, any]) -> str:
    """执行计算购买计划"""
    StatusManager.update_status("开始计算购买计划...")
    buy_plan, warning_message = calculate_buy_plan(**input_values)
    StatusManager.update_status("计算完成，正在生成结果报告...")
    return format_results(input_values, buy_plan, warning_message)


def calculate_with_reserve(input_values: Dict[str, any], reserve_percentage: int) -> str:
    """执行保留部分资金的计算"""
    StatusManager.update_status(f"开始计算（保留{reserve_percentage}%资金）...")
    
    # 计算保留的资金
    total_funds = input_values['funds']
    reserved_funds = total_funds * (reserve_percentage / 100)
    available_funds = total_funds - reserved_funds
    
    # 更新输入值中的可用资金
    input_values['funds'] = available_funds
    
    # 调用原有的计算函数
    buy_plan, warning_message = calculate_buy_plan(**input_values)
    
    StatusManager.update_status("计算完成，正在生成结果报告...")
    result = format_results(input_values, buy_plan, warning_message, reserved_funds)
    return result


def format_results(
        input_values: Dict, buy_plan: List[Tuple[float, int]],
        warning_message: str, reserved_funds: float = 0) -> str:
    result = f"总资金: {input_values['funds']:.2f}\n"
    if reserved_funds > 0:
        result += f"保留资金: {reserved_funds:.2f}\n"
        result += f"可用资金: {input_values['funds'] - reserved_funds:.2f}\n"
    result += f"初始价格: {input_values['initial_price']:.2f}\n"
    result += f"止损价格: {input_values['stop_loss_price']:.2f}\n"
    result += f"网格数量: {len(buy_plan)}\n"

    # 添加分配方式的详细信息
    allocation_method = input_values['allocation_method']
    if allocation_method == 0:
        actual_amounts = [price * quantity for price, quantity in buy_plan]
        avg_amount = sum(actual_amounts) / len(actual_amounts)
        result += f"选择的分配方式: 等金额分配 (每个网格平均约 {avg_amount:.0f}元)\n"
        result += "分配特点: 每个价格点分配相同金额\n"
    elif allocation_method == 1:
        result += "选择的分配方式: 等比例分配（指数分配）\n"
        result += "分配特点: 价格越低，分配资金呈指数增长\n"
        result += "效果: 在最低价位分配最多资金，资金分配差异大\n"
    else:
        result += "选择的分配方式: 线性加权分配\n"
        result += "分配特点: 价格越低，分配资金线性增加\n"
        result += f"效果: 低价位分配更多资金，但增长相对平缓（最低价格网格权重为最高价格网格的 {input_values['num_grids']} 倍）\n"

    result += "购买计划如下：\n"

    total_shares = 0
    total_cost = 0
    for price, quantity in buy_plan:
        buy_amount = price * quantity
        result += f"价格: {price:.2f}, 购买股数: {quantity}, 购买金额: 约{buy_amount:.0f}元\n"
        total_shares += quantity
        total_cost += buy_amount

    average_price = total_cost / total_shares if total_shares > 0 else 0

    result += f"\n总购买股数: {total_shares}\n"
    result += f"总投资成本: {total_cost:.2f}\n"
    result += f"平均购买价格: {average_price:.2f}\n"

    max_loss = total_cost - (input_values['stop_loss_price'] * total_shares)
    result += f"\n最大潜在亏损: {max_loss:.2f} (达到止损价时)\n"
    result += f"最大亏损比例: {(max_loss / input_values['funds']) * 100:.2f}%\n"

    if warning_message:
        result += f"\n警告: {warning_message}\n"
        StatusManager.update_status("计算完成，但有警告")  # 添加此行
    else:
        StatusManager.update_status("计算完成")  # 添加此行

    if total_shares > 100000:  # 或者其他您认为合适的阈值
        result += "\n注意：此计划包含大量股票。"

    return result


def parse_trading_instruction(instruction: str, current_api_price: Optional[float] = None) -> Dict[str, Union[str, float, Tuple[float, float], None]]:
    logger.info(f"开始解析交易指令: {instruction}")
    instruction = instruction.upper()
    
    # 匹配股票代码，考虑可能的前缀如"日内"
    symbol_match = re.search(r'(?:日内)?([A-Z]+)', instruction)
    symbol = symbol_match.group(1) if symbol_match else None
    logger.info(f"解析到的股票代码: {symbol}")
    
    # 匹配价格区间或单一价格
    price_range = re.search(r'(?:区间|现价到?|)(\d+(\.\d+)?)(?:-|到|之间|附近)?\s*(?:(\d+(\.\d+)?))?', instruction)
    if price_range:
        lower_price = float(price_range.group(1))
        higher_price = float(price_range.group(3)) if price_range.group(3) else lower_price
        current_price = higher_price
        logger.info(f"解析到的价格区间: {lower_price}-{higher_price}")
        if lower_price > higher_price:
            raise ValueError("价格区间无效：起始价格大于结束价格")
    else:
        current_price = None
        lower_price = None
        higher_price = None
        logger.warning("未能解析到价格区间")
    
    # 查找止损价格
    stop_loss_match = re.search(r'止损(\d+(\.\d+)?)', instruction)
    if stop_loss_match:
        stop_loss = float(stop_loss_match.group(1))
        if stop_loss >= current_price:
            stop_loss = current_price * 0.95  # 设置为当前价格的95%
            logger.warning(f"止损价格高于或等于当前价格，已自动调整为 {stop_loss:.2f}")
    else:
        stop_loss = lower_price if lower_price else (current_price * 0.95 if current_price else None)
    
    logger.info(f"使用的止损价格: {stop_loss}")
    
    # 查找压力价格
    resistance = re.search(r'压力(\d+(\.\d+)?)', instruction)
    if resistance:
        resistance = float(resistance.group(1))
        logger.info(f"解析到的压力价格: {resistance}")
    
    # 验证必要信息是否存在
    if not symbol or current_price is None:
        raise ValueError("无效的指令格式：缺少股票代码或价格信息")
    
    result: Dict[str, Union[str, float, Tuple[float, float], None]] = {
        "symbol": symbol,
        "current_price": current_price,
        "stop_loss": stop_loss,
        "price_range": (lower_price, higher_price) if lower_price is not None else None,
        "resistance": resistance if resistance else None
    }
    logger.info(f"解析结果: {result}")

    price_tolerance = 0.1  # 10%的容忍度
    if current_api_price and current_price:
        price_diff = abs(current_api_price - current_price) / current_price
        if price_diff > price_tolerance:
            result['price_warning'] = f"指令价格与当前实际价格相差超过{price_tolerance*100}%"
    logger.info("解析完成")
    return result

def calculate_grid_from_instruction(parsed_instruction: Dict[str, any], total_funds: float, num_grids: int, allocation_method: int) -> str:
    symbol = parsed_instruction["symbol"]
    current_price = parsed_instruction["current_price"]
    stop_loss = parsed_instruction["stop_loss"]
    
    if not current_price or not stop_loss:
        raise ValueError("无法从指令中提取到足够的信息")
    
    buy_plan, warning_message = calculate_buy_plan(total_funds, current_price, stop_loss, num_grids, allocation_method)
    
    result = f"标的: {symbol}\n" + format_results({
        'funds': total_funds,
        'initial_price': current_price,
        'stop_loss_price': stop_loss,
        'num_grids': num_grids,
        'allocation_method': allocation_method
    }, buy_plan, warning_message)
    
    return result

if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "../tests/test_instruction_parsing.py"])