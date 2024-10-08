# src/api/moomoo_adapter.py

import logging
import os
import configparser
import threading
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from moomoo import (
    OpenSecTradeContext, TrdSide, OrderType, TrdEnv, TrdMarket, SecurityFirm,
    RET_OK, Currency, OrderStatus
)

from src.utils.logger import setup_logger
from src.utils.error_handler import TradingError
from .trading_interface import TradingInterface

logger = logging.getLogger(__name__)

class MoomooAdapter:
    def __init__(self, config=None):
        self.config = config or self.load_moomoo_config()
        self.HOST = self.config.get('host', '127.0.0.1')
        self.PORT = int(self.config.get('port', '11111'))
        self.SECURITY_FIRM = getattr(SecurityFirm, self.config.get('security_firm', 'FUTUINC'))
        self.stop_event = threading.Event()

    @staticmethod
    def load_moomoo_config() -> Dict[str, str]:
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'userconfig.ini')
        if not os.path.exists(config_path):
            logger.warning("userconfig.ini not found. Using default values.")
            return {
                'host': '127.0.0.1',
                'port': '11111',
                'security_firm': 'FUTUINC'
            }
        config.read(config_path)
        if 'MoomooAPI' not in config:
            logger.warning("MoomooAPI section not found in userconfig.ini. Using default values.")
            return {
                'host': '127.0.0.1',
                'port': '11111',
                'security_firm': 'FUTUINC'
            }
        return dict(config['MoomooAPI'])

    def test_moomoo_connection(self, trade_env: TrdEnv, market: TrdMarket, timeout: float = 10.0) -> bool:
        result = [False]
        exception = [None]

        def connection_attempt():
            try:
                with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                    ret, data = trd_ctx.get_acc_list()
                    if ret == RET_OK:
                        logger.info(f"Moomoo API connection successful for {market} in {trade_env} mode")
                        result[0] = True
                    else:
                        logger.error(f"Moomoo API connection failed for {market} in {trade_env} mode: {data}")
            except Exception as e:
                logger.exception(f"Error testing Moomoo connection for {market} in {trade_env} mode: {str(e)}")
                exception[0] = e

        thread = threading.Thread(target=connection_attempt)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            logger.error(f"Moomoo API connection timed out after {timeout} seconds")
            self.stop_event.set()
            thread.join(1)
            return False

        if exception[0]:
            raise exception[0]

        return result[0]

    def stop_all_connections(self):
        self.stop_event.set()

    def get_acc_list(self, trade_env: TrdEnv, market: TrdMarket) -> Optional[pd.DataFrame]:
        logger.info(f"Getting account list for trade_env: {trade_env}, market: {market}")
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.get_acc_list()
            if ret == RET_OK:
                filtered_data = data[data['trd_env'] == trade_env]
                logger.info(f"Filtered account list: {filtered_data.to_dict()}")
                return filtered_data
            else:
                raise TradingError(f'获取账户列表失败：{data}')
        except Exception as e:
            logger.exception(f"获取账户列表时发生错误：{str(e)}")
            raise TradingError(f"获取账户列表失败：{str(e)}")

    @staticmethod
    def select_account(acc_list: pd.DataFrame) -> Optional[int]:
        print("\n可用账户:")
        for i, (_, acc) in enumerate(acc_list.iterrows()):
            print(f"{i+1}. 账户ID: {acc['acc_id']}, 类型: {acc['acc_type']}, 环境: {acc['trd_env']}")
        while True:
            try:
                choice = int(input("\n请选择要查询的账户 (输入序号): ")) - 1
                if 0 <= choice < len(acc_list):
                    return acc_list.iloc[choice]['acc_id']
                else:
                    print("无效的选择，请重试。")
            except ValueError:
                print("请输入有效的数字。")
            except Exception as e:
                logger.exception(f"选择账户时发生错误：{str(e)}")
                return None

    def get_account_info(self, **kwargs) -> Dict[str, Any]:
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        currency = kwargs.get('currency', Currency.USD)
        
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.accinfo_query(acc_id=acc_id, trd_env=trade_env, currency=currency)
            if ret == RET_OK:
                return data.to_dict('records')[0]
            else:
                raise TradingError(f'获取账户 {acc_id} 信息失败：{data}')
        except Exception as e:
            logger.exception(f"获取账户信息时发生错误：{str(e)}")
            raise TradingError(f"获取账户信息失败：{str(e)}")

    def get_history_orders(self, **kwargs) -> Dict[str, Any]:
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        include_cancelled = kwargs.get('include_cancelled', False)
        days = kwargs.get('days', 30)

        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                status_filter_list = [] if include_cancelled else [
                    OrderStatus.SUBMITTED,
                    OrderStatus.FILLED_PART,
                    OrderStatus.FILLED_ALL,
                    OrderStatus.CANCELLED_PART,
                    OrderStatus.CANCELLED_ALL
                ]
                
                ret, data = trd_ctx.history_order_list_query(
                    status_filter_list=status_filter_list,
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    trd_env=trade_env,
                    acc_id=acc_id
                )
                
                if ret == RET_OK:
                    logger.info(f"Successfully retrieved {len(data)} historical orders from {start_date.date()} to {end_date.date()}")
                    return data.to_dict('records')
                else:
                    raise TradingError(f'查询账户 {acc_id} 历史订单失败：{data}')
        except Exception as e:
            logger.exception(f"获取历史订单信息时发生错误：{str(e)}")
            raise TradingError(f"获取历史订单失败：{str(e)}")

    def get_positions(self, **kwargs) -> Dict[str, Any]:
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')

        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.position_list_query(acc_id=acc_id, trd_env=trade_env)
            if ret == RET_OK:
                logger.info(f"Successfully retrieved {len(data)} positions")
                return data.to_dict('records')
            else:
                raise TradingError(f'查询账户 {acc_id} 持仓失败：{data}')
        except Exception as e:
            logger.exception(f"获取持仓信息时发生错误：{str(e)}")
            raise TradingError(f"获取持仓信息失败：{str(e)}")

    def place_order(self, **kwargs) -> Any:
        acc_id = kwargs.get('acc_id')
        trade_env = kwargs.get('trade_env')
        market = kwargs.get('market')
        code = kwargs.get('code')
        price = kwargs.get('price')
        qty = kwargs.get('qty')
        trd_side = kwargs.get('trd_side')

        try:
            # 根据市场添加前缀
            if market == TrdMarket.US:
                code = f"US.{code}"
            elif market == TrdMarket.HK:
                code = f"HK.{code}"
            
            with OpenSecTradeContext(filter_trdmarket=market, host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM) as trd_ctx:
                ret, data = trd_ctx.place_order(
                    price=price, 
                    qty=qty, 
                    code=code, 
                    trd_side=trd_side,
                    order_type=OrderType.NORMAL, 
                    trd_env=trade_env,
                    acc_id=acc_id
                )
                if ret == RET_OK:
                    logger.info(f"下单成功：{data}")
                    return data
                else:
                    raise TradingError(f"下单失败：{data}")
        except Exception as e:
            logger.exception(f"下单时发生异常：{str(e)}")
            raise TradingError(f"下单失败：{str(e)}")

    def unlock_trade(self, acc_id: int, trade_env: TrdEnv, market: TrdMarket, password: str) -> bool:
        try:
            with OpenSecTradeContext(host=self.HOST, port=self.PORT, security_firm=self.SECURITY_FIRM, filter_trdmarket=market) as trd_ctx:
                ret, data = trd_ctx.unlock_trade(password, acc_id=acc_id, trd_env=trade_env)
            if ret == RET_OK:
                logger.info("Successfully unlocked trade")
                return True
            else:
                raise TradingError(f'解锁交易失败：{data}')
        except Exception as e:
            logger.exception(f"解锁交易时发生错误：{str(e)}")
            raise TradingError(f"解锁交易失败：{str(e)}")
        
    def close(self):
        """关闭 Moomoo API 连接"""
        # 实现关闭连接的逻辑
        pass