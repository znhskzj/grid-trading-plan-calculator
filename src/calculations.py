import logging
import numpy as np
from typing import Dict, List, Tuple
from .utils import exception_handler
# from .gui import App
from .status_manager import StatusManager

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


@exception_handler
def calculate_weights(prices: List[float], method: int, max_shares: int) -> List[int]:
    logger.debug(f"开始计算权重: 方法={method}, 最大股数={max_shares}")
    StatusManager.update_status("正在计算权重...")

    if len(prices) == 1:
        return [max_shares]

    if method == 0:  # 等金额分配
        weights = [1] * len(prices)
    elif method == 1:  # 等比例分配 - 指数增长策略
        max_price = max(prices)
        min_price = min(prices)
        price_range = max_price - min_price
        if price_range == 0:
            weights = [1] * len(prices)
        else:
            weights = [np.exp(3 * (max_price - price) / price_range) for price in prices]
    elif method == 2:  # 线性加权 - 低价格更高权重
        weights = list(range(1, len(prices) + 1))
    else:
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


def run_calculation(input_values: Dict) -> str:
    StatusManager.update_status("开始计算购买计划...")
    buy_plan, warning_message = calculate_buy_plan(**input_values)
    StatusManager.update_status("计算完成，正在生成结果报告...")
    return format_results(input_values, buy_plan, warning_message)


@exception_handler
def calculate_with_reserve(input_values: Dict, reserve_percentage: float) -> str:
    StatusManager.update_status(f"开始计算（保留{reserve_percentage}%资金）...")
    funds = input_values['funds']
    reserved_funds = funds * (reserve_percentage / 100)
    available_funds = funds - reserved_funds
    input_values['funds'] = available_funds
    buy_plan, warning_message = calculate_buy_plan(**input_values)
    StatusManager.update_status("计算完成，正在生成结果报告...")
    return format_results(input_values, buy_plan, warning_message, reserved_funds)


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

    return result
