# src/core/trading_logic.py

import numpy as np
import re
from typing import List, Tuple, Dict, Union, Any, Optional
from src.utils.logger import setup_logger
from src.utils.error_handler import TradingLogicError
from src.config.config_manager import ConfigManager

logger = setup_logger('trading_logic', 'logs/trading_logic.log')

class TradingLogic:
    def __init__(self):
        self.config_manager: ConfigManager = ConfigManager()
        self.trading_config: Dict[str, Any] = self.config_manager.get_trading_config()

    def validate_inputs(self, funds: float, initial_price: float, stop_loss_price: float, num_grids: int, allocation_method: int) -> None:
        """验证输入参数的有效性"""
        if funds <= 0:
            raise TradingLogicError("总资金必须是正数")
        if initial_price <= 0:
            raise TradingLogicError("初始价格必须是正数")
        if stop_loss_price <= 0:
            raise TradingLogicError("止损价格必须是正数")
        if num_grids <= 0:
            raise TradingLogicError("网格数量必须是正整数")
        if allocation_method not in [0, 1, 2]:
            raise TradingLogicError("分配方式必须是0、1或2")
        if stop_loss_price >= initial_price:
            raise TradingLogicError("止损价格必须小于初始价格")
        if funds < initial_price:
            raise TradingLogicError("总资金必须大于初始价格")
        if num_grids > 100:
            raise TradingLogicError("网格数量不能超过100")

    def calculate_buy_plan(self, funds: float, initial_price: float, stop_loss_price: float, num_grids: int, allocation_method: int) -> Tuple[List[Tuple[float, int]], str]:
        """计算购买计划"""
        logger.info("开始执行 calculate_buy_plan 函数")
        
        # 使用 trading_config 中的默认值
        funds = funds or float(self.trading_config.get('default_funds', 50000.0))
        initial_price = initial_price or float(self.trading_config.get('default_initial_price', 50.0))
        stop_loss_price = stop_loss_price or float(self.trading_config.get('default_stop_loss_price', 30.0))
        num_grids = num_grids or int(self.trading_config.get('default_num_grids', 10))
        allocation_method = allocation_method or int(self.trading_config.get('default_allocation_method', 1))

        try:
            self.validate_inputs(funds, initial_price, stop_loss_price, num_grids, allocation_method)
        except TradingLogicError as e:
            logger.error(f"输入验证失败: {str(e)}")
            return [], str(e)

        max_price: float = initial_price
        min_price: float = stop_loss_price

        max_shares: int = int(funds / min_price)
        logger.debug(f"最大可购买股数: {max_shares}")

        if max_shares < num_grids:
            num_grids = max_shares
            logger.warning(f"资金不足以分配到所有网格，已减少网格数量至 {num_grids}")

        buy_prices: np.ndarray = np.linspace(max_price, min_price, num_grids)
        logger.debug(f"生成的价格网格: {buy_prices}")

        if allocation_method == 0:  # 等金额分配
            target_amount_per_grid: float = funds / num_grids
            buy_quantities: List[int] = [max(1, int(target_amount_per_grid / price)) for price in buy_prices]
        else:
            buy_quantities: List[int] = self.calculate_weights(buy_prices.tolist(), allocation_method, max_shares)

        total_cost: float = sum(price * quantity for price, quantity in zip(buy_prices, buy_quantities))
        if total_cost > funds:
            scale_factor: float = funds / total_cost
            buy_quantities = [max(1, int(quantity * scale_factor)) for quantity in buy_quantities]

        remaining_funds: float = funds - sum(price * quantity for price, quantity in zip(buy_prices, buy_quantities))
        while remaining_funds > min(buy_prices):
            for i in range(num_grids):
                if remaining_funds >= buy_prices[i]:
                    buy_quantities[i] += 1
                    remaining_funds -= buy_prices[i]
                    break

        buy_plan: List[Tuple[float, int]] = [(round(price, 2), int(quantity)) for price, quantity in zip(buy_prices, buy_quantities)]

        single_share_count: int = sum(1 for _, quantity in buy_plan if quantity == 1)
        warning_message: str = ""
        if single_share_count > num_grids // 2:
            warning_message = "\n警告：当前参数可能不够合理，多个价位只购买1股。建议减少网格数量或增加总资金。"

        logger.info("calculate_buy_plan 函数执行完毕")
        return buy_plan, warning_message
        
    def save_recent_calculation(self, funds: float, initial_price: float, stop_loss_price: float, num_grids: int) -> None:
        recent_calc: Dict[str, str] = {
            'funds': str(funds),
            'initial_price': str(initial_price),
            'stop_loss_price': str(stop_loss_price),
            'num_grids': str(num_grids)
        }
        self.config_manager.set_config('RecentCalculations', recent_calc)

    def calculate_weights(self, prices: List[float], method: int, max_shares: int) -> List[int]:
        """计算不同分配方式的权重"""
        logger.debug(f"开始计算权重: 方法={method}, 最大股数={max_shares}")

        if len(prices) == 1:
            return [max_shares]

        allocation_methods: Dict[int, callable] = {
            0: lambda: self.equal_amount_allocation(len(prices)),
            1: lambda: self.exponential_allocation(prices),
            2: lambda: self.linear_weighted_allocation(len(prices))
        }

        weights: List[float] = allocation_methods.get(method, lambda: [])()
        if not weights:
            raise TradingLogicError("无效的分配方式")

        total_weight: float = sum(weights)
        initial_shares: List[int] = [max(1, int(max_shares * (weight / total_weight))) for weight in weights]

        logger.debug(f"计算得到的初始股数: {initial_shares}")
        return initial_shares

    def equal_amount_allocation(self, num_prices: int) -> List[float]:
        """等金额分配方法"""
        return [1.0] * num_prices

    def exponential_allocation(self, prices: List[float]) -> List[float]:
        """指数分配方法"""
        max_price: float = max(prices)
        min_price: float = min(prices)
        price_range: float = max_price - min_price
        if price_range == 0:
            return [1.0] * len(prices)
        return [np.exp(3 * (max_price - price) / price_range) for price in prices]

    def linear_weighted_allocation(self, num_prices: int) -> List[float]:
        """线性加权分配方法"""
        return list(range(1, num_prices + 1))

    def calculate_with_reserve(self, input_values: Dict[str, Any], reserve_percentage: int) -> Tuple[List[Tuple[float, int]], str, float]:
        """执行保留部分资金的计算"""
        logger.info(f"开始计算（保留{reserve_percentage}%资金）...")
        
        total_funds: float = input_values['funds']
        reserved_funds: float = total_funds * (reserve_percentage / 100)
        available_funds: float = total_funds - reserved_funds
        
        input_values['funds'] = available_funds
        
        buy_plan, warning_message = self.calculate_buy_plan(**input_values)
        
        return buy_plan, warning_message, reserved_funds

    def parse_trading_instruction(self, instruction: str, current_api_price: Optional[float] = None) -> Dict[str, Union[str, float, Tuple[float, float], None]]:
        """
        解析交易指令
        
        :param instruction: 交易指令字符串
        :param current_api_price: 当前 API 提供的价格（可选）
        :return: 解析后的指令字典
        """
        logger.info(f"开始解析交易指令: {instruction}")
        instruction = instruction.upper()
        
        symbol_match = re.search(r'(?:日内)?([A-Z]+)', instruction)
        symbol: Optional[str] = symbol_match.group(1) if symbol_match else None
        logger.info(f"解析到的股票代码: {symbol}")
        
        price_range = re.search(r'(?:区间|现价到?|)(\d+(\.\d+)?)(?:-|到|之间|附近)?\s*(?:(\d+(\.\d+)?))?', instruction)
        if price_range:
            lower_price: float = float(price_range.group(1))
            higher_price: float = float(price_range.group(3)) if price_range.group(3) else lower_price
            current_price: float = higher_price
            logger.info(f"解析到的价格区间: {lower_price}-{higher_price}")
            if lower_price > higher_price:
                raise TradingLogicError("价格区间无效：起始价格大于结束价格")
        else:
            current_price = None
            lower_price = None
            higher_price = None
            logger.warning("未能解析到价格区间")
        
        stop_loss_match = re.search(r'止损(\d+(\.\d+)?)', instruction)
        if stop_loss_match:
            stop_loss: float = float(stop_loss_match.group(1))
            if stop_loss >= current_price:
                stop_loss = current_price * 0.95  # 设置为当前价格的95%
                logger.warning(f"止损价格高于或等于当前价格，已自动调整为 {stop_loss:.2f}")
        else:
            stop_loss = lower_price if lower_price else (current_price * 0.95 if current_price else None)
        
        logger.info(f"使用的止损价格: {stop_loss}")
        
        resistance_match = re.search(r'压力(\d+(\.\d+)?)', instruction)
        resistance: Optional[float] = float(resistance_match.group(1)) if resistance_match else None
        if resistance:
            logger.info(f"解析到的压力价格: {resistance}")
        
        if not symbol or current_price is None:
            raise TradingLogicError("无效的指令格式：缺少股票代码或价格信息")
        
        result: Dict[str, Union[str, float, Tuple[float, float], None]] = {
            "symbol": symbol,
            "current_price": current_price,
            "stop_loss": stop_loss,
            "price_range": (lower_price, higher_price) if lower_price is not None else None,
            "resistance": resistance
        }
        logger.info(f"解析结果: {result}")

        price_tolerance: float = 0.1  # 10%的容忍度
        if current_api_price and current_price:
            price_diff: float = abs(current_api_price - current_price) / current_price
            if price_diff > price_tolerance:
                result['price_warning'] = f"指令价格与当前实际价格相差超过{price_tolerance*100}%"
        
        logger.info("解析完成")
        return result

    def process_instruction(self, instruction: str, current_api_price: Optional[float] = None) -> Dict[str, Any]:
        """
        处理交易指令
        
        :param instruction: 交易指令字符串
        :param current_api_price: 当前 API 提供的价格（可选）
        :return: 处理后的指令字典
        """
        logger.info(f"开始处理交易指令: {instruction}")
        try:
            parsed_instruction = self.parse_trading_instruction(instruction, current_api_price)
            logger.debug(f"解析后的指令: {parsed_instruction}")
            if self._validate_instruction(parsed_instruction):
                logger.info("指令验证通过")
                return parsed_instruction
            else:
                logger.warning("指令验证失败")
                raise TradingLogicError("指令中缺少必要的信息")
        except Exception as e:
            logger.error(f"处理指令时发生错误: {str(e)}", exc_info=True)
            raise TradingLogicError(f"处理指令失败: {str(e)}")

    def _validate_instruction(self, parsed_instruction: Dict[str, Any]) -> bool:
        """
        验证解析后的指令是否包含所有必要信息
        
        :param parsed_instruction: 解析后的指令字典
        :return: 是否有效
        """
        logger.debug(f"验证解析后的指令: {parsed_instruction}")
        required_fields: List[str] = ['symbol', 'current_price', 'stop_loss']
        is_valid: bool = all(parsed_instruction.get(field) is not None for field in required_fields)
        logger.info(f"指令验证结果: {'通过' if is_valid else '失败'}")
        return is_valid